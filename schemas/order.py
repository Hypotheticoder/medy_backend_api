from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class OrderBase(BaseModel):
    customer_id: str
    shop_id: Optional[str] = None
    order_type: str = "cart"
    prescription_url: Optional[str] = None
    receiver_name: str
    receiver_phone: str
    delivery_address: str
    delivery_lat: float
    delivery_lng: float
    is_emergency: bool = False
    delivery_instructions: Optional[str] = None
    caby_order_id: Optional[str] = None
    distance_km: Optional[float] = None
    items: List[Any] = []
    item_total: float = 0.0
    platform_fee: float = 0.0
    delivery_fee: float = 0.0
    taxes: float = 0.0
    total_bill_amount: float = 0.0
    payment_mode: str
    payment_status: str = "pending"
    transaction_id: Optional[str] = None
    order_status: str = "bidding"
    rider_id: Optional[str] = None
    rider_name: Optional[str] = None
    rider_phone: Optional[str] = None
    rider_lat: Optional[float] = None
    rider_lng: Optional[float] = None
    vehicle_number: Optional[str] = None
    vehicle_model: Optional[str] = None
    pickup_otp: Optional[str] = None
    drop_otp: Optional[str] = None

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    shop_id: Optional[str] = None
    order_type: Optional[str] = None
    prescription_url: Optional[str] = None
    receiver_name: Optional[str] = None
    receiver_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_lat: Optional[float] = None
    delivery_lng: Optional[float] = None
    is_emergency: Optional[bool] = None
    delivery_instructions: Optional[str] = None
    caby_order_id: Optional[str] = None
    distance_km: Optional[float] = None
    items: Optional[List[Any]] = None
    item_total: Optional[float] = None
    platform_fee: Optional[float] = None
    delivery_fee: Optional[float] = None
    taxes: Optional[float] = None
    total_bill_amount: Optional[float] = None
    payment_mode: Optional[str] = None
    payment_status: Optional[str] = None
    transaction_id: Optional[str] = None
    order_status: Optional[str] = None
    rider_id: Optional[str] = None
    rider_name: Optional[str] = None
    rider_phone: Optional[str] = None
    rider_lat: Optional[float] = None
    rider_lng: Optional[float] = None
    vehicle_number: Optional[str] = None
    vehicle_model: Optional[str] = None
    pickup_otp: Optional[str] = None
    drop_otp: Optional[str] = None
    accepted_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

class OrderResponse(OrderBase):
    order_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    class Config:
        from_attributes = True
