from pydantic import BaseModel
from typing import Literal


class Invoice_update_approval(BaseModel):
    approved: bool
    note: str | None = None
    sick_leave_balance: int | None = None
    paid_leave_balance: int | None = None


class Leave_balance_approval(BaseModel):
    approved: bool
    sick_leave_balance: int | None = None
    paid_leave_balance: int | None = None


class Invoice_intent_approval(BaseModel):
    intent: list[Literal["update_total_amount", "update_due_date", "update_status", "get_invoice_details", "get_invoice_pdf", "other"]]
    note: str | None = None