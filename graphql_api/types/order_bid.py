import strawberry
from typing import Optional
from datetime import datetime
from strawberry.scalars import JSON

@strawberry.type
class OrderBidType:
    """GraphQL representation of a Shop's Bid."""
    bid_id: str
    order_id: str
    shop_id: str
    bid_type: str
    bid_status: str
    proposed_items: JSON
    total_bid_price: float
    estimated_ready_time_mins: Optional[float]
    created_at: datetime
