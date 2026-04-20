"""
Document extraction helpers.
extract_receipt() — full receipt pipeline with validation.
extract_any_document() — generic pass-through for other document types.
"""

import logging
from datetime import datetime
from typing import Any

from app.extractor import extract_document
from app.prompts import DOC_TYPE_CONFIG, SUPPORTED_DOC_TYPES
from app.models import EmailExtraction, InvoiceExtraction
from app.gst_exempt import is_gst_exempt, get_exempt_reason

logger = logging.getLogger(__name__)


def _resolve_line_gst(items: list, total_gst: float | None, gst_summary: dict | None = None) -> list:
    """
    Four-tier GST resolution applied to every line item:

    Priority 1 — Receipt GST code (Z/G/F/* printed on the receipt)
                 Most reliable: the merchant's own POS system labelled it.
    Priority 2 — ATO GST-exempt rules (keyword + category matching)
                 Catches items where the code was missing or unclear.
    Priority 3 — Per-line 1/11 calculation for confirmed taxable items.
    Priority 4 — Proportional redistribution when line totals don't
                 reconcile with the document-level GST total.

    GST summary table (if extracted) is used as the authoritative total
    for reconciliation in Priority 4.
    """
    # Resolve authoritative total GST — prefer gst_summary over document field
    authoritative_gst = None
    if gst_summary and gst_summary.get("gst_total") is not None:
        authoritative_gst = gst_summary["gst_total"]
    elif total_gst is not None:
        authoritative_gst = total_gst

    for item in items:
        desc = item.get("line_description", "")
        cat = item.get("item_category")
        code = (item.get("gst_code") or "").upper().strip()

        # Priority 1 — use the printed GST code
        if code in ("Z", "F"):
            item["gst_exempt"] = True
            item["gst_amount"] = 0.0
            continue
        elif code in ("G", "*"):
            item["gst_exempt"] = False
            # gst_amount will be calculated in Priority 3 below

        # Priority 2 — ATO exempt rules (only when no code present)
        elif not code:
            if is_gst_exempt(desc, cat):
                item["gst_exempt"] = True
                item["gst_amount"] = 0.0
                continue

        # Priority 3 — calculate 1/11 for confirmed taxable items
        if not item.get("gst_exempt") and item.get("gst_amount") is None:
            item["gst_amount"] = round((item.get("line_amount") or 0) / 11, 2)

    # Priority 4 — proportional reconciliation
    if authoritative_gst is not None:
        calculated = sum(i.get("gst_amount") or 0 for i in items)
        if abs(calculated - authoritative_gst) > 0.05:
            taxable = [i for i in items if not i.get("gst_exempt")]
            taxable_gross = sum(i.get("line_amount") or 0 for i in taxable)
            if taxable_gross > 0:
                for item in taxable:
                    proportion = (item.get("line_amount") or 0) / taxable_gross
                    item["gst_amount"] = round(authoritative_gst * proportion, 2)
                logger.info(
                    f"GST reconciled: line total ${calculated:.2f} → "
                    f"authoritative ${authoritative_gst:.2f} across "
                    f"{len(taxable)} taxable item(s)"
                )

    return items


_PAYMENT_KEYWORDS = {
    "visa card", "mastercard", "master card", "amex", "american express",
    "cash payment", "cash", "eftpos", "eftpos payment", "payment received",
    "payment", "deposit", "prepayment", "pre-payment", "pre payment",
    "credit card", "debit card", "card payment", "bank transfer",
    "direct debit", "cheque", "check",
}

def _is_payment_line(description: str) -> bool:
    desc = description.lower().strip()
    return any(kw in desc for kw in _PAYMENT_KEYWORDS)


def _strip_payment_lines(items: list) -> tuple[list, list]:
    """
    Separate charge items from payment records.
    Returns (charge_items, payment_lines).
    """
    charges, payments = [], []
    for item in items:
        desc = item.get("line_description", "")
        amount = item.get("line_amount", 0) or 0
        if _is_payment_line(desc) and amount <= 0:
            payments.append(item)
        else:
            charges.append(item)
    return charges, payments


