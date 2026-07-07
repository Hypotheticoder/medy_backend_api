import strawberry
from typing import Optional
from datetime import datetime
from strawberry.scalars import JSON

@strawberry.type
class CartType:
    """GraphQL representation of a Customer's Shopping Cart."""
    cart_id: str
    customer_id: str
    items: JSON
    total_price: float
    updated_at: Optional[datetime]
