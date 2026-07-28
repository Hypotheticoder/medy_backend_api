from fastapi import APIRouter, Depends, HTTPException
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
