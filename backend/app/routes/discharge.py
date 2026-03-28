"""
Discharge API Routes
POST /api/discharge                      — create discharge record
GET  /api/discharge/by-bill/{bill_no}    — get discharge by bill_no  (MUST be before /{id})
GET  /api/discharge/{id}                 — get discharge by id
PUT  /api/discharge/{id}                 — update discharge
POST /api/discharge/{id}/extract         — upload PDF, Gemini extracts fields, updates record
"""
import gc
import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.models.discharge import DischargeRequest, DischargeResponse, DischargeExtract
from app.services.supabase_client import get_supabase
from app.services.ocr import extract_pdf_text, render_gemini_thumbnails
from app.services.discharge_extractor import extract_discharge_data
from app.services.ocr_strategies.quality_checker import TextQualityChecker
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

OCR_QUALITY_USABLE = 40.0


# ---------------------------------------------------------------------------
# Revenue flag computation
# ---------------------------------------------------------------------------

def _compute_revenue_flags(discharge: dict, pre_auth: dict | None) -> List[dict]:
    flags: List[dict] = []

    # Missing discharge date
    if not discharge.get("discharge_date"):
        flags.append({
            "field": "discharge_date",
            "severity": "critical",
            "message": "Discharge date is missing",
        })

    # Missing procedure codes
    if not discharge.get("procedure_codes"):
        flags.append({
            "field": "procedure_codes",
            "severity": "warning",
            "message": "Procedure codes (ICD-10 PCS/CPT) not provided",
        })

    if pre_auth:
        # ICD-10 diagnosis code mismatch
        discharge_icd = (discharge.get("final_icd10_codes") or "").strip()
        preauth_icd = (pre_auth.get("icd10_diagnosis_code") or "").strip()
        if discharge_icd and preauth_icd:
            # Compare by prefix (first 3 chars of ICD-10 code)
            discharge_prefix = discharge_icd.split(",")[0].strip()[:3].upper()
            preauth_prefix = preauth_icd[:3].upper()
            if discharge_prefix and preauth_prefix and discharge_prefix != preauth_prefix:
                flags.append({
                    "field": "final_icd10_codes",
                    "severity": "warning",
                    "message": f"Diagnosis code mismatch: discharge={discharge_icd!r} vs pre-auth={preauth_icd!r}",
                })

        # Bill vs pre-auth estimate variance
        total_bill = discharge.get("total_bill_amount")
        total_estimate = pre_auth.get("total_estimated_cost")
        if total_bill is not None and total_estimate is not None and total_estimate > 0:
            pct = ((total_bill - total_estimate) / total_estimate) * 100
            if pct > 20:
                flags.append({
                    "field": "total_bill_amount",
                    "severity": "critical",
                    "message": f"Bill exceeds pre-auth by {pct:.1f}%",
                })
            elif pct > 5:
                flags.append({
                    "field": "total_bill_amount",
                    "severity": "warning",
                    "message": f"Bill exceeds pre-auth by {pct:.1f}%",
                })

    return flags


def _row_to_response(row: dict) -> DischargeResponse:
    return DischargeResponse(**{k: v for k, v in row.items() if k in DischargeResponse.model_fields})


# ---------------------------------------------------------------------------
# Routes — order matters: by-bill BEFORE /{id}
# ---------------------------------------------------------------------------

@router.get("/discharge/by-bill/{bill_no}", response_model=DischargeResponse)
async def get_discharge_by_bill(bill_no: str):
    """Get a discharge record by bill number."""
    sb = get_supabase()
    res = sb.table("discharge_requests").select("*").eq("bill_no", bill_no).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail=f"No discharge record found for bill_no='{bill_no}'")
    return _row_to_response(res.data[0])