def extract_receipt(file_path: str, content_type: str) -> dict[str, Any]:
    """
    Run GPT-4.1-mini extraction on a receipt, then validate and normalise the result.
    Returns a dict ready to be unpacked into ReceiptResponse.
    """
    system_prompt, schema_name, schema = DOC_TYPE_CONFIG["receipt"]

    raw = extract_document(file_path, content_type, schema_name, schema, system_prompt)
    logger.info(f"Raw extraction: merchant={raw.get('merchant_name')}, total={raw.get('transaction_amount')}")

    # --- Separate payment lines from charge items ---
    raw_items = raw.get("items") or []
    items, payment_lines_raw = _strip_payment_lines(raw_items)

    # Build structured payment_lines list
    payment_lines = []
    for pl in payment_lines_raw:
        payment_lines.append({
            "description": pl.get("line_description", "Payment"),
            "amount": abs(pl.get("line_amount", 0) or 0),
            "payment_method": "card" if any(
                kw in pl.get("line_description", "").lower()
                for kw in ["visa", "mastercard", "amex", "eftpos", "credit", "debit"]
            ) else "cash",
        })

    # --- Fix transaction_amount when model returned 0 (balance due) ---
    tx_total = raw.get("transaction_amount") or 0
    if tx_total == 0 and items:
        tx_total = round(sum(i.get("line_amount", 0) or 0 for i in items), 2)
        logger.info(
            f"transaction_amount was 0 (balance due on folio) — "
            f"recalculated from charge lines: ${tx_total:.2f}"
        )

    # --- Auto-generate single item if no charge lines found ---
    if not items:
        items = [{
            "line_number": 1,
            "line_description": raw.get("merchant_name", "Unknown"),
            "quantity": 1,
            "unit_price": tx_total,
            "line_amount": tx_total,
            "gst_amount": raw.get("gst_amount"),
            "gst_code": None,
            "gst_exempt": False,
            "item_category": "general_retail",
            "notes": "Auto-generated: no line items detected",
        }]

    items = _resolve_line_gst(items, raw.get("gst_amount"), raw.get("gst_summary"))

    # --- Validation ---
    items_total = sum(i.get("line_amount", 0) or 0 for i in items)
    tx_total = raw.get("transaction_amount", 0.0) or 0.0
    items_match = abs(items_total - tx_total) < 0.05

    # --- Date fallback ---
    transaction_date = raw.get("transaction_date")
    if not transaction_date:
        transaction_date = datetime.now().strftime("%Y-%m-%d")
        logger.info("No date on receipt — using today as fallback")

    confidence = raw.get("confidence", 0.9) or 0.9

    receipt_data = {
        "document_subtype":   raw.get("document_subtype", "receipt"),
        "merchant_name":      raw.get("merchant_name") or "Unknown Merchant",
        "merchant_abn":       raw.get("merchant_abn"),
        "merchant_address":   raw.get("merchant_address"),
        "merchant_phone":     raw.get("merchant_phone"),
        "transaction_amount": tx_total,
        "subtotal_amount":    raw.get("subtotal_amount"),
        "gst_amount":         raw.get("gst_amount"),
        "discount_amount":    raw.get("discount_amount"),
        "surcharge_amount":   raw.get("surcharge_amount"),
        "category_group":     raw.get("category_group"),
        "transaction_date":   transaction_date,
        "transaction_time":   raw.get("transaction_time"),
        "receipt_number":     raw.get("receipt_number"),
        "payment_method":     raw.get("payment_method") or "card",
        "card_last_four":     raw.get("card_last_four"),
        "loyalty_points":     raw.get("loyalty_points"),
        "gst_summary":        raw.get("gst_summary"),
        "payment_lines":      payment_lines or None,
        "items":              items,
        "ocr_confidence":     confidence,
        "receipt_status":     2,
        "is_manually_entered": False,
        "items_total_matches": items_match,
        "items_total_difference": round(tx_total - items_total, 2) if not items_match else None,
    }

    warnings = _build_warnings(receipt_data, items, items_total, tx_total, items_match)

    subtype = raw.get("document_subtype", "receipt")
    if subtype != "receipt":
        warnings.insert(0, f"Document identified as '{subtype}' — transaction_amount reflects total charges, not balance due")

    return {
        "success": True,
        "receipt_data": receipt_data,
        "raw_data": raw,
        "validation_warnings": warnings or None,
    }


