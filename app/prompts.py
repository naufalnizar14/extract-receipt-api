"""
System prompts and JSON schemas per document type.
To add a new document type: add a prompt, a schema, and register it in DOC_TYPE_CONFIG.

Schemas must be strict-mode compatible:
  - Every property listed in "required"
  - additionalProperties: false on every object
  - Nullable fields use {"type": ["string", "null"]} etc.
"""

# ---------------------------------------------------------------------------
# Shared category taxonomy — mirrors credit-card-expense-management-app
# 20 category groups, 93 granular compliance categories
# ---------------------------------------------------------------------------

_CATEGORY_GROUPS = [
    "meals_dining", "travel_accommodation", "transport_vehicles", "fuel_energy",
    "office_stationery", "it_software", "telecommunications", "professional_services",
    "marketing_advertising", "training_education", "health_medical", "insurance_finance",
    "utilities_facilities", "construction_engineering", "tools_equipment",
    "safety_compliance", "retail_merchandise", "subscriptions_memberships",
    "government_official", "restricted_non_compliant",
]

_COMPLIANCE_CATEGORIES = [
    # meals_dining
    "restaurant", "fast_food", "coffee_shop", "bar_pub_tavern", "brewery",
    "food_delivery", "fresh_food_market", "catering_services", "convenience_store",
    "meat_deli", "staff_meals",
    # travel_accommodation
    "airline_flights", "hotel_accommodation", "airbnb_short_stay", "travel_agency",
    "visa_fees", "airport_transfers", "cruise", "travel_insurance",
    "conference_accommodation",
    # transport_vehicles
    "taxi_rideshare", "car_rental", "public_transport", "parking_fees", "toll_roads",
    "vehicle_leasing", "vehicle_maintenance", "motor_registration", "carwash",
    # fuel_energy
    "petrol_diesel", "lpg_gas", "ev_charging", "fuel_cards",
    # office_stationery
    "office_supplies", "stationery", "printing_copying", "postage_courier",
    "bookstore", "newsagent",
    # it_software
    "software_licenses", "it_hardware", "cloud_services", "web_hosting",
    "domain_registration", "it_support_services", "cybersecurity",
    # telecommunications
    "mobile_phone_plans", "internet_broadband", "landline_telephone",
    "satellite_comms", "conferencing_services",
    # professional_services
    "accounting_bookkeeping", "legal_services", "management_consulting",
    "engineering_consulting", "architectural_services", "recruitment_services",
    "freelance_services", "environmental_services",
    # marketing_advertising
    "digital_advertising", "print_advertising", "social_media_marketing",
    "pr_services", "promotional_materials", "events_sponsorship",
    "photography_videography",
    # training_education
    "online_courses", "seminars_conferences", "trade_certifications",
    "university_fees", "professional_development", "educational_materials",
    # health_medical
    "medical_consultations", "pharmacy", "dental_services", "optical_services",
    "physiotherapy", "pathology_imaging", "occupational_health",
    "mental_health_services",
    # insurance_finance
    "business_insurance", "professional_indemnity", "public_liability",
    "workers_compensation", "vehicle_insurance", "bank_fees_charges",
    "loan_repayments", "asset_management",
    # utilities_facilities
    "electricity", "gas_utilities", "water_rates", "waste_management",
    "cleaning_services", "pest_control", "security_services",
    # construction_engineering
    "building_materials", "concrete_masonry", "timber_framing", "roofing_materials",
    "plumbing_supplies", "electrical_supplies", "civil_engineering_materials",
    "subcontractor_services",
    # tools_equipment
    "hand_tools", "power_tools", "heavy_equipment_hire", "machinery_purchase",
    "testing_equipment", "workshop_supplies",
    # safety_compliance
    "personal_protective_equipment", "fire_safety_equipment", "first_aid_supplies",
    "whs_training", "compliance_audits",
    # retail_merchandise
    "electronics_appliances", "clothing_apparel", "sporting_goods", "hardware_retail",
    "automotive_parts", "furniture_fittings", "gifts_vouchers", "general_retail",
    # subscriptions_memberships
    "digital_subscriptions", "software_subscriptions", "industry_memberships",
    "gym_membership", "media_streaming",
    # government_official
    "government_fees_charges", "council_rates", "licenses_permits", "court_fees",
    "fines_penalties",
    # restricted_non_compliant
    "gambling_betting", "adult_entertainment", "casino", "personal_alcohol",
    "nightclubs_clubs", "lottery", "personal_shopping",
    # fallback
    "other",
]

