"""Database access for invoice lookups and approved field updates."""

from collections.abc import Mapping
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import text

from app.database.connection import engine


_EDITABLE_FIELDS = frozenset({"status", "due_date", "total_amount"})


class InvoiceNotFoundError(LookupError):
    """The invoice no longer exists at write time."""


def _identifier(invoice_id: str) -> str:
    if not isinstance(invoice_id, str) or not invoice_id.strip():
        raise ValueError("An invoice ID is required.")
    return invoice_id.strip()


def invoice_exists(invoice_id: str) -> bool:
    invoice_id = _identifier(invoice_id)
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT invoice_id FROM public.invoices WHERE invoice_id = :invoice_id"),
            {"invoice_id": invoice_id},
        )
        return result.scalar_one_or_none() is not None


def get_invoice_details(invoice_id: str) -> dict[str, Any] | None:
    invoice_id = _identifier(invoice_id)
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM public.invoices WHERE invoice_id = :invoice_id"),
            {"invoice_id": invoice_id},
        ).mappings().one_or_none()
        return dict(row) if row is not None else None


def update_invoice_fields(invoice_id: str, changes: Mapping[str, str]) -> None:
    """Commit all approved changes together, requiring exactly one matching invoice."""
    values = dict(changes)
    if not values or not values.keys() <= _EDITABLE_FIELDS:
        raise ValueError("Provide one or more editable invoice fields.")

    for field, value in values.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"A value is required for {field}.")
        values[field] = value.strip()
    if "total_amount" in values:
        try:
            amount = Decimal(values["total_amount"])
        except InvalidOperation as exc:
            raise ValueError("Invoice amount must be numeric.") from exc
        if not amount.is_finite():
            raise ValueError("Invoice amount must be finite.")
        values["total_amount"] = str(amount)
    if "due_date" in values:
        values["due_date"] = date.fromisoformat(values["due_date"]).isoformat()

    # Only allowlisted column names enter the SQL. All data uses bound parameters.
    assignments = ", ".join(f"{field} = :{field}" for field in values)
    statement = text(f"UPDATE public.invoices SET {assignments} WHERE invoice_id = :invoice_id")
    params = {**values, "invoice_id": _identifier(invoice_id)}
    with engine.begin() as conn:
        result = conn.execute(statement, params)
        if result.rowcount == 0:
            raise InvoiceNotFoundError(f"Invoice {params['invoice_id']} was not found.")
        if result.rowcount != 1:
            raise RuntimeError("Expected to update exactly one invoice.")
