from pydantic import BaseModel, Field
from typing import Literal


class AgentState(BaseModel):
    conversation_id: str
    message: str
    response: str | None = None


class InvoiceState(BaseModel):
    intent: list[Literal["update_total_amount", "update_due_date", "update_status", "get_invoice_details", "get_invoice_pdf", "other"]]
    invoice_id: str | None = Field(default=None, description="Invoice ID explicitly present in the message")
    invoice_date: str | None = Field(default=None, description="Invoice date explicitly present, otherwise null")
    due_date: str | None = Field(default=None, description="Due date explicitly present, otherwise null")
    total_amount: float | None = Field(default=None, description="Amount explicitly present, otherwise null")
    status: str | None = Field(default=None, description="Status explicitly present, otherwise null")


class CompanyPolicyState(BaseModel):
    intent: list[Literal["get_policy_details", "update_sick_leave", "update_paid_leave"]]
    policy_id: str | None = Field(default=None, description="Policy ID explicitly present in the message")
    title: str | None = Field(default=None, description="Policy title explicitly present in the message, otherwise null")
    employee_id: int | None = Field(default=None, description="Employee ID explicitly present in the message, otherwise null")
    employee_name: str | None = Field(default=None, description="Employee name explicitly present in the message, otherwise null")
    sick_leave: int | None = Field(default=None, description="Sick leave days explicitly present in the message, otherwise null")
    paid_leave: int | None = Field(default=None, description="Paid leave days explicitly present in the message, otherwise null")


class TechnicalState(BaseModel):
    intent: list[Literal["code_review", "bug_fix", "feature_request", "language_update"]]
    project: str | None = Field(default=None, description="Project name explicitly present in the message")
    language: Literal["Python", "JavaScript", "Java", "C++"] | None = Field(default=None, description="Programming language explicitly present in the message")
    code_snippet: str | None = Field(default=None, description="Code snippet explicitly present in the message, otherwise null")
