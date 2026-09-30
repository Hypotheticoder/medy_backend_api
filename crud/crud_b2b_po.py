from sqlalchemy.orm import Session
from models.b2b_cart import B2BCart
from models.b2b_purchase_order import B2BPurchaseOrder
from schemas.b2b_po_schemas import B2BOrderCheckout
from fastapi import HTTPException

def checkout_b2b_cart(db: Session, shop_id: str, checkout_req: B2BOrderCheckout):
    cart = db.query(B2BCart).filter(B2BCart.shop_id == shop_id).first()
    
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Calculate GST logic (assuming intra-state for now: CGST 6%, SGST 6% for a 12% item)
    subtotal = 0.0
    cgst_total = 0.0
    sgst_total = 0.0

    for item in cart.items:
        item_total = item["ptr"] * item["qty_boxes"]
        subtotal += item_total
        
        # Split GST equally for CGST and SGST
        half_gst = item["gst_percentage"] / 2 / 100
        cgst_total += (item_total * half_gst)
        sgst_total += (item_total * half_gst)

    total_amount = subtotal + cgst_total + sgst_total

    # Create the PO
    new_po = B2BPurchaseOrder(
        shop_id=shop_id,
        distributor_id=cart.active_distributor_id,
        items=cart.items,
        subtotal=subtotal,
        cgst_amount=cgst_total,
        sgst_amount=sgst_total,
        total_invoice_amount=total_amount,
        payment_terms=checkout_req.payment_terms,
        delivery_notes=checkout_req.delivery_notes
    )
    
    db.add(new_po)
    
    # Empty the cart after successful PO creation
    cart.items = []
    cart.active_distributor_id = None
    cart.total_estimated_price = 0.0
    
    db.commit()
    db.refresh(new_po)
    return new_po

def get_retailer_orders(db: Session, shop_id: str):
    return db.query(B2BPurchaseOrder).filter(B2BPurchaseOrder.shop_id == shop_id).order_by(B2BPurchaseOrder.created_at.desc()).all()

def get_distributor_orders(db: Session, distributor_id: str):
    return db.query(B2BPurchaseOrder).filter(B2BPurchaseOrder.distributor_id == distributor_id).order_by(B2BPurchaseOrder.created_at.desc()).all()
