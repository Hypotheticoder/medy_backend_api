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
