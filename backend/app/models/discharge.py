from pydantic import BaseModel
from typing import Optional, List


class DischargeRequest(BaseModel):
    bill_no: str
    pre_auth_id: Optional[str] = None
    abha_id: Optional[str] = None
    discharge_date: Optional[str] = None
    final_diagnosis: Optional[str] = None
    final_icd10_codes: Optional[str] = None
    procedure_codes: Optional[str] = None
    discharge_summary_text: Optional[str] = None
    room_charges: Optional[float] = None
    icu_charges: Optional[float] = None
    surgery_charges: Optional[float] = None
    medicine_charges: Optional[float] = None
    investigation_charges: Optional[float] = None
    other_charges: Optional[float] = None
    total_bill_amount: Optional[float] = None
    status: str = "pending"


class DischargeResponse(DischargeRequest):
    id: str
    revenue_flags: List[dict] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DischargeExtract(BaseModel):
    discharge_date: Optional[str] = None
    final_diagnosis: Optional[str] = None
    final_icd10_codes: Optional[str] = None
    procedure_codes: Optional[str] = None
    room_charges: Optional[float] = None
    icu_charges: Optional[float] = None
    surgery_charges: Optional[float] = None
    medicine_charges: Optional[float] = None
    investigation_charges: Optional[float] = None
    other_charges: Optional[float] = None
    total_bill_amount: Optional[float] = None