_CATEGORY_INSTRUCTIONS = """
DOCUMENT-LEVEL CATEGORY — assign one category_group that best describes the overall document:
meals_dining, travel_accommodation, transport_vehicles, fuel_energy, office_stationery,
it_software, telecommunications, professional_services, marketing_advertising,
training_education, health_medical, insurance_finance, utilities_facilities,
construction_engineering, tools_equipment, safety_compliance, retail_merchandise,
subscriptions_memberships, government_official, restricted_non_compliant

LINE-LEVEL CATEGORY — assign one item_category (granular) to each line item:
meals_dining → restaurant, fast_food, coffee_shop, bar_pub_tavern, brewery, food_delivery, fresh_food_market, catering_services, convenience_store, meat_deli, staff_meals
travel_accommodation → airline_flights, hotel_accommodation, airbnb_short_stay, travel_agency, visa_fees, airport_transfers, cruise, travel_insurance, conference_accommodation
transport_vehicles → taxi_rideshare, car_rental, public_transport, parking_fees, toll_roads, vehicle_leasing, vehicle_maintenance, motor_registration, carwash
fuel_energy → petrol_diesel, lpg_gas, ev_charging, fuel_cards
office_stationery → office_supplies, stationery, printing_copying, postage_courier, bookstore, newsagent
it_software → software_licenses, it_hardware, cloud_services, web_hosting, domain_registration, it_support_services, cybersecurity
telecommunications → mobile_phone_plans, internet_broadband, landline_telephone, satellite_comms, conferencing_services
professional_services → accounting_bookkeeping, legal_services, management_consulting, engineering_consulting, architectural_services, recruitment_services, freelance_services, environmental_services
marketing_advertising → digital_advertising, print_advertising, social_media_marketing, pr_services, promotional_materials, events_sponsorship, photography_videography
training_education → online_courses, seminars_conferences, trade_certifications, university_fees, professional_development, educational_materials
health_medical → medical_consultations, pharmacy, dental_services, optical_services, physiotherapy, pathology_imaging, occupational_health, mental_health_services
insurance_finance → business_insurance, professional_indemnity, public_liability, workers_compensation, vehicle_insurance, bank_fees_charges, loan_repayments, asset_management
utilities_facilities → electricity, gas_utilities, water_rates, waste_management, cleaning_services, pest_control, security_services
construction_engineering → building_materials, concrete_masonry, timber_framing, roofing_materials, plumbing_supplies, electrical_supplies, civil_engineering_materials, subcontractor_services
tools_equipment → hand_tools, power_tools, heavy_equipment_hire, machinery_purchase, testing_equipment, workshop_supplies
safety_compliance → personal_protective_equipment, fire_safety_equipment, first_aid_supplies, whs_training, compliance_audits
retail_merchandise → electronics_appliances, clothing_apparel, sporting_goods, hardware_retail, automotive_parts, furniture_fittings, gifts_vouchers, general_retail
subscriptions_memberships → digital_subscriptions, software_subscriptions, industry_memberships, gym_membership, media_streaming
government_official → government_fees_charges, council_rates, licenses_permits, court_fees, fines_penalties
restricted_non_compliant → gambling_betting, adult_entertainment, casino, personal_alcohol, nightclubs_clubs, lottery, personal_shopping

GST EXEMPT FLAG — set gst_exempt: true on line items that are GST-free under Australian law:
- Basic unprocessed food: bread, milk, eggs, meat, fresh/frozen/canned fruit & vegetables, cooking oils, plain water, tea/coffee beans, baby food, infant formula
- Prescription medicines (PBS items)
- Medical, dental, optical, allied health services
- Approved education and training course fees
- Childcare services
- Council rates, government fees, court fees, vehicle registration, fines
- Residential rent, bank interest, insurance premiums (input-taxed)
- Water rates and sewerage charges
TAXABLE (gst_exempt: false): hot takeaway food, alcohol, soft drinks, confectionery, snack foods, restaurant meals, prepared/processed food, clothing, electronics, fuel, most retail goods.

Examples:
- "Flat white" → item_category: coffee_shop, gst_exempt: false
- "Full cream milk 2L" → item_category: fresh_food_market, gst_exempt: true
- "Panadol (prescription)" → item_category: pharmacy, gst_exempt: true
- "Unleaded 91 45L" → item_category: petrol_diesel, gst_exempt: false
- "Council rates Q1" → item_category: council_rates, gst_exempt: true
- "Woolworths groceries" → item_category: fresh_food_market, gst_exempt: true (if basic food)
"""

