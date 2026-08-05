from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
import shutil
import os
from sqlalchemy.orm import Session
from db import get_db
from models.customer import CustomerUser
from schemas.customer import CustomerResponse

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.get("/get-profile/{customer_id}", response_model=CustomerResponse)
def get_customer_profile(customer_id: str, db: Session = Depends(get_db)):
    """Fetch Customer Profile by ID"""
    customer = db.query(CustomerUser).filter(CustomerUser.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # We explicitly include saved_addresses as it's a JSON column
    response_data = customer.__dict__.copy()
    response_data['saved_addresses'] = customer.saved_addresses or []
    return response_data

@router.put("/profile/{customer_id}", response_model=CustomerResponse)
async def update_customer_profile(
    customer_id: str,
    full_name: str = Form(None),
    alternative_phone_no: str = Form(None),
    profile_photo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """Update Customer Profile"""
    customer = db.query(CustomerUser).filter(CustomerUser.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    if full_name is not None:
        customer.name = full_name
        
    if profile_photo is not None:
        os.makedirs("uploads/profiles", exist_ok=True)
        file_path = f"uploads/profiles/{customer_id}_{profile_photo.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(profile_photo.file, buffer)
        customer.profile_picture = f"/{file_path}"
        
    db.commit()
    db.refresh(customer)
    
    response_data = customer.__dict__.copy()
    response_data['saved_addresses'] = customer.saved_addresses or []
    return response_data

