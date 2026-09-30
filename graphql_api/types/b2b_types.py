import strawberry
from typing import List, Optional
import json
from sqlalchemy.orm import Session

from models.b2b_purchase_order import B2BPurchaseOrder
from models.distributor import DistributorUser

@strawberry.type
class DistributorCatalogItemType:
    inventory_id: str
    medicine_id: str
    medicine_name: str
    pack_size: str
    manufacturer: Optional[str]
    batch_number: str
    ptr: float
    mrp: float
    available_stock_boxes: int
    moq: int

@strawberry.type
class B2BOrderItemType:
    medicine_id: str
    batch_number: str
    qty_boxes: int
    ptr: float

@strawberry.type
class DistributorSummaryType:
    distributor_id: str
    company_name: str
    phone: str

@strawberry.type
class B2BPurchaseOrderType:
    po_id: str
    subtotal: float
    total_invoice_amount: float
    po_status: str
    payment_terms: str
    created_at: str
    
    # Store raw JSON and distributor ID internally so resolvers can use them
    items_json: strawberry.Private[list]
    distributor_id: strawberry.Private[str]
    
    # Resolving the JSON column into a GraphQL list
    @strawberry.field
    def items(self) -> List[B2BOrderItemType]:
        return [
            B2BOrderItemType(
                medicine_id=item["medicine_id"],
                batch_number=item["batch_number"],
                qty_boxes=item["qty_boxes"],
                ptr=item["ptr"]
            )
            for item in self.items_json
        ]
    
    # Resolving the Distributor details dynamically
    @strawberry.field
    def distributor(self, info: strawberry.Info) -> DistributorSummaryType:
        db: Session = info.context["db"]
        dist = db.query(DistributorUser).filter(DistributorUser.distributor_id == self.distributor_id).first()
        return DistributorSummaryType(
            distributor_id=dist.distributor_id,
            company_name=dist.company_name,
            phone=dist.phone
        )

@strawberry.type
class B2BCartResponseType:
    cart_id: str
    active_distributor_id: Optional[str]
    total_estimated_price: float