# Shared line item schema used by receipt and invoice
# category_group is at DOCUMENT level — line items use item_category (granular) only
_LINE_ITEM_SCHEMA = {
    "type": "object",
    "required": [
        "line_number", "line_description", "quantity", "unit_price",
        "line_amount", "gst_code", "gst_amount", "gst_exempt",
        "item_category", "notes"
    ],
    "additionalProperties": False,
    "properties": {
        "line_number":      {"type": "integer"},
        "line_description": {"type": "string"},
        "quantity":         {"type": ["number", "null"]},
        "unit_price":       {"type": ["number", "null"]},
        "line_amount":      {"type": "number"},
        "gst_code":         {"type": ["string", "null"]},   # Z, G, F, * or null
        "gst_amount":       {"type": ["number", "null"]},
        "gst_exempt":       {"type": "boolean"},
        "item_category":    {"type": "string", "enum": _COMPLIANCE_CATEGORIES},
        "notes":            {"type": ["string", "null"]},
    }
}

_GST_SUMMARY_SCHEMA = {
    "type": "object",
    "required": ["zero_rated_net", "taxable_net", "gst_total", "taxable_gross"],
    "additionalProperties": False,
    "properties": {
        "zero_rated_net":  {"type": ["number", "null"]},
        "taxable_net":     {"type": ["number", "null"]},
        "gst_total":       {"type": ["number", "null"]},
        "taxable_gross":   {"type": ["number", "null"]},
    }
}

# ---------------------------------------------------------------------------
# RECEIPT
# ---------------------------------------------------------------------------

RECEIPT_SYSTEM = f"""
You are an expert receipt and tax invoice parser for Australian businesses.

═══════════════════════════════════════════
GST EXTRACTION — READ THIS CAREFULLY
═══════════════════════════════════════════

STEP 1 — READ LINE-LEVEL GST CODES
Many Australian receipts print a single letter suffix after each line item amount:
  Z  = GST-free (zero rated). Set gst_exempt: true, gst_amount: 0.00
  G  = GST applies (10%). Set gst_exempt: false. Calculate gst_amount = line_amount / 11
  F  = GST-free (some retailers use F instead of Z). Same as Z.
  *  = GST applies (some retailers use asterisk). Same as G.

These codes appear directly on the receipt next to the price. Read them carefully.
Example: "FLUFFY FABRIC SOFT L eac   5.99 G" → gst_exempt: false, gst_amount: 0.54

STEP 2 — READ THE GST SUMMARY TABLE
Most Australian receipts print a GST breakdown table at the bottom, e.g.:
  GST%  Net.Amt   GST    Amount
  Z  0   22.26   0.00   22.26
  G  10   6.35   0.63    6.98

Extract this as gst_summary — it is the authoritative source of GST truth.
Fields: zero_rated_net, taxable_net, gst_total, taxable_gross
If no summary table is shown, set all gst_summary fields to null.

STEP 3 — CROSS-CHECK
The sum of all G-line gst_amounts must equal gst_summary.gst_total.
The document-level gst_amount must equal gst_summary.gst_total.

═══════════════════════════════════════════
DOCUMENT TYPE DETECTION
═══════════════════════════════════════════
Set document_subtype to one of:
- "receipt"       — standard point-of-sale receipt
- "hotel_folio"   — hotel/motel/accommodation bill showing charges + payment lines
- "tax_invoice"   — formal tax invoice with ABN, often from professional services
- "statement"     — periodic account statement

═══════════════════════════════════════════
TRANSACTION AMOUNT — CRITICAL RULE
═══════════════════════════════════════════
transaction_amount = the TOTAL VALUE OF GOODS AND SERVICES purchased.
It is NEVER the balance due or net balance.

For hotel folios and tax invoices:
- The document shows CHARGE LINES (accommodation, meals, parking) and PAYMENT LINES (Visa Card -$350, Cash -$200)
- transaction_amount = SUM OF CHARGE LINES ONLY (positive amounts)
- Do NOT subtract payments. The $0 balance means it was paid in full — not that nothing was spent.
- Example: 2 nights × $175 = $350 transaction_amount, even if balance due = $0

═══════════════════════════════════════════
PAYMENT LINES — KEEP SEPARATE FROM ITEMS
═══════════════════════════════════════════
Payment lines are records of how the bill was settled. They are NOT purchased items.
Identify payment lines by description keywords: "Visa Card", "Mastercard", "Amex", "Cash",
"EFTPOS", "Deposit", "Prepayment", "Pre-payment", "Payment Received", "Credit Card".

- Do NOT put payment lines in the items array.
- Capture them in payment_lines array instead.
- Use them to determine payment_method and card_last_four.

═══════════════════════════════════════════
OTHER RULES
═══════════════════════════════════════════
- Extract every field you can see. Do not guess values not visible.
- Payment method: EFTPOS, payWave, tap, Visa, Mastercard, Amex, credit, debit → "card". Cash → "cash". Default "card".
- items: only purchased goods/services. If none visible, create one using merchant name and transaction_amount.
- transaction_date: YYYY-MM-DD. If not visible return null.
- transaction_time: HH:MM. If not visible return null.
- surcharge_amount: card surcharge, service fee. Labels: "Surcharge", "Card Surcharge", "Service Fee", "Credit Card Fee". Null if absent.
- merchant_abn: format XX XXX XXX XXX.
- card_last_four: last 4 digits of card if shown.
- confidence: 0.0–1.0 reflecting extraction clarity.
- Return null for any field not found — never fabricate data.

{_CATEGORY_INSTRUCTIONS}
"""

