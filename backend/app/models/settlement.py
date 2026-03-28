from pydantic import BaseModel
from typing import Optional


class SettlementRequest(BaseModel):
    bill_no: str
    pre_auth_id: Optional[str] = None
    discharge_id: Optional[str] = None
    abha_id: Optional[str] = None
    pre_auth_approved_amount: Optional[float] = None
    claimed_amount: Optional[float] = None
    deduction_amount: float = 0.0
    deduction_reason: Optional[str] = None
    final_settlement_amount: Optional[float] = None
    status: str = "pending"
    tpa_remarks: Optional[str] = None
    settlement_date: Optional[str] = None


class SettlementResponse(SettlementRequest):
    id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
