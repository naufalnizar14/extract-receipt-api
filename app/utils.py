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

logger = logging.getLogger(__name__)


def extract_receipt(file_path: str, content_type: str) -> dict[str, Any]:
    """
    Run GPT-4.1-mini extraction on a receipt, then validate and normalise the result.
    Returns a dict ready to be unpacked into ReceiptResponse.
    """
    system_prompt, schema_name, schema = DOC_TYPE_CONFIG["receipt"]

    raw = extract_document(file_path, content_type, schema_name, schema, system_prompt)
    logger.info(f"Raw extraction: merchant={raw.get('merchant_name')}, total={raw.get('transaction_amount')}")

    # --- Line items ---
    items = raw.get("items") or []
    if not items:
        total = raw.get("transaction_amount", 0.0) or 0.0
        items = [{
            "line_number": 1,
            "line_description": raw.get("merchant_name", "Unknown"),
            "quantity": 1,
            "unit_price": total,
            "line_amount": total,
            "gst_amount": raw.get("gst_amount"),
            "item_category": None,
            "notes": "Auto-generated: no line items detected",
        }]

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
        "merchant_name":      raw.get("merchant_name") or "Unknown Merchant",
        "merchant_abn":       raw.get("merchant_abn"),
        "merchant_address":   raw.get("merchant_address"),
        "merchant_phone":     raw.get("merchant_phone"),
        "transaction_amount": tx_total,
        "subtotal_amount":    raw.get("subtotal_amount"),
        "gst_amount":         raw.get("gst_amount"),
        "discount_amount":    raw.get("discount_amount"),
        "surcharge_amount":   raw.get("surcharge_amount"),
        "transaction_date":   transaction_date,
        "transaction_time":   raw.get("transaction_time"),
        "receipt_number":     raw.get("receipt_number"),
        "payment_method":     raw.get("payment_method") or "card",
        "card_last_four":     raw.get("card_last_four"),
        "loyalty_points":     raw.get("loyalty_points"),
        "items":              items,
        "ocr_confidence":     confidence,
        "receipt_status":     2,
        "is_manually_entered": False,
        "items_total_matches": items_match,
        "items_total_difference": round(tx_total - items_total, 2) if not items_match else None,
    }

    warnings = _build_warnings(receipt_data, items, items_total, tx_total, items_match)

    return {
        "success": True,
        "receipt_data": receipt_data,
        "raw_data": raw,
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
