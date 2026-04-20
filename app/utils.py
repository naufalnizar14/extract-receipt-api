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

    if not raw.get("document_type_verified", True):
        detected = raw.get("detected_document_type", "unknown")
        return {
            "success": False,
            "error": (
                f"Document does not appear to be a receipt or tax invoice. "
                f"Detected: '{detected}'. Please re-upload using the correct document type."
            ),
        }

    logger.info(f"Raw extraction: merchant={raw.get('merchant_name')}, total={raw.get('transaction_amount')}")

    # --- Separate payment lines from charge items ---
    # The model may have already extracted payment_lines separately (preferred),
    # or they may still be mixed into items (fallback: strip them out ourselves)
    raw_items = raw.get("items") or []
    items, payment_lines_raw = _strip_payment_lines(raw_items)

    # Prefer model-extracted payment_lines; fall back to what we stripped
    # Strip surcharge entries — the model sometimes puts surcharges in payment_lines by mistake;
    # they are already captured in surcharge_amount and are not payment records.
    model_payment_lines = [
        pl for pl in (raw.get("payment_lines") or [])
        if "surcharge" not in pl.get("description", "").lower()
    ]
    if model_payment_lines:
        payment_lines = model_payment_lines
    else:
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

    # --- Resolve correct GST-inclusive transaction_amount ---
    # Priority 1: GST summary total = zero_rated_net + taxable_gross
    #             (taxable_gross alone is ONLY the G/taxable portion — must add Z items)
    #             Only override raw_tx when there is a meaningful discrepancy (>$0.05),
    #             which indicates the model returned an ex-GST or balance-due amount.
    # Priority 2: sum of charge line_amounts when raw_tx = 0 (balance-due folios)
    # Priority 3: raw_tx + doc-level gst when raw_tx looks ex-GST
    # Priority 4: trust raw_tx as-is
    gst_summary = raw.get("gst_summary") or {}
    taxable_gross = gst_summary.get("taxable_gross")
    zero_rated_net = gst_summary.get("zero_rated_net") or 0
    raw_tx = raw.get("transaction_amount") or 0
    gst_amount_doc = raw.get("gst_amount") or 0

    surcharge_raw = raw.get("surcharge_amount") or 0

    # Summary total = GST-free items + GST-inclusive taxable items (never includes surcharge)
    summary_total = round(zero_rated_net + taxable_gross, 2) if taxable_gross is not None else None

    if summary_total and summary_total > 0:
        diff = abs(raw_tx - summary_total)
        if diff <= 0.05:
            # raw_tx already matches summary — trust it as-is
            tx_total = raw_tx
        elif abs(raw_tx - summary_total - surcharge_raw) <= 0.05:
            # Difference equals the surcharge — raw_tx correctly includes surcharge, keep it
            tx_total = raw_tx
        else:
            # Genuine discrepancy (e.g. model returned ex-GST) — rebuild from summary + surcharge
            tx_total = round(summary_total + surcharge_raw, 2)
            logger.info(
                f"transaction_amount corrected from ${raw_tx:.2f} "
                f"to ${tx_total:.2f} using gst_summary "
                f"(zero_rated=${zero_rated_net:.2f} + taxable_gross=${taxable_gross:.2f} + surcharge=${surcharge_raw:.2f})"
            )
    elif raw_tx == 0 and items:
        # Balance-due folio — recalculate from charge lines
        tx_total = round(sum(i.get("line_amount", 0) or 0 for i in items), 2)
        logger.info(f"transaction_amount was 0 — recalculated from charge lines: ${tx_total:.2f}")
    elif abs(raw_tx + gst_amount_doc - round(sum(i.get("line_amount", 0) or 0 for i in items), 2)) < 0.05:
        # raw_tx looks like ex-GST (raw_tx + gst ≈ items total) — correct it
        tx_total = round(raw_tx + gst_amount_doc, 2)
        logger.info(f"transaction_amount was ex-GST ${raw_tx:.2f} — corrected to ${tx_total:.2f}")
    else:
        tx_total = raw_tx

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
    surcharge = raw.get("surcharge_amount") or 0
    # tx_total was already resolved above (taxable_gross / line sum / raw_tx) — do not overwrite
    # Surcharge is not a purchased item so add it back before comparing
    items_match = abs(items_total + surcharge - tx_total) < 0.05

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
        "items_total_difference": round(tx_total - surcharge - items_total, 2) if not items_match else None,
    }

    warnings = _build_warnings(receipt_data, items, items_total, tx_total, items_match, surcharge)

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

    if not raw.get("document_type_verified", True):
        detected = raw.get("detected_document_type", "unknown")
        return {
            "success": False,
            "error": (
                f"Document does not appear to be an invoice. "
                f"Detected: '{detected}'. Please re-upload using the correct document type."
            ),
        }

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
    items_gst_total = sum(i.get("gst_amount", 0) or 0 for i in items)
    doc_gst = raw.get("gst_amount", 0) or 0
    total = raw.get("invoice_total_amount", 0) or 0
    # Line amounts on Australian invoices are typically ex-GST; accept any of:
    # 1. lines already GST-inclusive
    # 2. lines ex-GST + per-line GST totals
    # 3. lines ex-GST + document-level GST (model may only extract GST at header level)
    items_match = (
        abs(items_total - total) < 0.05
        or abs(items_total + items_gst_total - total) < 0.05
        or abs(items_total + doc_gst - total) < 0.05
    )
    if items and not items_match:
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

    if not raw.get("document_type_verified", True):
        detected = raw.get("detected_document_type", "unknown")
        return {
            "success": False,
            "error": (
                f"Document does not appear to be an email. "
                f"Detected: '{detected}'. Please re-upload using the correct document type."
            ),
        }

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

    if not data.get("document_type_verified", True):
        detected = data.get("detected_document_type", "unknown")
        return {
            "success": False,
            "error": (
                f"Document does not appear to be a {document_type}. "
                f"Detected: '{detected}'. Please re-upload using the correct document type."
            ),
        }

    warnings = []
    confidence = data.get("confidence", 1.0) or 1.0
    if confidence < 0.8:
        warnings.append(f"Low extraction confidence: {confidence * 100:.0f}%")

    return {
        "success": True,
        "data": data,
        "validation_warnings": warnings or None,
    }


def _build_warnings(receipt_data, items, items_total, tx_total, items_match, surcharge=0.0) -> list[str]:
    warnings = []

    if not items_match:
        items_plus_surcharge = items_total + surcharge
        expected = tx_total
        detail = f"${items_total:.2f} items"
        if surcharge:
            detail += f" + ${surcharge:.2f} surcharge = ${items_plus_surcharge:.2f}"
        warnings.append(
            f"Line items total ({detail}) does not match transaction amount (${expected:.2f})"
        )
    if receipt_data["ocr_confidence"] < 0.8:
        warnings.append(f"Low extraction confidence: {receipt_data['ocr_confidence'] * 100:.0f}%")
    if not receipt_data.get("receipt_number"):
        warnings.append("Receipt number not found")
    if len(items) == 1 and items[0].get("notes") == "Auto-generated: no line items detected":
        warnings.append("No line items detected — created default item from total")

    return warnings
