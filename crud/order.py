from sqlalchemy.orm import Session
from models.order import Order
from schemas.order import OrderCreate, OrderUpdate
from typing import List, Optional

def get_order(db: Session, order_id: str) -> Optional[Order]:
    return db.query(Order).filter(Order.order_id == order_id).first()

def get_orders(db: Session, skip: int = 0, limit: int = 50, customer_id: Optional[str] = None, shop_id: Optional[str] = None) -> List[Order]:
    query = db.query(Order)
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)
    if shop_id:
        query = query.filter(Order.shop_id == shop_id)
    return query.offset(skip).limit(limit).all()

def create_order(db: Session, obj_in: OrderCreate) -> Order:
    db_obj = Order(**obj_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_order(db: Session, db_obj: Order, obj_in: OrderUpdate) -> Order:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_order(db: Session, db_obj: Order) -> None:
    db.delete(db_obj)
    db.commit()