def extract_invoice(file_path: str, content_type: str) -> dict[str, Any]:
    """Run GPT-4.1-mini extraction on an invoice with full field capture."""
    system_prompt, schema_name, schema = DOC_TYPE_CONFIG["invoice"]
    raw = extract_document(file_path, content_type, schema_name, schema, system_prompt)

    logger.info(
        f"Invoice extracted — vendor={raw.get('vendor_name')}, "
        f"total={raw.get('invoice_total_amount')}, items={len(raw.get('items', []))}"
    )

    warnings = []
    if raw.get("confidence", 1.0) < 0.8:
        warnings.append(f"Low extraction confidence: {raw['confidence'] * 100:.0f}%")
    if not raw.get("due_date"):
        warnings.append("Due date not found — please set manually")
    if not raw.get("gst_amount"):
        warnings.append("GST amount not found — inferred from total")

    items = _resolve_line_gst(raw.get("items") or [], raw.get("gst_amount"))
    raw["items"] = items

    items_total = sum(i.get("line_amount", 0) or 0 for i in items)
    total = raw.get("invoice_total_amount", 0) or 0
    if items and abs(items_total - total) > 0.05:
        warnings.append(
            f"Line items total (${items_total:.2f}) does not match invoice total (${total:.2f})"
        )

    return {
        "success": True,
        "invoice_data": raw,
        "raw_data": raw,
        "validation_warnings": warnings or None,
    }


def extract_email(file_path: str, content_type: str) -> dict[str, Any]:
    """
    Run GPT-4.1-mini extraction on an email document.
    Returns categorisation, summary, action items, attachments, and financial fields.
    """
    system_prompt, schema_name, schema = DOC_TYPE_CONFIG["email"]
    raw = extract_document(file_path, content_type, schema_name, schema, system_prompt)

    logger.info(
        f"Email extracted — category={raw.get('category')}, "
        f"priority={raw.get('priority')}, requires_action={raw.get('requires_action')}"
    )

    warnings = []
    if raw.get("confidence", 1.0) < 0.8:
        warnings.append(f"Low extraction confidence: {raw['confidence'] * 100:.0f}%")
    if raw.get("requires_action") and not raw.get("due_date"):
        warnings.append("Action required but no due date found — please set manually")

    return {
        "success": True,
        "email_data": raw,
        "validation_warnings": warnings or None,
    }


def extract_any_document(file_path: str, content_type: str, document_type: str) -> dict[str, Any]:
    """Generic extraction for invoice, statement, email etc."""
    if document_type not in DOC_TYPE_CONFIG:
        raise ValueError(f"Unknown document_type '{document_type}'. Supported: {SUPPORTED_DOC_TYPES}")

    system_prompt, schema_name, schema = DOC_TYPE_CONFIG[document_type]
    data = extract_document(file_path, content_type, schema_name, schema, system_prompt)

    warnings = []
    confidence = data.get("confidence", 1.0) or 1.0
    if confidence < 0.8:
        warnings.append(f"Low extraction confidence: {confidence * 100:.0f}%")

    return {
        "success": True,
        "data": data,
        "validation_warnings": warnings or None,
    }


def _build_warnings(receipt_data, items, items_total, tx_total, items_match) -> list[str]:
    warnings = []

    if not items_match:
        warnings.append(
            f"Line items total (${items_total:.2f}) does not match transaction amount (${tx_total:.2f})"
        )
    if receipt_data["ocr_confidence"] < 0.8:
        warnings.append(f"Low extraction confidence: {receipt_data['ocr_confidence'] * 100:.0f}%")
    if not receipt_data.get("receipt_number"):
        warnings.append("Receipt number not found")
    if len(items) == 1 and items[0].get("notes") == "Auto-generated: no line items detected":
        warnings.append("No line items detected — created default item from total")

    return warnings
