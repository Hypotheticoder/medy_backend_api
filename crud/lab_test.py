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
    # 1. Calculate the final price automatically based on MRP and Discount!
    discount_amount = pricing_data.mrp * (pricing_data.discount_percent / 100)
    calculated_final_price = round(pricing_data.mrp - discount_amount, 2)
    
    # 2. Save it to the Bridge Table
    db_pricing = LabTestPricing(
        id=uuid.uuid4().hex,
        lab_id=lab_id,
        final_price=calculated_final_price,
        **pricing_data.model_dump()
    )
    
    db.add(db_pricing)
    db.commit()
    db.refresh(db_pricing)
    return db_pricing
