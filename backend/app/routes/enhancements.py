"""
Enhancement Request API Routes

GET  /api/enhancement/patient/{abha_id}        — search patient + full case history
GET  /api/enhancement/pre-auth/{pre_auth_id}   — get all enhancements for a pre-auth
POST /api/enhancement/pre-auth/{pre_auth_id}   — raise new enhancement request
GET  /api/enhancement/{id}                     — get single enhancement
PUT  /api/enhancement/{id}                     — update enhancement
GET  /api/enhancement                          — list all enhancements
"""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from app.models.enhancement import EnhancementRequest, EnhancementResponse, PatientCaseHistory
from app.services.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_response(row: dict) -> EnhancementResponse:
    allowed = EnhancementResponse.model_fields.keys()
    return EnhancementResponse(**{k: v for k, v in row.items() if k in allowed})


def _enhancements_for(sb, pre_auth_id: str) -> list[EnhancementResponse]:
    res = (
        sb.table("enhancement_requests")
        .select("*")
        .eq("pre_auth_id", pre_auth_id)
        .order("sequence_no")
        .execute()
    )
    return [_to_response(r) for r in (res.data or [])]


# ---------------------------------------------------------------------------
# Search patient case history by ABHA ID
# ---------------------------------------------------------------------------

@router.get("/enhancement/patient/{abha_id}", response_model=list[PatientCaseHistory])
async def get_patient_case_history(abha_id: str):
    """
    Return all pre-auth requests for a patient (by ABHA ID),
    each enriched with its enhancement history.
    """
    sb = get_supabase()

    # Verify ABHA exists
    abha_res = sb.table("abha_registry").select("abha_id, name").eq("abha_id", abha_id.strip()).execute()
    if not abha_res.data:
        raise HTTPException(
            status_code=404,
            detail=f"No patient found with ABHA ID '{abha_id}'.",
        )

    # Fetch all pre-auth requests for this ABHA ID
    pa_res = (
        sb.table("pre_auth_requests")
        .select(
            "id, abha_id, patient_name, provisional_diagnosis, icd10_diagnosis_code, "
            "admission_date, admission_type, hospital_name, total_estimated_cost, "
            "status, created_at"
        )
        .eq("abha_id", abha_id.strip())
        .order("created_at", desc=True)
        .execute()
    )

    history = []
    for pa in (pa_res.data or []):
        enhancements = _enhancements_for(sb, pa["id"])
        history.append(PatientCaseHistory(
            pre_auth_id=pa["id"],
            patient_name=pa.get("patient_name"),
            abha_id=pa.get("abha_id"),
            provisional_diagnosis=pa.get("provisional_diagnosis"),
            icd10_diagnosis_code=pa.get("icd10_diagnosis_code"),
            admission_date=pa.get("admission_date"),
            admission_type=pa.get("admission_type"),
            hospital_name=pa.get("hospital_name"),
            total_estimated_cost=pa.get("total_estimated_cost"),
            status=pa.get("status", "draft"),
            created_at=pa.get("created_at"),
            enhancements=enhancements,
        ))

    return history


# ---------------------------------------------------------------------------
# Enhancements for a specific pre-auth
# ---------------------------------------------------------------------------

@router.get("/enhancement/pre-auth/{pre_auth_id}", response_model=list[EnhancementResponse])
async def list_enhancements_for_pre_auth(pre_auth_id: str):
    sb = get_supabase()
    return _enhancements_for(sb, pre_auth_id)


@router.post("/enhancement/pre-auth/{pre_auth_id}", response_model=EnhancementResponse)
async def create_enhancement(pre_auth_id: str, data: EnhancementRequest):
    """Raise a new enhancement request for an existing pre-auth."""
    sb = get_supabase()

    # Verify pre-auth exists and grab original diagnosis snapshot
    pa_res = (
        sb.table("pre_auth_requests")
        .select("id, abha_id, provisional_diagnosis, icd10_diagnosis_code, total_estimated_cost")
        .eq("id", pre_auth_id)
        .execute()
    )
    if not pa_res.data:
        raise HTTPException(status_code=404, detail=f"Pre-auth '{pre_auth_id}' not found")

    pa = pa_res.data[0]

    # Determine next sequence number
    seq_res = (
        sb.table("enhancement_requests")
        .select("sequence_no")
        .eq("pre_auth_id", pre_auth_id)
        .order("sequence_no", desc=True)
        .limit(1)
        .execute()
    )
    next_seq = (seq_res.data[0]["sequence_no"] + 1) if seq_res.data else 1

    row = {k: v for k, v in data.model_dump().items() if v is not None}
    row["pre_auth_id"] = pre_auth_id
    row["abha_id"] = pa.get("abha_id")
    row["sequence_no"] = next_seq
    row["status"] = "submitted"
    row["original_diagnosis"] = pa.get("provisional_diagnosis")
    row["original_icd10_code"] = pa.get("icd10_diagnosis_code")
    row["original_total_cost"] = pa.get("total_estimated_cost")

    res = sb.table("enhancement_requests").insert(row).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create enhancement request")

    return _to_response(res.data[0])


# ---------------------------------------------------------------------------
# Single enhancement CRUD
# ---------------------------------------------------------------------------

@router.get("/enhancement/{enhancement_id}", response_model=EnhancementResponse)
async def get_enhancement(enhancement_id: str):
    sb = get_supabase()
    res = sb.table("enhancement_requests").select("*").eq("id", enhancement_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail=f"Enhancement '{enhancement_id}' not found")
    return _to_response(res.data[0])


@router.put("/enhancement/{enhancement_id}", response_model=EnhancementResponse)
async def update_enhancement(enhancement_id: str, data: EnhancementRequest):
    sb = get_supabase()

    check = sb.table("enhancement_requests").select("id").eq("id", enhancement_id).execute()
    if not check.data:
        raise HTTPException(status_code=404, detail=f"Enhancement '{enhancement_id}' not found")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    res = sb.table("enhancement_requests").update(updates).eq("id", enhancement_id).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Update failed")
    return _to_response(res.data[0])


@router.get("/enhancement", response_model=list[EnhancementResponse])
async def list_all_enhancements():
    sb = get_supabase()
    res = (
        sb.table("enhancement_requests")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return [_to_response(r) for r in (res.data or [])]
