from pydantic import BaseModel, Field
from typing import Optional, List, Any


class PaymentLine(BaseModel):
    description: str
    amount: float
    payment_method: str


class GstSummary(BaseModel):
    zero_rated_net: Optional[float] = None   # Z/F items net total
    taxable_net: Optional[float] = None      # G items net total (ex-GST)
    gst_total: Optional[float] = None        # Total GST charged
    taxable_gross: Optional[float] = None    # G items gross total (inc-GST)


class LineItem(BaseModel):
    line_number: int
    line_description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    line_amount: float
    gst_code: Optional[str] = None           # Z, G, F, * as printed on receipt
    gst_amount: Optional[float] = None
    gst_exempt: bool = False
    item_category: Optional[str] = None
    notes: Optional[str] = None


class ReceiptExtraction(BaseModel):
    # Document type
    document_subtype: Optional[str] = None  # receipt, hotel_folio, tax_invoice, statement

    # Document-level category
    category_group: Optional[str] = None

    # Core fields
    merchant_name: str
    merchant_abn: Optional[str] = None
    merchant_address: Optional[str] = None
    merchant_phone: Optional[str] = None

    # Amounts
    transaction_amount: float
    subtotal_amount: Optional[float] = None
    gst_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    surcharge_amount: Optional[float] = None

    # Transaction details
    transaction_date: str
    transaction_time: Optional[str] = None
    receipt_number: Optional[str] = None
    payment_method: str = "card"
    card_last_four: Optional[str] = None
    loyalty_points: Optional[str] = None

    # GST summary table from receipt
    gst_summary: Optional[GstSummary] = None

    # Payment records (hotel folios, tax invoices — separated from charge items)
    payment_lines: Optional[List[PaymentLine]] = None

    # Line items (charges only, no payment lines)
    items: List[LineItem]

    # Metadata
    ocr_confidence: float
    receipt_status: int = Field(default=2, description="2 = AI Processed")
    is_manually_entered: bool = False

    # Validation
    items_total_matches: bool
    items_total_difference: Optional[float] = None


class ReceiptResponse(BaseModel):
    success: bool
    receipt_data: Optional[ReceiptExtraction] = None
    raw_data: Optional[dict] = None
    validation_warnings: Optional[List[str]] = None
    error: Optional[str] = None


class EmailAttachment(BaseModel):
    filename: str
    inferred_type: str
    notes: Optional[str] = None


class EmailKeyDate(BaseModel):
    date: str
    context: str


class EmailKeyPerson(BaseModel):
    name: str
    role: Optional[str] = None


class EmailKeyAmount(BaseModel):
    amount: float
    context: str


class EmailLineItem(BaseModel):
    description: str
    amount: Optional[float] = None
    quantity: Optional[float] = None
    notes: Optional[str] = None


class EmailExtraction(BaseModel):
    # Metadata
    email_subject: Optional[str] = None
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None
    date_sent: Optional[str] = None
    to_recipients: Optional[List[str]] = None
    cc_recipients: Optional[List[str]] = None

    # Classification
    category: str
    summary: str
    priority: str

    # Action item — drives the dashboard
    requires_action: bool
    action_description: Optional[str] = None
    due_date: Optional[str] = None

    # Financial
    merchant_name: Optional[str] = None
    reference_number: Optional[str] = None
    total_amount: Optional[float] = None
    gst_amount: Optional[float] = None
    currency: Optional[str] = None

    # Entities
    key_dates: List[EmailKeyDate] = []
    key_people: List[EmailKeyPerson] = []
    key_amounts: List[EmailKeyAmount] = []

    # Attachments & line items
    attachments: List[EmailAttachment] = []
    line_items: List[EmailLineItem] = []

    confidence: float


class EmailResponse(BaseModel):
    success: bool
    email_data: Optional[EmailExtraction] = None
    raw_data: Optional[dict] = None
    error: Optional[str] = None


class InvoiceExtraction(BaseModel):
    # Document-level category
    category_group: Optional[str] = None

    # Vendor
    vendor_name: str
    vendor_abn: Optional[str] = None
    vendor_address: Optional[str] = None
    vendor_email: Optional[str] = None
    vendor_phone: Optional[str] = None
    vendor_website: Optional[str] = None
    salesperson: Optional[str] = None

    # Customer (Bill To / Sold To)
    customer_name: Optional[str] = None
    customer_abn: Optional[str] = None
    customer_address: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None

    # Ship To
    ship_to_name: Optional[str] = None
    ship_to_address: Optional[str] = None

    # References
    invoice_number: str
    reference_number: Optional[str] = None
    po_reference: Optional[str] = None
    order_date: Optional[str] = None
    invoice_date: str
    due_date: Optional[str] = None
    delivery_date: Optional[str] = None

    # Terms
    payment_terms: Optional[str] = None
    terms_of_sale: Optional[str] = None

    # Amounts
    subtotal_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    freight_amount: Optional[float] = None
    gst_amount: Optional[float] = None
    invoice_total_amount: float

    # Payment details
    bank_bsb: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_name: Optional[str] = None
    bpay_biller_code: Optional[str] = None
    bpay_reference: Optional[str] = None

    # Line items
    items: List[LineItem]

    # Metadata
    confidence: float
    invoice_status: int = Field(default=2, description="2 = AI Processed")
    is_manually_entered: bool = False


class InvoiceResponse(BaseModel):
    success: bool
    invoice_data: Optional[InvoiceExtraction] = None
    raw_data: Optional[dict] = None
    validation_warnings: Optional[List[str]] = None
    error: Optional[str] = None


class DocumentResponse(BaseModel):
    """Generic response for statement document type."""
    success: bool
    document_type: str
    data: Optional[Any] = None
    validation_warnings: Optional[List[str]] = None
    error: Optional[str] = None
