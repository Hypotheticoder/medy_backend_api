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
    receiver_phone: str
    delivery_address: str
    is_emergency: bool
    caby_order_id: Optional[str]
    items: JSON
    item_total: float
    platform_fee: float
    delivery_fee: float
    taxes: float
    total_bill_amount: float
    payment_mode: str
    payment_status: str
    order_status: str
    rider_name: Optional[str]
    rider_phone: Optional[str]
    vehicle_number: Optional[str]
    vehicle_model: Optional[str]
    pickup_otp: Optional[str]
    drop_otp: Optional[str]
    transaction_id: Optional[str]
    created_at: datetime
    accepted_at: Optional[datetime]
    delivered_at: Optional[datetime]