@router.post("/discharge", response_model=DischargeResponse)
async def create_discharge(data: DischargeRequest):
    """Create a new discharge record and compute initial revenue flags."""
    sb = get_supabase()

    row = {k: v for k, v in data.model_dump().items() if v is not None}
    row["status"] = row.get("status", "pending")
    row["revenue_flags"] = []

    # Fetch pre-auth for flag computation
    pre_auth = None
    if data.pre_auth_id:
        pa_res = sb.table("pre_auth_requests").select("*").eq("id", data.pre_auth_id).execute()
        if pa_res.data:
            pre_auth = pa_res.data[0]

    flags = _compute_revenue_flags(row, pre_auth)
    row["revenue_flags"] = flags

    res = sb.table("discharge_requests").insert(row).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create discharge record")
    return _row_to_response(res.data[0])


@router.get("/discharge/{discharge_id}", response_model=DischargeResponse)
async def get_discharge(discharge_id: str):
    """Get a discharge record by ID."""
    sb = get_supabase()
    res = sb.table("discharge_requests").select("*").eq("id", discharge_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail=f"Discharge '{discharge_id}' not found")
    return _row_to_response(res.data[0])


@router.put("/discharge/{discharge_id}", response_model=DischargeResponse)
async def update_discharge(discharge_id: str, data: DischargeRequest):
    """Update a discharge record and recompute revenue flags."""
    sb = get_supabase()

    check = sb.table("discharge_requests").select("id, pre_auth_id").eq("id", discharge_id).execute()
    if not check.data:
        raise HTTPException(status_code=404, detail=f"Discharge '{discharge_id}' not found")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Use pre_auth_id from update payload or existing record
    pre_auth_id = data.pre_auth_id or check.data[0].get("pre_auth_id")
    pre_auth = None
    if pre_auth_id:
        pa_res = sb.table("pre_auth_requests").select("*").eq("id", pre_auth_id).execute()
        if pa_res.data:
            pre_auth = pa_res.data[0]

    flags = _compute_revenue_flags(updates, pre_auth)
    updates["revenue_flags"] = flags

    res = sb.table("discharge_requests").update(updates).eq("id", discharge_id).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Update failed")
    return _row_to_response(res.data[0])


@router.post("/discharge/{discharge_id}/extract", response_model=DischargeExtract)
async def extract_discharge(
    discharge_id: str,
    file: UploadFile = File(...),
):
    """
    Upload a discharge summary / final bill PDF. OCR + Gemini extracts
    billing and clinical fields, updates the discharge record, recomputes flags.
    Returns the extracted fields.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(pdf_bytes) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    sb = get_supabase()
    check = sb.table("discharge_requests").select("*").eq("id", discharge_id).execute()
    if not check.data:
        raise HTTPException(status_code=404, detail=f"Discharge '{discharge_id}' not found")

    existing = check.data[0]

    # OCR
    try:
        extracted_text, pdf_ref = await extract_pdf_text(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"OCR failed: {e}")

    quality = TextQualityChecker.get_quality_score(extracted_text) if extracted_text else 0.0
    page_images = None
    if quality < OCR_QUALITY_USABLE:
        page_images = render_gemini_thumbnails(pdf_ref)

    del pdf_ref
    gc.collect()

    # Gemini extraction
    try:
        extract = await extract_discharge_data(extracted_text, page_images)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Discharge extraction failed: {e}")
    finally:
        if page_images:
            for img in page_images:
                img.close()
            gc.collect()

    # Merge extracted fields into existing record
    merged = dict(existing)
    updates: dict = {k: v for k, v in extract.model_dump().items() if v is not None}
    merged.update(updates)
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Recompute flags
    pre_auth = None
    pre_auth_id = existing.get("pre_auth_id")
    if pre_auth_id:
        pa_res = sb.table("pre_auth_requests").select("*").eq("id", pre_auth_id).execute()
        if pa_res.data:
            pre_auth = pa_res.data[0]

    flags = _compute_revenue_flags(merged, pre_auth)
    updates["revenue_flags"] = flags

    sb.table("discharge_requests").update(updates).eq("id", discharge_id).execute()

    return extract
