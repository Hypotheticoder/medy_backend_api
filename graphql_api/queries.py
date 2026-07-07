import strawberry
from typing import List, Optional
from strawberry.types import Info

from graphql_api.types import MedicineType, OrderType, PharmaShopType, CartType

from models.medicine import Medicine
from models.order import Order
from models.pharma_shop import PharmaShopUser
from models.cart import Cart

@strawberry.type
class Query:
    
    @strawberry.field
    def search_medicines(
        self, 
        info: Info, 
        query: Optional[str] = None, 
        category: Optional[str] = None,
        limit: int = 20, 
        offset: int = 0
    ) -> List[MedicineType]:
        """
        Allows the Flutter app to search the global catalog by name or category.
        Usage: query { searchMedicines(query: "Dolo", limit: 10) { medicineName mrp } }
        """
        db = info.context["db"]
        db_query = db.query(Medicine)
        
        if query:
            # Case-insensitive search using ILIKE
            db_query = db_query.filter(Medicine.medicine_name.ilike(f"%{query}%"))
        
        if category:
            db_query = db_query.filter(Medicine.medicine_category == category)
            
        return db_query.offset(offset).limit(limit).all()

    @strawberry.field
    def get_my_order_history(self, info: Info, customer_id: str, limit: int = 10) -> List[OrderType]:
        """
        Fetches the order history for a specific customer.
        """
        db = info.context["db"]
        return db.query(Order).filter(Order.customer_id == customer_id).order_by(Order.created_at.desc()).limit(limit).all()

    @strawberry.field
    def get_medicine_by_id(self, info: Info, medicine_id: str) -> Optional[MedicineType]:
        db = info.context["db"]
        return db.query(Medicine).filter(Medicine.medicine_id == medicine_id).first()

    @strawberry.field
    def get_shop_profile(self, info: Info, shop_id: str) -> Optional[PharmaShopType]:
        """
        Allows the customer to click on a bidding pharmacy and see their profile/rating.
        """
        db = info.context["db"]
        return db.query(PharmaShopUser).filter(PharmaShopUser.shop_id == shop_id).first()

    @strawberry.field
    def get_active_shops_nearby(self, info: Info, lat: float, lng: float) -> List[PharmaShopType]:
        """
        Fetches shops to show on the map (Basic implementation).
        In production, you'd use PostGIS (ST_Distance) here.
        """
        db = info.context["db"]
        # Basic filter returning highly rated verified shops that are online
        return db.query(PharmaShopUser).filter(
            PharmaShopUser.is_verified == True,
            PharmaShopUser.is_accepting_orders == True
        ).order_by(PharmaShopUser.rating.desc()).limit(10).all()

    @strawberry.field
    def get_my_cart(self, info: Info, customer_id: str) -> CartType:
        """
        Fetches the customer's cart for the UI Badge or Cart Screen.
        """
        db = info.context["db"]
        cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
        
        if not cart:
            # Ghost cart generation: If they don't have a cart, return an empty one
            # so the Flutter app doesn't crash with a Null error.
            return CartType(
                cart_id="empty",
                customer_id=customer_id,
                items=[],
                total_price=0.0,
                updated_at=None
            )
        return cart
