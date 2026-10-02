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
                medicine_id=item.get("medicine_id", "unknown_medicine"),
                batch_number=item.get("batch_number", "N/A"),
                qty_boxes=item.get("qty_boxes", 0),
                ptr=item.get("ptr", 0.0)
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
class B2BCartItemType:
    inventory_id: str
    qty_boxes: int
    ptr: float
    gst_percentage: float

    @strawberry.field
    def medicine_name(self, info: strawberry.Info) -> str:
        db = info.context["db"]
        from models.distributor_inventory import DistributorInventory
        from models.medicine import Medicine
        inv = db.query(DistributorInventory).filter(DistributorInventory.inventory_id == self.inventory_id).first()
        if inv:
            med = db.query(Medicine).filter(Medicine.medicine_id == inv.medicine_id).first()
            if med:
                return med.medicine_name
        return "Unknown Medicine"

    @strawberry.field
    def moq(self, info: strawberry.Info) -> int:
        db = info.context["db"]
        from models.distributor_inventory import DistributorInventory
        inv = db.query(DistributorInventory).filter(DistributorInventory.inventory_id == self.inventory_id).first()
        return inv.moq if inv else 1


@strawberry.type
class B2BCartResponseType:
    cart_id: str
    active_distributor_id: Optional[str]
    total_estimated_price: float
    items_json: strawberry.Private[list]
    
    @strawberry.field
    def items(self) -> List[B2BCartItemType]:
        if not self.items_json:
            return []
        return [
            B2BCartItemType(
                inventory_id=item.get("inventory_id", ""),
                qty_boxes=item.get("qty_boxes", 0),
                ptr=item.get("ptr", 0.0),
                gst_percentage=item.get("gst_percentage", 12.0)
            )
            for item in self.items_json
        ]


@strawberry.type
class NearbyDistributorType:
    distributor_id: str
    company_name: str
    phone: str
    address: str
    distance_km: float

@strawberry.type
class B2BRazorpayOrderType:
    razorpay_order_id: str
    amount_in_paise: int
    currency: str
    key_id: str
