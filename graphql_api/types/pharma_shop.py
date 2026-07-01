import strawberry
from typing import Optional

@strawberry.type
class PharmaShopType:
    """GraphQL representation of a Pharmacy Shop (Safe fields only, no passwords!)."""
    shop_id: str
    shop_name: str
    owner_name: str
    shop_image: Optional[str]
    address: str
    latitude: float
    longitude: float
    is_verified: bool
    is_accepting_orders: bool
    rating: float
