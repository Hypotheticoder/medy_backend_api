from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import logging
import csv
import io

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

@router.post("/global/upload-csv")
async def upload_labtest_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Admin Only: Upload a CSV file to bulk import lab tests to the global catalog.
    Expected CSV Headers: 
    test_name, category, description, is_profile, number_of_parameters, sample_type, search_tags, fasting_required, fasting_hours, pre_test_info
    """
    from models.lab_test import generate_test_id
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only .csv files are supported.")

    try:
        contents = await file.read()
        decoded_content = contents.decode('utf-8-sig') 
        csv_reader = csv.DictReader(io.StringIO(decoded_content))
        
        required_headers = ['test_name', 'category']
        headers = [h.strip().lower() for h in (csv_reader.fieldnames or [])]
        
        missing_headers = [h for h in required_headers if h not in headers]
        if missing_headers:
            raise HTTPException(status_code=400, detail=f"Missing required CSV headers: {missing_headers}")

        actual_to_lower = {h: h.strip().lower() for h in (csv_reader.fieldnames or [])}
        
        tests_to_insert = []
        row_count = 0
        
        for row in csv_reader:
            clean_row = {actual_to_lower[k]: v for k, v in row.items() if k}

            raw_name = clean_row.get('test_name', '')
            raw_category = clean_row.get('category', '')
            if not raw_name or str(raw_name).strip() == '' or not raw_category or str(raw_category).strip() == '':
                continue

            try:
                # Booleans
                prof_str = str(clean_row.get('is_profile', 'false')).strip().lower()
                is_prof = prof_str in ['true', 'yes', '1', 'y']
                
                fast_str = str(clean_row.get('fasting_required', 'false')).strip().lower()
                is_fasting = fast_str in ['true', 'yes', '1', 'y']
                
                # Integer
                num_params_raw = clean_row.get('number_of_parameters', 1)
                try:
                    num_params = int(num_params_raw) if num_params_raw else 1
                except ValueError:
                    num_params = 1

                new_test = LabTest(
                    test_id=generate_test_id(),
                    test_name=str(raw_name).strip(),
                    category=str(raw_category).strip(),
                    description=str(clean_row.get('description', '')).strip() or None,
                    is_profile=is_prof,
                    number_of_parameters=num_params,
                    sample_type=str(clean_row.get('sample_type', '')).strip() or None,
                    search_tags=str(clean_row.get('search_tags', '')).strip() or None,
                    fasting_required=is_fasting,
                    fasting_hours=str(clean_row.get('fasting_hours', '')).strip() or None,
                    pre_test_info=str(clean_row.get('pre_test_info', '')).strip() or None
                )
                tests_to_insert.append(new_test)
                row_count += 1
                
            except ValueError as ve:
                logger.error(f"Row skipped due to parsing error (Row {row_count + 1}): {ve}")
                continue 

        if tests_to_insert:
            db.bulk_save_objects(tests_to_insert)
            db.commit()
            
        return {
            "status": "success",
            "message": f"Successfully imported {row_count} lab tests.",
            "imported_count": row_count
        }
        
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Database integrity error. Check for duplicate IDs or invalid data.")
    except Exception as e:
        db.rollback()
        logger.error(f"Fatal CSV Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")

