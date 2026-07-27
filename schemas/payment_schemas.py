from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ==========================================
# 1. REQUEST SCHEMAS (From Flutter to Backend)
# ==========================================
class RazorpayOrderCreate(BaseModel):
    """JSON body sent by Flutter to initiate a payment."""
    amount: float = Field(..., description="Amount in Rupees (e.g., 500.00)")
    internal_receipt_id: str = Field(..., description="Your DB ID (e.g., LAB-BKG-123)")

class RazorpayVerifyRequest(BaseModel):
    """JSON body sent by Flutter after the user enters their UPI PIN."""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

# ==========================================
# 2. RESPONSE SCHEMAS (From Backend to Flutter/Admin)
# ==========================================
class RazorpayOrderResponse(BaseModel):
    status: str
    razorpay_order_id: str
    amount: float
    currency: str = "INR"
    key_id: str

class PaymentTransactionResponse(BaseModel):
    """Used if you want to show payment history in an Admin Dashboard."""
    transaction_id: str
    order_id: str
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    amount: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