RECEIPT_SCHEMA = {
    "type": "object",
    "required": [
        "document_subtype",
        "merchant_name", "merchant_abn", "merchant_address", "merchant_phone",
        "category_group",
        "transaction_amount", "subtotal_amount", "gst_amount", "discount_amount",
        "surcharge_amount", "transaction_date", "transaction_time", "receipt_number",
        "payment_method", "card_last_four", "loyalty_points",
        "confidence", "gst_summary", "payment_lines", "items"
    ],
    "additionalProperties": False,
    "properties": {
        "document_subtype":   {"type": "string", "enum": ["receipt", "hotel_folio", "tax_invoice", "statement"]},
        "merchant_name":      {"type": "string"},
        "category_group":     {"type": "string", "enum": _CATEGORY_GROUPS},
        "merchant_abn":       {"type": ["string", "null"]},
        "merchant_address":   {"type": ["string", "null"]},
        "merchant_phone":     {"type": ["string", "null"]},
        "transaction_amount": {"type": "number"},
        "subtotal_amount":    {"type": ["number", "null"]},
        "gst_amount":         {"type": ["number", "null"]},
        "discount_amount":    {"type": ["number", "null"]},
        "surcharge_amount":   {"type": ["number", "null"]},
        "transaction_date":   {"type": ["string", "null"]},
        "transaction_time":   {"type": ["string", "null"]},
        "receipt_number":     {"type": ["string", "null"]},
        "payment_method":     {"type": "string", "enum": ["card", "cash"]},
        "card_last_four":     {"type": ["string", "null"]},
        "loyalty_points":     {"type": ["string", "null"]},
        "confidence":         {"type": "number"},
        "gst_summary":        _GST_SUMMARY_SCHEMA,
        "payment_lines": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["description", "amount", "payment_method"],
                "additionalProperties": False,
                "properties": {
                    "description":    {"type": "string"},
                    "amount":         {"type": "number"},
                    "payment_method": {"type": "string", "enum": ["card", "cash"]},
                }
            }
        },
        "items":              {"type": "array", "items": _LINE_ITEM_SCHEMA},
    }
}

# ---------------------------------------------------------------------------
# INVOICE
# ---------------------------------------------------------------------------

