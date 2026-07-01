import strawberry
from typing import Optional
from datetime import datetime
from strawberry.scalars import JSON

@strawberry.type
class OrderType:
    """GraphQL representation of a Customer's Order."""
    order_id: str
    customer_id: str
    shop_id: Optional[str]
    order_type: str
    prescription_url: Optional[str]
    receiver_name: str
    delivery_address: str
    is_emergency: bool
    caby_order_id: Optional[str]
    items: JSON
    item_total: float
    delivery_fee: float
    total_bill_amount: float
    payment_mode: str
    payment_status: str
    order_status: str
    created_at: datetime
