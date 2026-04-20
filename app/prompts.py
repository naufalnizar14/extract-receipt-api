"""
System prompts and JSON schemas per document type.
To add a new document type: add a prompt, a schema, and register it in DOC_TYPE_CONFIG.

Schemas must be strict-mode compatible:
  - Every property listed in "required"
  - additionalProperties: false on every object
  - Nullable fields use {"type": ["string", "null"]} etc.
"""

# ---------------------------------------------------------------------------
# RECEIPT
# ---------------------------------------------------------------------------

RECEIPT_SYSTEM = """
You are an expert receipt and tax invoice parser for Australian businesses.

Rules:
- Extract every field you can see. Do not guess values that are not visible.
- GST: if not explicitly shown, infer as (total / 11) rounded to 2 decimal places for Australian receipts.
- Payment method: map EFTPOS, payWave, tap, Visa, Mastercard, Amex, credit, debit → "card". Map cash → "cash". Default to "card".
- Line items: extract every item shown. If no items are visible, create one item using the merchant name and transaction total.
- transaction_date: format as YYYY-MM-DD. If not visible return null.
- transaction_time: format as HH:MM. If not visible return null.
- item_category: infer from context (e.g. "Fuel", "Groceries", "Food & Beverage", "Office Supplies", "Parking", "Travel", "Accommodation", "Entertainment", "Medical", "Other").
- confidence: 0.0–1.0 reflecting how clearly the document shows the extracted data.
- merchant_abn: Australian Business Number if shown (format: XX XXX XXX XXX).
- card_last_four: last 4 digits of card number if shown on receipt.
- surcharge_amount: any card surcharge, service fee, or processing fee added on top of the subtotal. Common labels: "Surcharge", "Card Surcharge", "Service Fee", "Credit Card Fee". Return null if not present.
- Return null for any field not found — never fabricate data.
"""

RECEIPT_SCHEMA = {
    "type": "object",
    "required": [
        "merchant_name", "merchant_abn", "merchant_address", "merchant_phone",
        "transaction_amount", "subtotal_amount", "gst_amount", "discount_amount",
        "surcharge_amount", "transaction_date", "transaction_time", "receipt_number",
        "payment_method", "card_last_four", "loyalty_points",
        "confidence", "items"
    ],
    "additionalProperties": False,
    "properties": {
        "merchant_name":     {"type": "string"},
        "merchant_abn":      {"type": ["string", "null"]},
        "merchant_address":  {"type": ["string", "null"]},
        "merchant_phone":    {"type": ["string", "null"]},
        "transaction_amount": {"type": "number"},
        "subtotal_amount":   {"type": ["number", "null"]},
        "gst_amount":        {"type": ["number", "null"]},
        "discount_amount":   {"type": ["number", "null"]},
        "surcharge_amount":  {"type": ["number", "null"]},
        "transaction_date":  {"type": ["string", "null"]},
        "transaction_time":  {"type": ["string", "null"]},
        "receipt_number":    {"type": ["string", "null"]},
        "payment_method":    {"type": "string", "enum": ["card", "cash"]},
        "card_last_four":    {"type": ["string", "null"]},
        "loyalty_points":    {"type": ["string", "null"]},
        "confidence":        {"type": "number"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "line_number", "line_description", "quantity",
                    "unit_price", "line_amount", "gst_amount", "item_category", "notes"
                ],
                "additionalProperties": False,
                "properties": {
                    "line_number":      {"type": "integer"},
                    "line_description": {"type": "string"},
                    "quantity":         {"type": ["number", "null"]},
                    "unit_price":       {"type": ["number", "null"]},
                    "line_amount":      {"type": "number"},
                    "gst_amount":       {"type": ["number", "null"]},
                    "item_category":    {"type": ["string", "null"]},
                    "notes":            {"type": ["string", "null"]},
                }
            }
        }
    }
}

# ---------------------------------------------------------------------------
# INVOICE
# ---------------------------------------------------------------------------

INVOICE_SYSTEM = """
You are an expert tax invoice parser for Australian businesses.

Rules:
- Extract every visible field. Do not guess values not present.
- GST: if not explicitly shown, infer as (total / 11) rounded to 2 decimal places.
- All dates: format as YYYY-MM-DD.
- po_reference: Purchase Order number if present.
- payment_terms examples: "Net 30", "Due on receipt", "14 days".
- bank_bsb: 6-digit BSB number if shown (format: XXX-XXX).
- vendor_abn: Australian Business Number if shown (format: XX XXX XXX XXX).
- item_category: infer from line item descriptions.
- confidence: 0.0–1.0 reflecting extraction clarity.
- Return null for any field not found.
"""

INVOICE_SCHEMA = {
    "type": "object",
    "required": [
        "vendor_name", "vendor_abn", "vendor_address", "vendor_email", "vendor_phone",
        "invoice_number", "invoice_date", "due_date", "payment_terms",
        "po_reference", "invoice_total_amount", "subtotal_amount", "gst_amount",
        "bank_bsb", "bank_account_number", "bank_account_name",
        "confidence", "items"
    ],
    "additionalProperties": False,
    "properties": {
        "vendor_name":           {"type": "string"},
        "vendor_abn":            {"type": ["string", "null"]},
        "vendor_address":        {"type": ["string", "null"]},
        "vendor_email":          {"type": ["string", "null"]},
        "vendor_phone":          {"type": ["string", "null"]},
        "invoice_number":        {"type": "string"},
        "invoice_date":          {"type": "string"},
        "due_date":              {"type": ["string", "null"]},
        "payment_terms":         {"type": ["string", "null"]},
        "po_reference":          {"type": ["string", "null"]},
        "invoice_total_amount":  {"type": "number"},
        "subtotal_amount":       {"type": ["number", "null"]},
        "gst_amount":            {"type": ["number", "null"]},
        "bank_bsb":              {"type": ["string", "null"]},
        "bank_account_number":   {"type": ["string", "null"]},
        "bank_account_name":     {"type": ["string", "null"]},
        "confidence":            {"type": "number"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "line_number", "line_description", "quantity",
                    "unit_price", "line_amount", "gst_amount", "item_category", "notes"
                ],
                "additionalProperties": False,
                "properties": {
                    "line_number":      {"type": "integer"},
                    "line_description": {"type": "string"},
                    "quantity":         {"type": ["number", "null"]},
                    "unit_price":       {"type": ["number", "null"]},
                    "line_amount":      {"type": "number"},
                    "gst_amount":       {"type": ["number", "null"]},
                    "item_category":    {"type": ["string", "null"]},
                    "notes":            {"type": ["string", "null"]},
                }
            }
        }
    }
}