INVOICE_SYSTEM = f"""
You are an expert tax invoice parser for Australian businesses.

VENDOR (SELLER) DETAILS — extract from the top/header of the invoice:
- vendor_name, vendor_abn, vendor_address, vendor_email, vendor_phone, vendor_website
- salesperson: name of the sales rep or account manager shown on the invoice

CUSTOMER (BUYER) DETAILS — extract the "Bill To" / "Sold To" section:
- customer_name, customer_abn, customer_address, customer_email, customer_phone

SHIPPING — extract the "Ship To" / "Deliver To" section if different from billing:
- ship_to_name, ship_to_address

INVOICE REFERENCES:
- invoice_number: the invoice number (e.g. INV-001, #12345)
- reference_number: any additional reference number shown (e.g. "Ref:", "Job #", "Work Order")
- po_reference: Purchase Order number (e.g. "PO:", "P.O. Number")
- order_date: date the order was placed (YYYY-MM-DD)
- invoice_date: date the invoice was issued (YYYY-MM-DD)
- due_date: payment due date (YYYY-MM-DD). Look for "Due Date", "Payment Due", "Please pay by".
- delivery_date: date goods/services were or will be delivered (YYYY-MM-DD)

PAYMENT TERMS:
- payment_terms: e.g. "Net 30", "Due on receipt", "2/10 Net 30", "COD"
- terms_of_sale: any additional sale conditions shown (e.g. "Ex Works", "FOB", "All sales final")

AMOUNTS — extract every amount field visible:
- subtotal_amount: pre-tax subtotal
- discount_amount: any discount applied
- freight_amount: shipping/freight/delivery charges
- gst_amount: GST / tax total. If not shown, infer as (invoice_total_amount / 11) rounded to 2dp.
- invoice_total_amount: the final total due

PAYMENT DETAILS:
- bank_bsb: BSB number (format: XXX-XXX)
- bank_account_number, bank_account_name
- bpay_biller_code: BPay biller code if shown
- bpay_reference: BPay reference number if shown

LINE ITEMS — extract every line item with:
- line_number, line_description, quantity, unit_price, line_amount
- gst_amount: GST for this specific line. If not shown per-line, infer as (line_amount / 11).
- category_group and item_category per the taxonomy below.

RULES:
- All dates: YYYY-MM-DD format.
- All ABNs: XX XXX XXX XXX format.
- confidence: 0.0–1.0 reflecting overall extraction clarity.
- Return null for any field not found — never fabricate data.

{_CATEGORY_INSTRUCTIONS}
"""

INVOICE_SCHEMA = {
    "type": "object",
    "required": [
        # Document-level category
        "category_group",
        # Vendor
        "vendor_name", "vendor_abn", "vendor_address", "vendor_email",
        "vendor_phone", "vendor_website", "salesperson",
        # Customer
        "customer_name", "customer_abn", "customer_address",
        "customer_email", "customer_phone",
        # Ship to
        "ship_to_name", "ship_to_address",
        # References
        "invoice_number", "reference_number", "po_reference",
        "order_date", "invoice_date", "due_date", "delivery_date",
        # Terms
        "payment_terms", "terms_of_sale",
        # Amounts
        "subtotal_amount", "discount_amount", "freight_amount",
        "gst_amount", "invoice_total_amount",
        # Payment details
        "bank_bsb", "bank_account_number", "bank_account_name",
        "bpay_biller_code", "bpay_reference",
        # Meta
        "confidence", "items"
    ],
    "additionalProperties": False,
    "properties": {
        # Document-level category
        "category_group":       {"type": "string", "enum": _CATEGORY_GROUPS},
        # Vendor
        "vendor_name":          {"type": "string"},
        "vendor_abn":           {"type": ["string", "null"]},
        "vendor_address":       {"type": ["string", "null"]},
        "vendor_email":         {"type": ["string", "null"]},
        "vendor_phone":         {"type": ["string", "null"]},
        "vendor_website":       {"type": ["string", "null"]},
        "salesperson":          {"type": ["string", "null"]},
        # Customer
        "customer_name":        {"type": ["string", "null"]},
        "customer_abn":         {"type": ["string", "null"]},
        "customer_address":     {"type": ["string", "null"]},
        "customer_email":       {"type": ["string", "null"]},
        "customer_phone":       {"type": ["string", "null"]},
        # Ship to
        "ship_to_name":         {"type": ["string", "null"]},
        "ship_to_address":      {"type": ["string", "null"]},
        # References
        "invoice_number":       {"type": "string"},
        "reference_number":     {"type": ["string", "null"]},
        "po_reference":         {"type": ["string", "null"]},
        "order_date":           {"type": ["string", "null"]},
        "invoice_date":         {"type": "string"},
        "due_date":             {"type": ["string", "null"]},
        "delivery_date":        {"type": ["string", "null"]},
        # Terms
        "payment_terms":        {"type": ["string", "null"]},
        "terms_of_sale":        {"type": ["string", "null"]},
        # Amounts
        "subtotal_amount":      {"type": ["number", "null"]},
        "discount_amount":      {"type": ["number", "null"]},
        "freight_amount":       {"type": ["number", "null"]},
        "gst_amount":           {"type": ["number", "null"]},
        "invoice_total_amount": {"type": "number"},
        # Payment details
        "bank_bsb":             {"type": ["string", "null"]},
        "bank_account_number":  {"type": ["string", "null"]},
        "bank_account_name":    {"type": ["string", "null"]},
        "bpay_biller_code":     {"type": ["string", "null"]},
        "bpay_reference":       {"type": ["string", "null"]},
        # Meta
        "confidence":           {"type": "number"},
        "items":                {"type": "array", "items": _LINE_ITEM_SCHEMA},
    }
}

