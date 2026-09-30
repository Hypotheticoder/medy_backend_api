from sqlalchemy.orm import Session
from models.b2b_cart import B2BCart
from schemas.b2b_cart_schemas import AddToB2BCart
from fastapi import HTTPException

def get_or_create_b2b_cart(db: Session, shop_id: str):
    cart = db.query(B2BCart).filter(B2BCart.shop_id == shop_id).first()
    if not cart:
        cart = B2BCart(shop_id=shop_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

def add_item_to_cart(db: Session, shop_id: str, request: AddToB2BCart):
    cart = get_or_create_b2b_cart(db, shop_id)
    
    # The Swiggy Check: Block if adding from a different distributor
    if cart.active_distributor_id and cart.active_distributor_id != request.distributor_id:
        if len(cart.items) > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Cart contains items from another distributor. Clear cart first."
            )
    
    # Set the active distributor if cart was empty
    cart.active_distributor_id = request.distributor_id
    
    # Calculate price and append item (simplified logic, you'll need to check if item already exists and update qty)
    item_dict = request.item.model_dump()
    cart.items.append(item_dict)
    
    # SQLAlchemy JSON mutation trigger
    cart.items.changed() 
    cart.total_estimated_price += (request.item.ptr * request.item.qty_boxes)
    
    db.commit()
    db.refresh(cart)
    return cart

def clear_b2b_cart(db: Session, shop_id: str):
    cart = get_or_create_b2b_cart(db, shop_id)
    cart.items = []
    cart.active_distributor_id = None
    cart.total_estimated_price = 0.0
    db.commit()
    return cart
