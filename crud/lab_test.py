from sqlalchemy.orm import Session
from models.lab_test import LabTest, generate_test_id
from models.lab_test_pricing import LabTestPricing
from schemas.lab_test_schemas import LabTestCreate, LabTestPricingCreate
import uuid

def create_global_test(db: Session, test_data: LabTestCreate) -> LabTest:
    """Admin adds a new test to the global dictionary."""
    db_test = LabTest(
        test_id=generate_test_id(),
        **test_data.model_dump()
    )
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    return db_test

def add_pricing_for_lab(db: Session, lab_id: str, pricing_data: LabTestPricingCreate) -> LabTestPricing:
    """A Patholab adds a test to their inventory and sets their price."""
    # Save it to the Bridge Table
    db_pricing = LabTestPricing(
        id=uuid.uuid4().hex,
        lab_id=lab_id,
        **pricing_data.model_dump()
    )
    
    db.add(db_pricing)
    db.commit()
    db.refresh(db_pricing)
    return db_pricing

def get_inventory_for_lab(db: Session, lab_id: str):
    """Fetch the full table of tests offered by this lab."""
    return db.query(LabTestPricing).filter(LabTestPricing.lab_id == lab_id).all()

def update_lab_pricing(db: Session, pricing_id: str, update_data: dict):
    """Edit the MRP, Discount, or Turnaround Time for a test."""
    pricing = db.query(LabTestPricing).filter(LabTestPricing.id == pricing_id).first()
    if not pricing:
        return None
    for key, value in update_data.items():
        setattr(pricing, key, value)
    db.commit()
    db.refresh(pricing)
    return pricing

def delete_lab_pricing(db: Session, pricing_id: str) -> bool:
    """Delete a test from this lab's offerings."""
    pricing = db.query(LabTestPricing).filter(LabTestPricing.id == pricing_id).first()
    if not pricing:
        return False
    db.delete(pricing)
    db.commit()
    return True