# ---------------------------------------------------------------------------
# BANK / CREDIT CARD STATEMENT
# ---------------------------------------------------------------------------

STATEMENT_SYSTEM = """
You are an expert bank and credit card statement parser.

Rules:
- Extract every transaction line visible on the statement.
- type: "debit" for money going out, "credit" for money coming in.
- All dates: format as YYYY-MM-DD.
- amounts: always positive numbers regardless of debit/credit direction.
- account_number: mask all but last 4 digits if partially shown.
- confidence: 0.0–1.0 reflecting extraction clarity.
- Return null for any field not found.
"""

STATEMENT_SCHEMA = {
    "type": "object",
    "required": [
        "account_holder", "bank_name", "account_number", "account_type",
        "statement_period_start", "statement_period_end",
        "opening_balance", "closing_balance", "total_debits", "total_credits",
        "confidence", "transactions"
    ],
    "additionalProperties": False,
    "properties": {
        "account_holder":        {"type": "string"},
        "bank_name":             {"type": ["string", "null"]},
        "account_number":        {"type": ["string", "null"]},
        "account_type":          {"type": ["string", "null"]},
        "statement_period_start": {"type": ["string", "null"]},
        "statement_period_end":  {"type": ["string", "null"]},
        "opening_balance":       {"type": ["number", "null"]},
        "closing_balance":       {"type": ["number", "null"]},
        "total_debits":          {"type": ["number", "null"]},
        "total_credits":         {"type": ["number", "null"]},
        "confidence":            {"type": "number"},
        "transactions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["date", "description", "amount", "type", "balance", "reference", "category"],
                "additionalProperties": False,
                "properties": {
                    "date":        {"type": "string"},
                    "description": {"type": "string"},
                    "amount":      {"type": "number"},
                    "type":        {"type": "string", "enum": ["debit", "credit"]},
                    "balance":     {"type": ["number", "null"]},
                    "reference":   {"type": ["string", "null"]},
                    "category":    {"type": ["string", "null"]},
                }
            }
        }
    }
}

# ---------------------------------------------------------------------------
# EMAIL (booking confirmations, order confirmations, payment receipts)
# ---------------------------------------------------------------------------

EMAIL_SYSTEM = """
You are an expert at extracting expense and financial information from emails.

Rules:
- Identify the document_type: "booking_confirmation", "order_confirmation", "payment_receipt", "subscription_receipt", "refund", or "other".
- Extract merchant/sender details and any financial amounts shown.
- All dates: format as YYYY-MM-DD.
- currency: ISO 4217 code (e.g. "AUD", "USD").
- Extract any line items or booking details visible in the email body.
- confidence: 0.0–1.0 reflecting extraction clarity.
- Return null for any field not found.
"""

EMAIL_SCHEMA = {
    "type": "object",
    "required": [
        "email_subject", "sender_name", "sender_email", "date_sent",
        "document_type", "merchant_name", "reference_number",
        "total_amount", "currency", "confidence", "line_items"
    ],
    "additionalProperties": False,
    "properties": {
        "email_subject":    {"type": ["string", "null"]},
        "sender_name":      {"type": ["string", "null"]},
        "sender_email":     {"type": ["string", "null"]},
        "date_sent":        {"type": ["string", "null"]},
        "document_type":    {
            "type": "string",
            "enum": ["booking_confirmation", "order_confirmation", "payment_receipt", "subscription_receipt", "refund", "other"]
        },
        "merchant_name":    {"type": ["string", "null"]},
        "reference_number": {"type": ["string", "null"]},
        "total_amount":     {"type": ["number", "null"]},
        "currency":         {"type": ["string", "null"]},
        "confidence":       {"type": "number"},
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["description", "amount", "quantity", "notes"],
                "additionalProperties": False,
                "properties": {
                    "description": {"type": "string"},
                    "amount":      {"type": ["number", "null"]},
                    "quantity":    {"type": ["number", "null"]},
                    "notes":       {"type": ["string", "null"]},
                }
            }
        }
    }
}

# ---------------------------------------------------------------------------
# Registry — add new document types here
# ---------------------------------------------------------------------------

DOC_TYPE_CONFIG: dict[str, tuple[str, str, dict]] = {
    #  key          (system_prompt,    schema_name,          schema)
    "receipt":   (RECEIPT_SYSTEM,   "extract_receipt",   RECEIPT_SCHEMA),
    "invoice":   (INVOICE_SYSTEM,   "extract_invoice",   INVOICE_SCHEMA),
    "statement": (STATEMENT_SYSTEM, "extract_statement", STATEMENT_SCHEMA),
    "email":     (EMAIL_SYSTEM,     "extract_email",     EMAIL_SCHEMA),
}

SUPPORTED_DOC_TYPES = list(DOC_TYPE_CONFIG.keys())