# ---------------------------------------------------------------------------
# BANK / CREDIT CARD STATEMENT
# ---------------------------------------------------------------------------

STATEMENT_SYSTEM = f"""
You are an expert bank and credit card statement parser for Australian businesses.

Rules:
- Extract every transaction line visible on the statement.
- type: "debit" for money going out, "credit" for money coming in.
- All dates: format as YYYY-MM-DD.
- amounts: always positive numbers regardless of direction.
- account_number: mask all but last 4 digits if partially shown.
- confidence: 0.0–1.0 reflecting extraction clarity.
- Return null for any field not found.

{_CATEGORY_INSTRUCTIONS}

Apply category_group and category to every transaction line based on the merchant name and description.
Examples:
- "MCDONALD'S PARRAMATTA" → category_group: meals_dining, category: fast_food
- "BP FUEL PENRITH" → category_group: fuel_energy, category: petrol_diesel
- "UBER *TRIP" → category_group: transport_vehicles, category: taxi_rideshare
- "WILSON PARKING" → category_group: transport_vehicles, category: parking_fees
- "OFFICEWORKS" → category_group: office_stationery, category: office_supplies
- "NETFLIX.COM" → category_group: subscriptions_memberships, category: media_streaming
- "AGL ENERGY" → category_group: utilities_facilities, category: electricity
- "BUNNINGS WAREHOUSE" → category_group: tools_equipment, category: hand_tools
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
        "account_holder":         {"type": "string"},
        "bank_name":              {"type": ["string", "null"]},
        "account_number":         {"type": ["string", "null"]},
        "account_type":           {"type": ["string", "null"]},
        "statement_period_start": {"type": ["string", "null"]},
        "statement_period_end":   {"type": ["string", "null"]},
        "opening_balance":        {"type": ["number", "null"]},
        "closing_balance":        {"type": ["number", "null"]},
        "total_debits":           {"type": ["number", "null"]},
        "total_credits":          {"type": ["number", "null"]},
        "confidence":             {"type": "number"},
        "transactions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "date", "description", "amount", "type",
                    "balance", "reference", "category_group", "category"
                ],
                "additionalProperties": False,
                "properties": {
                    "date":           {"type": "string"},
                    "description":    {"type": "string"},
                    "amount":         {"type": "number"},
                    "type":           {"type": "string", "enum": ["debit", "credit"]},
                    "balance":        {"type": ["number", "null"]},
                    "reference":      {"type": ["string", "null"]},
                    "category_group": {"type": "string", "enum": _CATEGORY_GROUPS},
                    "category":       {"type": "string", "enum": _COMPLIANCE_CATEGORIES},
                }
            }
        }
    }
}

# ---------------------------------------------------------------------------
# EMAIL
# ---------------------------------------------------------------------------

EMAIL_SYSTEM = """
You are an expert email analyst for a business expense and task management system.

Your job is to fully analyse an email and extract everything needed to:
1. Categorise it correctly
2. Summarise it clearly
3. Identify any required action and its due date
4. Extract all financial details
5. Identify attachments and what they likely contain

