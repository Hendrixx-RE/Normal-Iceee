"""
Pre-Authorization API Routes
GET  /api/abha/{abha_id}                    — lookup patient from ABHA registry
POST /api/pre-auth                          — create a new pre-auth request
GET  /api/pre-auth                          — list all pre-auth requests
GET  /api/pre-auth/{id}                     — get a single pre-auth request
PUT  /api/pre-auth/{id}                     — update / save pre-auth request
POST /api/pre-auth/{id}/extract-medical     — upload PDF → Gemini fills medical fields
POST /api/pre-auth/{id}/generate-pdf        — generate downloadable PDF
"""
import gc
import logging
import random
import string
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response


def _generate_bill_no() -> str:
    from datetime import datetime
    return f"BILL-{datetime.now().strftime('%Y%m%d')}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"

from app.models.pre_auth import (
    AbhaPatient, PreAuthRequest, PreAuthResponse,
    MedicalExtract, get_missing_required,
)
from app.services.supabase_client import get_supabase
from app.services.ocr import extract_pdf_text, render_gemini_thumbnails
from app.services.pre_auth_extractor import extract_medical_for_preauth
from app.services.pdf_generator import generate_pre_auth_pdf
from app.services.ocr_strategies.quality_checker import TextQualityChecker
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

OCR_QUALITY_GOOD   = 75.0
OCR_QUALITY_USABLE = 40.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_response(row: dict) -> PreAuthResponse:
    missing = get_missing_required(PreAuthRequest(**{
        k: v for k, v in row.items()
        if k in PreAuthRequest.model_fields
    }))
    return PreAuthResponse(
        **{k: v for k, v in row.items() if k in PreAuthResponse.model_fields},
        missing_required_fields=missing,
    )


# ---------------------------------------------------------------------------
# ABHA Lookup
# ---------------------------------------------------------------------------

@router.get("/abha/{abha_id}", response_model=AbhaPatient)
async def lookup_abha(abha_id: str):
    """Fetch patient demographics and insurance details from the ABHA registry."""
    sb = get_supabase()
    res = sb.table("abha_registry").select("*").eq("abha_id", abha_id.strip()).execute()
    if not res.data:
        raise HTTPException(
            status_code=404,
            detail=f"No patient found with ABHA ID '{abha_id}'. Please fill the details manually.",
        )
    return AbhaPatient(**res.data[0])


# ---------------------------------------------------------------------------
# Pre-Auth CRUD
# ---------------------------------------------------------------------------

@router.post("/pre-auth", response_model=PreAuthResponse)
async def create_pre_auth(data: PreAuthRequest):
    """Create a new pre-auth request (starts as draft)."""
    sb = get_supabase()
    row = {k: v for k, v in data.model_dump().items() if v is not None}
    row["status"] = "draft"
    row["bill_no"] = _generate_bill_no()
    res = sb.table("pre_auth_requests").insert(row).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create pre-auth request")
    return _row_to_response(res.data[0])


@router.get("/pre-auth", response_model=list[PreAuthResponse])
async def list_pre_auths():
    """List all pre-auth requests, newest first."""
    sb = get_supabase()
    res = sb.table("pre_auth_requests").select("*").order("created_at", desc=True).execute()
    return [_row_to_response(r) for r in (res.data or [])]


@router.get("/pre-auth/{pre_auth_id}", response_model=PreAuthResponse)
async def get_pre_auth(pre_auth_id: str):
    """Get a single pre-auth request by ID."""
    sb = get_supabase()
    res = sb.table("pre_auth_requests").select("*").eq("id", pre_auth_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail=f"Pre-auth '{pre_auth_id}' not found")
    return _row_to_response(res.data[0])


@router.put("/pre-auth/{pre_auth_id}", response_model=PreAuthResponse)
async def update_pre_auth(pre_auth_id: str, data: PreAuthRequest):
    """Update an existing pre-auth request with new field values."""
    from datetime import datetime, timezone
    sb = get_supabase()

    # Verify it exists
    check = sb.table("pre_auth_requests").select("id").eq("id", pre_auth_id).execute()
    if not check.data:
        raise HTTPException(status_code=404, detail=f"Pre-auth '{pre_auth_id}' not found")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    res = sb.table("pre_auth_requests").update(updates).eq("id", pre_auth_id).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Update failed")
    return _row_to_response(res.data[0])


# ---------------------------------------------------------------------------
# Medical Extraction from uploaded PDF
# ---------------------------------------------------------------------------

@router.post("/pre-auth/{pre_auth_id}/extract-medical", response_model=MedicalExtract)
async def extract_medical(
    pre_auth_id: str,
    file: UploadFile = File(...),
):
    """
    Upload a clinical PDF. OCR + Gemini extracts medical fields and
    auto-updates the pre-auth record. Returns the extracted fields.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(pdf_bytes) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

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
        extract = await extract_medical_for_preauth(extracted_text, page_images)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Medical extraction failed: {e}")
    finally:
        if page_images:
            for img in page_images:
                img.close()
            gc.collect()

    # Persist extracted fields into the pre-auth record (only non-null values)
    from datetime import datetime, timezone
    sb = get_supabase()
    updates = {k: v for k, v in extract.model_dump().items() if v is not None}
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        sb.table("pre_auth_requests").update(updates).eq("id", pre_auth_id).execute()

    return extract


# ---------------------------------------------------------------------------
# PDF Generation
# ---------------------------------------------------------------------------

@router.post("/pre-auth/{pre_auth_id}/generate-pdf")
async def generate_pdf(pre_auth_id: str):
    """
    Generate and return a downloadable pre-auth PDF.
    Works even if some required fields are missing (they appear as red placeholders).
    """
    sb = get_supabase()
    res = sb.table("pre_auth_requests").select("*").eq("id", pre_auth_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail=f"Pre-auth '{pre_auth_id}' not found")

    row = res.data[0]
    pre_auth = PreAuthRequest(**{k: v for k, v in row.items() if k in PreAuthRequest.model_fields})

    try:
        pdf_bytes = generate_pre_auth_pdf(pre_auth, pre_auth_id=pre_auth_id)
    except Exception as e:
        logger.error(f"PDF generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    # Update status to submitted
    from datetime import datetime, timezone
    sb.table("pre_auth_requests").update({
        "status": "submitted",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", pre_auth_id).execute()

    filename = f"pre_auth_{pre_auth_id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
