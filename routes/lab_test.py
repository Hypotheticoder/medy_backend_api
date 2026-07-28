from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from db import get_db
from schemas.lab_test_schemas import LabTestCreate, LabTestResponse, LabTestPricingCreate, LabTestPricingResponse
from crud.lab_test import create_global_test, add_pricing_for_lab

router = APIRouter(prefix="/api/rest/lab-inventory", tags=["REST - Lab Inventory"])
logger = logging.getLogger(__name__)

@router.post("/global", response_model=LabTestResponse)
def add_global_test(payload: LabTestCreate, db: Session = Depends(get_db)):
    """Admin Only: Add a new medical test to the global dictionary."""
    try:
        new_test = create_global_test(db, payload)
        return new_test
    except Exception as e:
        logger.error(f"Failed to add global test: {e}")
        raise HTTPException(status_code=500, detail="Could not create global test.")

@router.post("/pricing/{lab_id}", response_model=LabTestPricingResponse)
def add_test_to_lab(lab_id: str, payload: LabTestPricingCreate, db: Session = Depends(get_db)):
    """Patholab Back-Office: A lab adds a test to their inventory and sets their price."""
    # Note: In production, verify the lab_id matches the logged-in JWT token!
    try:
        new_pricing = add_pricing_for_lab(db, lab_id, payload)
        return new_pricing
    except Exception as e:
        logger.error(f"Failed to add pricing for lab {lab_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not add test to lab inventory.")

from typing import List, Optional
from models.lab_test import LabTest
from models.lab_test_pricing import LabTestPricing

@router.get("/global", response_model=List[LabTestResponse])
def get_global_tests(db: Session = Depends(get_db)):
    return db.query(LabTest).all()

@router.get("/global/search", response_model=List[LabTestResponse])
def search_global_tests(query: str, db: Session = Depends(get_db)):
    return db.query(LabTest).filter(LabTest.test_name.ilike(f"%{query}%")).all()

@router.get("/pricing/{lab_id}", response_model=List[LabTestPricingResponse])
def get_lab_inventory(lab_id: str, db: Session = Depends(get_db)):
    return db.query(LabTestPricing).filter(LabTestPricing.lab_id == lab_id).all()

@router.put("/{test_id}", response_model=LabTestPricingResponse)
def update_lab_inventory(test_id: str, payload: LabTestPricingCreate, db: Session = Depends(get_db)):
    pricing = db.query(LabTestPricing).filter(LabTestPricing.test_id == test_id, LabTestPricing.lab_id == payload.lab_id).first()
    if not pricing:
        raise HTTPException(status_code=404, detail="Test pricing not found in this lab inventory")
    
    pricing.price = payload.price
    pricing.discount_percentage = payload.discount_percentage
    pricing.final_price = payload.final_price
    db.commit()
    db.refresh(pricing)
    return pricing

from pydantic import BaseModel
class DeleteInventoryRequest(BaseModel):
    test_ids: List[str]
    lab_id: str

@router.post("/delete-by-ids")
def delete_lab_inventory(payload: DeleteInventoryRequest, db: Session = Depends(get_db)):
    db.query(LabTestPricing).filter(LabTestPricing.lab_id == payload.lab_id, LabTestPricing.test_id.in_(payload.test_ids)).delete(synchronize_session=False)
    db.commit()
    return {"status": "success", "message": "Tests removed from inventory successfully"}
