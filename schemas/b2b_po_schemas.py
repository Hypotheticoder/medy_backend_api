from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class B2BOrderCheckout(BaseModel):
    payment_terms: str # "prepaid", "net_15", "cod"
    delivery_notes: Optional[str] = None

class B2BPurchaseOrderResponse(BaseModel):
    po_id: str
    shop_id: str
    distributor_id: str
    subtotal: float
    cgst_amount: float
    sgst_amount: float
    total_invoice_amount: float
    payment_terms: str
    po_status: str
    created_at: datetime

    class Config:
        from_attributes = True
