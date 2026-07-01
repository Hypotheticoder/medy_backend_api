from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import logging
import csv
import io
import uuid
from db import get_db
from models.medicine import Medicine
from schemas.medicine import MedicineCreate, MedicineUpdate, MedicineResponse
import crud

router = APIRouter(prefix="/api/rest/medicines", tags=["REST - Medicines"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[MedicineResponse])
async def list_medicines(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get a list of medicines, optionally filtered by name (search) or category.
    """
    try:
        medicines = crud.get_medicines(db, skip=skip, limit=limit, search=search, category=category)
        return medicines
    except Exception as e:
        logger.error(f"Error fetching medicines: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/{medicine_id}", response_model=MedicineResponse)
async def get_medicine(medicine_id: str, db: Session = Depends(get_db)):
    """
    Get a specific medicine by ID.
    """
    try:
        medicine = crud.get_medicine(db, medicine_id=medicine_id)
        if not medicine:
            raise HTTPException(status_code=404, detail="Medicine not found")
        return medicine
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching medicine: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/", response_model=MedicineResponse, status_code=status.HTTP_201_CREATED)
async def create_medicine(payload: MedicineCreate, db: Session = Depends(get_db)):
    """
    Create a new medicine entry.
    """
    try:
        new_medicine = crud.create_medicine(db, obj_in=payload)
        return new_medicine
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Medicine with this ID might already exist")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create medicine: {e}")
        raise HTTPException(status_code=500, detail="Failed to create medicine")

@router.put("/{medicine_id}", response_model=MedicineResponse)
async def update_medicine(medicine_id: str, payload: MedicineUpdate, db: Session = Depends(get_db)):
    """
    Update an existing medicine.
    """
    try:
        medicine = crud.get_medicine(db, medicine_id=medicine_id)
        if not medicine:
            raise HTTPException(status_code=404, detail="Medicine not found")
        
        medicine = crud.update_medicine(db, db_obj=medicine, obj_in=payload)
        return medicine
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update medicine: {e}")
        raise HTTPException(status_code=500, detail="Failed to update medicine")

@router.delete("/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medicine(medicine_id: str, db: Session = Depends(get_db)):
    """
    Delete a medicine by ID.
    """
    try:
        medicine = crud.get_medicine(db, medicine_id=medicine_id)
        if not medicine:
            raise HTTPException(status_code=404, detail="Medicine not found")
        
        crud.delete_medicine(db, db_obj=medicine)
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete medicine: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete medicine")

def generate_med_id():
    return f"MED-{uuid.uuid4().hex[:8].upper()}"

@router.post("/upload-csv")
async def upload_medicine_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a CSV file to bulk import medicines.
    Expected CSV Headers: 
    name, manufacturer, pack_form, pack_size, category, composition, mrp, discount, prescription_required
    """
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only .csv files are supported. Please export your .xls to CSV.")

    try:
        contents = await file.read()
        # Ensure we decode cleanly (utf-8-sig handles invisible Excel BOM characters)
        decoded_content = contents.decode('utf-8-sig') 
        csv_reader = csv.DictReader(io.StringIO(decoded_content))
        
        # Validate headers exist (case-insensitive check)
        # 🚨 THE FIX: Only 'name' is strictly required now. Everything else is optional!
        required_headers = ['name']
        headers = [h.strip().lower() for h in (csv_reader.fieldnames or [])]
        
        missing_headers = [h for h in required_headers if h not in headers]
        if missing_headers:
            raise HTTPException(status_code=400, detail=f"Missing required CSV headers: {missing_headers}")

        # Map actual headers to lower-case for robust extraction
        actual_to_lower = {h: h.strip().lower() for h in (csv_reader.fieldnames or [])}
        
        medicines_to_insert = []
        row_count = 0
        
        for row in csv_reader:
            # 1. Clean the row dictionary based on lower-case headers
            clean_row = {actual_to_lower[k]: v for k, v in row.items() if k}

            # 2. 🚨 THE FIX: Skip empty phantom rows created by Excel
            raw_name = clean_row.get('name', '')
            if not raw_name or str(raw_name).strip() == '':
                continue

            try:
                # 3. Safely extract math fields
                mrp_value = float(clean_row.get('mrp', 0) or 0)
                discount_value = float(clean_row.get('discount', 0) or 0)
                final_price = mrp_value - (mrp_value * (discount_value / 100))
                
                # Convert 'true'/'false' strings to actual Booleans
                rx_req_str = str(clean_row.get('prescription_required', 'false')).strip().lower()
                is_rx_required = rx_req_str in ['true', 'yes', '1', 'y']

                new_med = Medicine(
                    medicine_id=generate_med_id(),
                    medicine_name=str(raw_name).strip(),
                    manufacturer=str(clean_row.get('manufacturer', '')).strip(),
                    
                    # 🚨 THE FIX: Provide safe string defaults if the dataset is missing these columns
                    pack_form=str(clean_row.get('pack_form', 'Standard')).strip() or 'Standard',     
                    pack_size=str(clean_row.get('pack_size', '1 Unit')).strip() or '1 Unit',     
                    
                    medicine_category=str(clean_row.get('category', 'General')).strip(),
                    medicine_composition=str(clean_row.get('composition', '')).strip(),
                    mrp=mrp_value,
                    discount_percent=discount_value,
                    final_selling_price=round(final_price, 2),
                    prescription_required=is_rx_required
                )
                medicines_to_insert.append(new_med)
                row_count += 1
                
            except ValueError as ve:
                logger.error(f"Row skipped due to parsing error (Row {row_count + 1}): {ve}")
                continue 

        if medicines_to_insert:
            # bulk_save_objects is insanely fast for large CSVs
            db.bulk_save_objects(medicines_to_insert)
            db.commit()
            
        return {
            "status": "success",
            "message": f"Successfully imported {row_count} medicines.",
            "imported_count": row_count
        }
        
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Database integrity error. Check for duplicate IDs or invalid data.")
    except Exception as e:
        db.rollback()
        logger.error(f"Fatal CSV Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")
