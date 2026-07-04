import strawberry
from typing import List, Optional
from strawberry.types import Info

# 🚨 Notice the updated import here! 🚨
from graphql_api.types import MedicineType, OrderType, PharmaShopType

from models.medicine import Medicine
from models.order import Order
from models.pharma_shop import PharmaShopUser

@strawberry.type
class Query:
    
    @strawberry.field
    def search_medicines(
        self, 
        info: Info, 
        query: Optional[str] = None, 
        category: Optional[str] = None, # 🚨 Added category filter
        limit: int = 20, 
        offset: int = 0                 # 🚨 Added offset for Infinite Scrolling
    ) -> List[MedicineType]:
        
        db = info.context["db"]
        db_query = db.query(Medicine)
        
        # 1. Search by name if provided
        if query:
            db_query = db_query.filter(Medicine.medicine_name.ilike(f"%{query}%"))
            
        # 2. Filter by category if provided (e.g., "Pain Relief")
        if category:
            db_query = db_query.filter(Medicine.medicine_category == category)
            
        # 3. Apply Offset and Limit for Pagination
        return db_query.offset(offset).limit(limit).all()

    @strawberry.field
    def get_my_order_history(self, info: Info, customer_id: str, limit: int = 10) -> List[OrderType]:
        db = info.context["db"]
        return db.query(Order).filter(Order.customer_id == customer_id).order_by(Order.created_at.desc()).limit(limit).all()

    @strawberry.field
    def get_medicine_by_id(self, info: Info, medicine_id: str) -> Optional[MedicineType]:
        db = info.context["db"]
        return db.query(Medicine).filter(Medicine.medicine_id == medicine_id).first()
