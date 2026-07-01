from sqlalchemy.orm import Session
from models.medicine import Medicine
from schemas.medicine import MedicineCreate, MedicineUpdate
from typing import List, Optional

def get_medicine(db: Session, medicine_id: str) -> Optional[Medicine]:
    return db.query(Medicine).filter(Medicine.medicine_id == medicine_id).first()

def get_medicines(db: Session, skip: int = 0, limit: int = 50, search: Optional[str] = None, category: Optional[str] = None) -> List[Medicine]:
    query = db.query(Medicine)
    if search:
        query = query.filter(Medicine.medicine_name.ilike(f"%{search}%"))
    if category:
        query = query.filter(Medicine.medicine_category == category)
    return query.offset(skip).limit(limit).all()

def create_medicine(db: Session, obj_in: MedicineCreate) -> Medicine:
    db_obj = Medicine(**obj_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_medicine(db: Session, db_obj: Medicine, obj_in: MedicineUpdate) -> Medicine:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_medicine(db: Session, db_obj: Medicine) -> None:
    db.delete(db_obj)
    db.commit()

def create_medicines_bulk(db: Session, medicines_in: List[Medicine]) -> List[Medicine]:
    db.add_all(medicines_in)
    db.commit()
    return medicines_in
