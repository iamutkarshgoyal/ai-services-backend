from app.repositories.invoice_repository import (
    InvoiceNotFoundError,
    get_invoice_details,
    invoice_exists,
    update_invoice_fields,
)
from app.graphs.approvals import Invoice_update_approval
from langgraph.types import interrupt
from app.graphs.state import InvoiceState
from datetime import date
from decimal import Decimal, InvalidOperation


def _require(value: object, field_name: str) -> None:
    if value is None or (isinstance(value, str) and not value.strip()):
        field_label = field_name.replace("_", " ")
        return {"response": f"Unable to identify exact {value} for field: {field_label}"}

    
def Invoice_tool(state: InvoiceState) -> dict:
    """Collect missing invoice fields, confirm each change, then apply approved edits."""

    fields = {
        "update_total_amount": "total_amount",
        "update_due_date": "due_date",
        "update_status": "status",}

    intents = list(dict.fromkeys(state.intent))
    messages = []
    if "get_invoice_pdf" in intents:
        messages.append("Invoice PDF download is currently unavailable.")

    if not any(intent in fields or intent == "get_invoice_details" for intent in intents):
        if not messages:
            messages.append("Would you like invoice details or a change to the amount, due date, or status?")
        return {"response": " ".join(messages)}

    def clarify(field: str, question: str):
        reply = interrupt({"type": "clarification", "field": field, "question": question})
        return reply.get("value") if isinstance(reply, dict) else reply

    identifier = state.invoice_id
    while not isinstance(identifier, str) or not identifier.strip():
        identifier = clarify("invoice_id", "Which invoice ID should I use?")
    invoice = state.model_copy(update={"invoice_id": identifier.strip()})
    if not invoice_exists(invoice.invoice_id):
        return {"response": f"Invoice {invoice.invoice_id} was not found."}

    approved = {}
    rejected = []
    for intent in intents:
        if intent not in fields:
            continue
        column = fields[intent]
        label = column.replace("_", " ")
        question = f"What should the new {label} be for invoice {invoice.invoice_id}?"
        value = getattr(invoice, column)

        while True:
            if column == "total_amount":
                try:
                    amount = Decimal(str(value))
                    if amount.is_finite():
                        value = str(amount)
                        break
                except InvalidOperation:
                    pass
                hint = "Enter a numeric amount."
            elif column == "due_date":
                try:
                    value = date.fromisoformat(str(value)).isoformat()
                    break
                except ValueError:
                    hint = "Use YYYY-MM-DD."
            else:
                if isinstance(value, str) and value.strip():
                    value = value.strip()
                    break
                hint = "Enter a status."
            value = clarify(column, f"{question} {hint}")

        decision = interrupt({
            "type": "approval",
            "question": f"Update {label} to {value} for invoice {invoice.invoice_id}?",
            "allowed_responses": ["yes", "no"],
            "approved": [True, False],
        })
        if Invoice_update_approval.model_validate(decision).approved:
            approved[column] = value
        else:
            rejected.append(label)

    if approved:
        # Apply the approved fields together after all review prompts have finished.
        try:
            update_invoice_fields(invoice.invoice_id, approved)
        except InvoiceNotFoundError as exc:
            return {"response": str(exc)}
        changes = ", ".join(f"{key.replace('_', ' ')} = {value}" for key, value in approved.items())
        messages.append(f"Updated invoice {invoice.invoice_id}: {changes}.")
    if rejected:
        messages.append(f"Rejected for invoice {invoice.invoice_id}: {', '.join(rejected)}.")
        
    if "get_invoice_details" in intents:
        row = get_invoice_details(invoice.invoice_id)
        if row is not None:
            details = ", ".join(f"{key}: {val}" for key, val in row.items())
            messages.append(f"Invoice {invoice.invoice_id} details: {details}.")
        else:
            messages.append(f"Invoice {invoice.invoice_id} was not found.")
    return {"response": " ".join(messages)}
