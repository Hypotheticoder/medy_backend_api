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
    # Calculate final prices
    discount = pricing_data.mrp * (pricing_data.discount_percent / 100)
    customer_selling_price = round(pricing_data.mrp - discount, 2)
    
    # Save it to the Bridge Table
    db_pricing = LabTestPricing(
        id=uuid.uuid4().hex,
        lab_id=lab_id,
        customer_selling_price=customer_selling_price,
        lab_base_rate=customer_selling_price,
        **pricing_data.model_dump()
    )
    
    db.add(db_pricing)
    db.commit()
    db.refresh(db_pricing)
    return db_pricing

def get_inventory_for_lab(db: Session, lab_id: str):
    """Fetch the full table of tests offered by this lab."""
    results = (
        db.query(LabTestPricing, LabTest)
        .join(LabTest, LabTestPricing.test_id == LabTest.test_id)
        .filter(LabTestPricing.lab_id == lab_id)
        .all()
    )
    
    response = []
    for pricing, test in results:
        discount = pricing.mrp - pricing.customer_selling_price
        discount_percent = (discount / pricing.mrp * 100) if pricing.mrp > 0 else 0.0
        
        response.append({
            "id": pricing.id,
            "test_id": pricing.test_id,
            "test_name": test.test_name,
            "category": test.category,
            "mrp": pricing.mrp,
            "discount_percent": round(discount_percent, 2),
            "final_price": pricing.customer_selling_price,
            "turnaround_time_hours": pricing.turnaround_time_hours,
            "home_collection_available": pricing.home_collection_available,
            "walk_in_available": pricing.walk_in_available
        })
    return response

def update_lab_pricing(db: Session, pricing_id: str, update_data: dict):
    """Edit the MRP, Discount, or Turnaround Time for a test."""
    pricing = db.query(LabTestPricing).filter(LabTestPricing.id == pricing_id).first()
    if not pricing:
        return None
    for key, value in update_data.items():
        setattr(pricing, key, value)
        
    # Recalculate prices if mrp or discount_percent changed
    if "mrp" in update_data or "discount_percent" in update_data:
        discount = pricing.mrp * (pricing.discount_percent / 100)
        pricing.customer_selling_price = round(pricing.mrp - discount, 2)
        pricing.lab_base_rate = pricing.customer_selling_price
        
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
