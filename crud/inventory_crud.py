from sqlalchemy.orm import Session
from models.distributor_inventory import DistributorInventory
from schemas.distributor_inventory import InventoryCreate

def add_single_inventory(db: Session, distributor_id: str, inventory: InventoryCreate):
    db_inventory = DistributorInventory(
        distributor_id=distributor_id,
        **inventory.model_dump()
    )
    db.add(db_inventory)
    db.commit()
    db.refresh(db_inventory)
    return db_inventory

def get_distributors_selling_medicine(db: Session, medicine_id: str):
    """
    Fetches all active distributors selling a specific medicine.
    (PostGIS distance filtering will be added here later).
    """
    return db.query(DistributorInventory).filter(
        DistributorInventory.medicine_id == medicine_id,
        DistributorInventory.is_active == True,
        DistributorInventory.available_stock_boxes > 0
    ).order_by(DistributorInventory.ptr.asc()).all() # Sorts by best wholesale price
