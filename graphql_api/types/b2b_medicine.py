import strawberry
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.distributor_inventory import DistributorInventory
from models.distributor import DistributorUser

@strawberry.type
class DistributorStockType:
    inventory_id: str
    distributor_id: str
    company_name: str
    batch_number: str
    ptr: float
    mrp: float
    available_stock_boxes: int
    moq: int

def get_available_sellers(root: "B2BMedicineType", info: strawberry.Info) -> List[DistributorStockType]:
    db: Session = info.context["db"]
    search_lat = info.context.get("search_lat")
    search_lng = info.context.get("search_lng")
    
    query = db.query(DistributorInventory, DistributorUser.company_name).join(
        DistributorUser, DistributorInventory.distributor_id == DistributorUser.distributor_id
    ).filter(
        DistributorInventory.medicine_id == root.medicine_id,
        DistributorInventory.is_active == True,
        DistributorInventory.available_stock_boxes > 0
    )

    if search_lat is not None and search_lng is not None:
        distance = (
            6371 * func.acos(
                func.cos(func.radians(search_lat)) * func.cos(func.radians(DistributorUser.latitude)) *
                func.cos(func.radians(DistributorUser.longitude) - func.radians(search_lng)) +
                func.sin(func.radians(search_lat)) * func.sin(func.radians(DistributorUser.latitude))
            )
        )
        query = query.filter(distance <= 20.0).order_by(distance.asc())

    results = query.all()

    return [
        DistributorStockType(
            inventory_id=inv.inventory_id,
            distributor_id=inv.distributor_id,
            company_name=company_name,
            batch_number=inv.batch_number,
            ptr=inv.ptr,
            mrp=inv.mrp,
            available_stock_boxes=inv.available_stock_boxes,
            moq=inv.moq
        )
        for inv, company_name in results
    ]

@strawberry.type
class B2BMedicineType:
    medicine_id: str
    medicine_name: str
    pack_size: str
    manufacturer: Optional[str]
    available_sellers: List[DistributorStockType] = strawberry.field(resolver=get_available_sellers)
