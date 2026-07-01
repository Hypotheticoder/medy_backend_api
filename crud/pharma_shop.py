from sqlalchemy.orm import Session
from models.pharma_shop import PharmaShopUser
from schemas.pharma_shop import PharmaShopCreate, PharmaShopUpdate
from typing import List, Optional

def get_pharma_shop(db: Session, shop_id: str) -> Optional[PharmaShopUser]:
    return db.query(PharmaShopUser).filter(PharmaShopUser.shop_id == shop_id).first()

def get_pharma_shops(db: Session, skip: int = 0, limit: int = 50) -> List[PharmaShopUser]:
    return db.query(PharmaShopUser).offset(skip).limit(limit).all()

def create_pharma_shop(db: Session, obj_in: PharmaShopCreate) -> PharmaShopUser:
    db_obj = PharmaShopUser(**obj_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_pharma_shop(db: Session, db_obj: PharmaShopUser, obj_in: PharmaShopUpdate) -> PharmaShopUser:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_pharma_shop(db: Session, db_obj: PharmaShopUser) -> None:
    db.delete(db_obj)
    db.commit()
