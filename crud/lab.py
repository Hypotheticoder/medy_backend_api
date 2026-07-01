from sqlalchemy.orm import Session
from models.lab import LabUser
from schemas.lab import LabCreate, LabUpdate
from typing import List, Optional

def get_lab(db: Session, lab_id: str) -> Optional[LabUser]:
    return db.query(LabUser).filter(LabUser.lab_id == lab_id).first()

def get_labs(db: Session, skip: int = 0, limit: int = 50) -> List[LabUser]:
    return db.query(LabUser).offset(skip).limit(limit).all()

def create_lab(db: Session, obj_in: LabCreate) -> LabUser:
    db_obj = LabUser(**obj_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_lab(db: Session, db_obj: LabUser, obj_in: LabUpdate) -> LabUser:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_lab(db: Session, db_obj: LabUser) -> None:
    db.delete(db_obj)
    db.commit()
