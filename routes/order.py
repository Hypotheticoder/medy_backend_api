from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from sqlalchemy.orm import Session
import requests
import logging
import json
import os
import shutil

from db import get_db
from models.order import Order, generate_order_id
import crud

# Handle missing OrderBid safely until it is created
try:
    from models.order_bid import OrderBid
except ImportError:
    OrderBid = None

from routes.websockets import redis_manager # Updated to match your websockets filename

router = APIRouter(prefix="/api/rest/orders", tags=["Order Lifecycle"])
logger = logging.getLogger(__name__)

# CABY API details (Replace with your actual internal Caby URLs)
CABY_BASE_URL = "https://appbackenddemo.naiyo24.com/customer_orders"

@router.post("/place")
async def place_order(payload: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Step 1: Customer places order -> Creates row -> Broadcasts to shops (Logic handled via Redis)"""
    new_order = Order(
        order_id=generate_order_id(),
        customer_id=payload["customer_id"],
        receiver_name=payload["receiver_name"],
        receiver_phone=payload["receiver_phone"],
        delivery_address=payload["delivery_address_text"],
        delivery_lat=payload["delivery_lat"],
        delivery_lng=payload["delivery_lng"],
        is_emergency=payload.get("is_emergency", False),
        delivery_instructions=payload.get("instructions", ""),
        payment_mode=payload.get("payment_mode", "cod"),
        order_type=payload.get("order_type", "cart"),
        prescription_url=payload.get("prescription_url", None),
        items=payload.get("items", []),
        item_total=payload.get("item_total", 0.0),
        platform_fee=payload.get("platform_fee", 0.0),
        delivery_fee=payload.get("delivery_fee", 0.0),
        taxes=payload.get("taxes", 0.0),
        total_bill_amount=payload.get("total_bill_amount", 0.0),
        order_status="bidding" # TIMER STARTS NOW
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    # (Background Task): Query Postgres with PostGIS/Haversine to find shops within 5km
    # and push a "NEW_ORDER" event to their WebSocket channels via Redis.
    # For now, we broadcast to all connected shops on the "shop_orders" channel.
    async def publish_new_order():
        await redis_manager.connect()
        order_payload = {
            "order_id": new_order.order_id,
            "customer_id": new_order.customer_id,
            "receiver_name": new_order.receiver_name,
            "receiver_phone": new_order.receiver_phone,
            "delivery_address": new_order.delivery_address,
            "delivery_lat": new_order.delivery_lat,
            "delivery_lng": new_order.delivery_lng,
            "items": new_order.items,
            "item_total": new_order.item_total,
            "platform_fee": new_order.platform_fee,
            "delivery_fee": new_order.delivery_fee,
            "taxes": new_order.taxes,
            "total_bill_amount": new_order.total_bill_amount,
            "order_type": new_order.order_type,
            "is_emergency": new_order.is_emergency,
            "created_at": new_order.created_at.isoformat() if new_order.created_at else None
        }
        await redis_manager.redis_client.publish("shop_orders", json.dumps(order_payload))
    
    # 🚨 FIX 3: Use FastAPI's safe background tasks instead of raw asyncio loop
    background_tasks.add_task(publish_new_order)
    
    return {"status": "success", "order_id": new_order.order_id, "message": "Auction started"}

@router.post("/{order_id}/accept-bid")
async def accept_winning_bid(order_id: str, payload: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Step 2: Customer selects a bid. We lock the database, fetch Caby fare, and prepare for checkout."""
    if not OrderBid:
        raise HTTPException(status_code=500, detail="OrderBid model not implemented yet.")

    try:
        # with_for_update() creates a strict SQL lock to prevent race conditions
        order = db.query(Order).with_for_update().filter(Order.order_id == order_id).first()
        if not order or order.order_status != "bidding":
            raise HTTPException(status_code=400, detail="Order not found or auction already closed.")

        winning_bid = db.query(OrderBid).filter(OrderBid.bid_id == payload["bid_id"]).first()
        if not winning_bid:
            raise HTTPException(status_code=404, detail="Bid not found.")

        # 1. Update Order with Shop's specifics
        order.shop_id = winning_bid.shop_id
        order.items = winning_bid.proposed_items
        order.item_total = winning_bid.total_bid_price
        
        # 2. Call Caby to get the exact delivery fare before checkout
        # We assume you have the Shop's lat/lng from the DB in a real scenario
        caby_fare_request = {
            "service_type": "medicine",
            "distance_km": 5.0, # TODO: Calculate actual Haversine distance here between shop and delivery location
            "is_parcel": False 
        }
        
        try:
            caby_response = requests.post(f"{CABY_BASE_URL}/calculate-fare", json=caby_fare_request, timeout=3)
            caby_response.raise_for_status()
            fare_data = caby_response.json()
            
            order.delivery_fee = fare_data["total_fare"]
        except Exception as e:
            logger.warning(f"Failed to fetch fare from Caby, using fallback: {e}")
            order.delivery_fee = 50.0  # Fallback fee
            
        order.total_bill_amount = order.item_total + order.delivery_fee + order.taxes

        # 3. Transition the status to lock it
        order.order_status = "checkout_pending"
        winning_bid.bid_status = "accepted_by_customer"
        
        # (Optional): Reject all other pending bids in DB here
        
        db.commit()
        db.refresh(order)

        # 4. Tell all listening shops the auction is over via Redis
        async def broadcast_closure():
            await redis_manager.connect()
            await redis_manager.redis_client.publish(
                f"live_bids:{order_id}", 
                json.dumps({"type": "AUCTION_CLOSED"})
            )
        background_tasks.add_task(broadcast_closure)

        return {
            "status": "success", 
            "order_id": order.order_id,
            "final_amount": order.total_bill_amount,
            "message": "Bid locked. Proceed to payment."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{order_id}/checkout")
async def complete_checkout(order_id: str, payload: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Step 2.5: Customer completes payment for the order (either COD or Online)"""
    try:
        order = db.query(Order).with_for_update().filter(Order.order_id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found.")
        if order.order_status != "checkout_pending":
            raise HTTPException(status_code=400, detail=f"Order cannot be checked out in status: {order.order_status}")

        payment_mode = payload.get("payment_mode", "cod")
        order.payment_mode = payment_mode
        
        if payment_mode == "cod":
            order.payment_status = "pending"
        elif payment_mode == "online":
            # For online payments, we should ideally verify razorpay signature here.
            # We will mock the validation as success for now since we're assuming the frontend handled it correctly
            # or the test keys are being used.
            order.payment_status = "paid"
            order.transaction_id = payload.get("razorpay_payment_id", "mock_txn_id")
        else:
            raise HTTPException(status_code=400, detail="Invalid payment mode")

        # Checkout complete -> Move order to 'packing' for the shop to handle
        order.order_status = "packing"
        db.commit()
        db.refresh(order)

        # Broadcast to shop that the order is ready for packing
        async def broadcast_packing():
            await redis_manager.connect()
            await redis_manager.redis_client.publish(
                f"shop_channel_{order.shop_id}",
                json.dumps({
                    "type": "order_status_updated",
                    "order": order.to_dict()
                })
            )
        background_tasks.add_task(broadcast_packing)

        return {
            "status": "success",
            "message": "Checkout completed successfully.",
            "order_id": order.order_id,
            "order_status": order.order_status
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{order_id}/dispatch-to-caby")
def dispatch_order_to_caby(order_id: str, db: Session = Depends(get_db)):
    """Step 3: After payment succeeds and Shop packs medicine, we push the job to Caby drivers."""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    
    if order.order_status != "packing":
        raise HTTPException(status_code=400, detail="Order is not ready for dispatch.")
    
    # FETCH REAL SHOP DATA
    from models.pharma_shop import PharmaShopUser
    shop = db.query(PharmaShopUser).filter(PharmaShopUser.shop_id == order.shop_id).first()
    
    if not shop:
        raise HTTPException(status_code=404, detail="Pharmacy data not found for dispatch.")
    
    # Build payload specifically for your Caby `customer_orders/create` endpoint
    caby_job_payload = {
        "order_type": "medicine",
        "vehicle_type": "parcel_bike", # Or whatever config Caby uses for med drops
        "pickup_address": shop.address, 
        "pickup_lat": shop.latitude, # Dynamic Shop Lat
        "pickup_lng": shop.longitude, # Dynamic Shop Lng
        "pickup_contact_name": shop.shop_name, # Driver knows who to ask for
        "pickup_contact_phone": shop.phone,    # Driver can call the shop
        "drop_address": order.delivery_address,
        "drop_lat": order.delivery_lat,
        "drop_lng": order.delivery_lng,
        "drop_contact_name": order.receiver_name,
        "drop_contact_phone": order.receiver_phone,
        "instructions": order.delivery_instructions,
        "is_emergency": order.is_emergency,
        "distance_km": order.distance_km,
        "estimated_time_mins": 15,
        "payment_method": order.payment_mode,
        "item_count": len(order.items) if order.items else 0
    }
    
    try:
        # Create the job in Caby's system
        response = requests.post(f"{CABY_BASE_URL}/create", json=caby_job_payload, timeout=3)
        response.raise_for_status()
        caby_data = response.json()
        caby_tracking_id = caby_data["id"]
    except Exception as e:
        logger.warning(f"Caby integration failed, using fallback tracking ID: {e}")
        caby_tracking_id = "mock_caby_" + order_id
        
    # Link the Caby tracking ID back to our Medicine Order
    order.caby_order_id = caby_tracking_id
    order.order_status = "finding_driver"
    db.commit()
    
    return {"status": "success", "caby_tracking_id": order.caby_order_id}

@router.post("/upload-prescription")
async def upload_prescription(
    customer_id: str,
    prescription: UploadFile = File(...)
):
    """Uploads a customer's prescription and returns the URL."""
    try:
        base_upload_path = os.path.join("uploads", "prescriptions", customer_id)
        os.makedirs(base_upload_path, exist_ok=True)
        
        file_path = os.path.join(base_upload_path, prescription.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(prescription.file, buffer)
            
        return {
            "status": "success",
            "prescription_url": f"/uploads/prescriptions/{customer_id}/{prescription.filename}"
        }
    except Exception as e:
        logger.error(f"Failed to upload prescription: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload prescription")

# 🚨 FIX 3: Added background_tasks parameter here too
@router.post("/{order_id}/cancel")
async def cancel_order(order_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Customer cancels an active order."""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.order_status not in ["bidding", "checkout_pending"]:
        raise HTTPException(status_code=400, detail="Order cannot be cancelled at this stage")
        
    order.order_status = "cancelled"
    db.commit()
    
    # Broadcast cancellation if it was in bidding
    async def broadcast_cancel():
        await redis_manager.connect()
        await redis_manager.redis_client.publish(
            f"live_bids:{order_id}", 
            json.dumps({"type": "AUCTION_CLOSED"})
        )
            
    # 🚨 FIX 3: Use background task
    background_tasks.add_task(broadcast_cancel)
        
    return {"status": "success", "message": "Order cancelled successfully"}
