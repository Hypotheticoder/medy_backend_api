from sqlalchemy.orm import Session
from models.customer import CustomerUser
from schemas.customer import CustomerCreate, CustomerUpdate
from typing import List, Optional

def get_customer(db: Session, customer_id: str) -> Optional[CustomerUser]:
    return db.query(CustomerUser).filter(CustomerUser.customer_id == customer_id).first()

def get_customer_by_phone(db: Session, phone: str) -> Optional[CustomerUser]:
    return db.query(CustomerUser).filter(CustomerUser.phone == phone).first()

def get_customers(db: Session, skip: int = 0, limit: int = 50) -> List[CustomerUser]:
    return db.query(CustomerUser).offset(skip).limit(limit).all()

def create_customer(db: Session, obj_in: CustomerCreate) -> CustomerUser:
    db_obj = CustomerUser(**obj_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_customer(db: Session, db_obj: CustomerUser, obj_in: CustomerUpdate) -> CustomerUser:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_customer(db: Session, db_obj: CustomerUser) -> None:
    db.delete(db_obj)
    db.commit()
