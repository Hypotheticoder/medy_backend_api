from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from db import get_db
from schemas.lab_test_schemas import LabTestCreate, LabTestResponse, LabTestPricingCreate, LabTestPricingResponse, LabTestPricingUpdate, LabInventoryItemResponse
from crud.lab_test import create_global_test, add_pricing_for_lab, get_inventory_for_lab, update_lab_pricing, delete_lab_pricing

# 🚨 Import the models so we can run our validation checks!
from models.lab_test import LabTest
from models.lab_test_pricing import LabTestPricing 

router = APIRouter(prefix="/api/rest/lab-inventory", tags=["REST - Lab Inventory"])
logger = logging.getLogger(__name__)

@router.post("/global", response_model=LabTestResponse)
def add_global_test(payload: LabTestCreate, db: Session = Depends(get_db)):
    """Admin Only: Add a new medical test to the global dictionary."""
    
    # 🚨 VALIDATION 1: Prevent duplicate Global Tests
    # We use .ilike() so "CBC" and "cbc" are treated as the exact same thing!
    existing_global_test = db.query(LabTest).filter(LabTest.test_name.ilike(payload.test_name)).first()
    if existing_global_test:
        raise HTTPException(
            status_code=400, 
            detail=f"A test named '{existing_global_test.test_name}' already exists in the global catalog."
        )

    try:
        new_test = create_global_test(db, payload)
        return new_test
    except Exception as e:
        logger.error(f"Failed to add global test: {e}")
        raise HTTPException(status_code=500, detail="Could not create global test.")

@router.post("/pricing/{lab_id}", response_model=LabTestPricingResponse)
def add_test_to_lab(lab_id: str, payload: LabTestPricingCreate, db: Session = Depends(get_db)):
    """Patholab Back-Office: A lab adds a test to their inventory and sets their price."""
    
    # 🚨 VALIDATION 2: Prevent a Lab from adding the exact same test twice
    existing_inventory_item = db.query(LabTestPricing).filter(
        LabTestPricing.lab_id == lab_id,
        LabTestPricing.test_id == payload.test_id
    ).first()
    
    if existing_inventory_item:
        raise HTTPException(
            status_code=400, 
            detail="You already have this test in your inventory. Please edit the existing price instead of adding it again."
        )

    try:
        new_pricing = add_pricing_for_lab(db, lab_id, payload)
        return new_pricing
    except Exception as e:
        logger.error(f"Failed to add pricing for lab {lab_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not add test to lab inventory.")

@router.get("/global", response_model=List[LabTestResponse])
def get_global_tests(db: Session = Depends(get_db)):
    """Fetch all tests from the global catalog."""
    return db.query(LabTest).all()

@router.get("/global/search", response_model=List[LabTestResponse])
def search_global_tests(query: str, db: Session = Depends(get_db)):
    """Search for global tests by name."""
    return db.query(LabTest).filter(LabTest.test_name.ilike(f"%{query}%")).all()

# ==========================================
# INVENTORY MANAGEMENT ROUTES
# ==========================================

@router.get("/{lab_id}", response_model=List[LabInventoryItemResponse])
def view_lab_inventory(lab_id: str, db: Session = Depends(get_db)):
    """Patholab Back-Office: Fetch the full table of tests offered by this lab."""
    return get_inventory_for_lab(db, lab_id)

@router.put("/pricing/{pricing_id}", response_model=LabTestPricingResponse)
def edit_inventory_item(pricing_id: str, payload: LabTestPricingUpdate, db: Session = Depends(get_db)):
    """Patholab Back-Office: Edit the MRP, Discount, or Turnaround Time for a test."""
    update_data = payload.model_dump(exclude_unset=True)
    updated_pricing = update_lab_pricing(db, pricing_id, update_data)
    
    if not updated_pricing:
        raise HTTPException(status_code=404, detail="Pricing item not found.")
    return updated_pricing

@router.delete("/pricing/{pricing_id}")
def remove_test_from_inventory(pricing_id: str, db: Session = Depends(get_db)):
    """Patholab Back-Office: Delete a test from this lab's offerings."""
    success = delete_lab_pricing(db, pricing_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pricing item not found.")
    return {"status": "success", "message": "Test removed from inventory."}