CATEGORISATION — assign exactly one category from this list:
Financial: invoice, receipt, statement, purchase_order, expense_claim, payment_reminder, refund, quote, contract, tax_document
HR: leave_request, payslip, timesheet, onboarding, policy_update, performance_review
IT: password_reset, security_alert, system_notification, software_license
Sales: inquiry, feedback, shipping_notification, subscription
Communication: meeting_request, newsletter, announcement, auto_reply
Other: marketing, spam, support_ticket, compliance_alert, general

SUMMARY — write 2-3 sentences max. Include: who sent it, what it is about, what action is needed.

ACTION ITEMS — extract any tasks or required responses. Examples:
- "Pay invoice #INV-001 by 2025-05-01"
- "Approve leave request for John Smith"
- "Respond to quote by end of week"
- "Review and sign attached contract"

PRIORITY — assign based on urgency and financial impact:
- "urgent": overdue, security alerts, same-day deadlines
- "high": due within 7 days, large amounts (>$1000)
- "medium": due within 30 days, moderate amounts
- "low": newsletters, announcements, no action needed

ATTACHMENTS — list every attachment mentioned or implied in the email. Infer the likely type from filename and context.

RULES:
- All dates: YYYY-MM-DD format.
- All amounts: positive numbers.
- currency: ISO 4217 (e.g. "AUD", "USD"). Default "AUD" if Australian context.
- due_date: the most important deadline in the email (payment due, response deadline, meeting date).
- confidence: 0.0–1.0 reflecting how clearly the email content supports your extraction.
- Return null for any field not visible or inferable.
"""

EMAIL_SCHEMA = {
    "type": "object",
    "required": [
        "email_subject", "sender_name", "sender_email", "date_sent",
        "to_recipients", "cc_recipients",
        "category", "summary", "priority",
        "requires_action", "action_description", "due_date",
        "merchant_name", "reference_number",
        "total_amount", "gst_amount", "currency",
        "key_dates", "key_people", "key_amounts",
        "attachments", "line_items", "confidence"
    ],
    "additionalProperties": False,
    "properties": {
        "email_subject":   {"type": ["string", "null"]},
        "sender_name":     {"type": ["string", "null"]},
        "sender_email":    {"type": ["string", "null"]},
        "date_sent":       {"type": ["string", "null"]},
        "to_recipients":   {"type": ["array", "null"], "items": {"type": "string"}},
        "cc_recipients":   {"type": ["array", "null"], "items": {"type": "string"}},
        "category": {
            "type": "string",
            "enum": [
                "invoice", "receipt", "statement", "purchase_order", "expense_claim",
                "payment_reminder", "refund", "quote", "contract", "tax_document",
                "leave_request", "payslip", "timesheet", "onboarding", "policy_update",
                "performance_review", "password_reset", "security_alert",
                "system_notification", "software_license", "inquiry", "feedback",
                "shipping_notification", "subscription", "meeting_request",
                "newsletter", "announcement", "auto_reply",
                "marketing", "spam", "support_ticket", "compliance_alert", "general"
            ]
        },
        "summary":  {"type": "string"},
        "priority": {"type": "string", "enum": ["urgent", "high", "medium", "low"]},
        "requires_action":    {"type": "boolean"},
        "action_description": {"type": ["string", "null"]},
        "due_date":           {"type": ["string", "null"]},
        "merchant_name":      {"type": ["string", "null"]},
        "reference_number":   {"type": ["string", "null"]},
        "total_amount":       {"type": ["number", "null"]},
        "gst_amount":         {"type": ["number", "null"]},
        "currency":           {"type": ["string", "null"]},
        "key_dates": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["date", "context"],
                "additionalProperties": False,
                "properties": {
                    "date":    {"type": "string"},
                    "context": {"type": "string"},
                }
            }
        },
        "key_people": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "role"],
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": ["string", "null"]},
                }
            }
        },
        "key_amounts": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["amount", "context"],
                "additionalProperties": False,
                "properties": {
                    "amount":  {"type": "number"},
                    "context": {"type": "string"},
                }
            }
        },
        "attachments": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["filename", "inferred_type", "notes"],
                "additionalProperties": False,
                "properties": {
                    "filename":      {"type": "string"},
                    "inferred_type": {
                        "type": "string",
                        "enum": ["invoice", "receipt", "statement", "contract",
                                 "purchase_order", "payslip", "report", "image", "other"]
                    },
                    "notes": {"type": ["string", "null"]},
                }
            }
        },
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
        },
        "confidence": {"type": "number"},
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
