from pydantic import BaseModel, Field
from typing import Optional, List, Any


class LineItem(BaseModel):
    line_number: int
    line_description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    line_amount: float
    gst_amount: Optional[float] = None
    item_category: Optional[str] = None
    notes: Optional[str] = None


class ReceiptExtraction(BaseModel):
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

    # Line items
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


class DocumentResponse(BaseModel):
    """Generic response for non-receipt document types (invoice, statement, email)."""
    success: bool
    document_type: str
    data: Optional[Any] = None
    validation_warnings: Optional[List[str]] = None
    error: Optional[str] = None
