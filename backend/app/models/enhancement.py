from pydantic import BaseModel
from typing import Optional, List


class EnhancementRequest(BaseModel):
    pre_auth_id: str
    abha_id: Optional[str] = None
    sequence_no: Optional[int] = None

    # Reason
    reason: str
    clinical_justification: Optional[str] = None

    # Updated diagnosis
    updated_diagnosis: Optional[str] = None
    updated_icd10_code: Optional[str] = None

    # Updated treatment
    updated_line_of_treatment: Optional[str] = None
    updated_surgery_name: Optional[str] = None
    updated_icd10_pcs_code: Optional[str] = None

    # Revised costs
    revised_room_rent_per_day: Optional[float] = None
    revised_icu_charges_per_day: Optional[float] = None
    revised_ot_charges: Optional[float] = None
    revised_surgeon_fees: Optional[float] = None
    revised_medicines_consumables: Optional[float] = None
    revised_investigations: Optional[float] = None
    revised_total_estimated_cost: Optional[float] = None


class EnhancementResponse(EnhancementRequest):
    id: str
    status: str = "draft"           # draft | submitted | approved | rejected
    tpa_remarks: Optional[str] = None
    # Snapshot of original pre-auth data for history display
    original_diagnosis: Optional[str] = None
    original_icd10_code: Optional[str] = None
    original_total_cost: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PatientCaseHistory(BaseModel):
    """Summary returned when searching by ABHA ID — one pre-auth + its enhancements."""
    pre_auth_id: str
    patient_name: Optional[str] = None
    abha_id: Optional[str] = None
    provisional_diagnosis: Optional[str] = None
    icd10_diagnosis_code: Optional[str] = None
    admission_date: Optional[str] = None
    admission_type: Optional[str] = None
    hospital_name: Optional[str] = None
    total_estimated_cost: Optional[float] = None
    status: str
    created_at: Optional[str] = None
    enhancements: List[EnhancementResponse] = []
