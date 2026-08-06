import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis
from typing import Dict, Set

from db import SessionLocal
from models.order_bid import OrderBid, generate_bid_id
from models.order import Order
from models.pharma_shop import PharmaShopUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["Real-Time Engine"])

import os

class RedisPubSubManager:
    def __init__(self):
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = os.getenv("REDIS_PORT", "6379")
        self.redis_url = os.getenv("REDIS_URL", f"redis://{redis_host}:{redis_port}/0")
        self.redis_client = None

    async def connect(self):
        if not self.redis_client:
            self.redis_client = await aioredis.from_url(self.redis_url, decode_responses=True)
            logger.info("Connected to Redis for WebSockets")

    async def publish_bid(self, order_id: str, bid_data: dict):
        """Saves the bid in Redis for fast retrieval and broadcasts it to the customer."""
        redis_key = f"order_bids:{order_id}"
        await self.redis_client.rpush(redis_key, json.dumps(bid_data))
        await self.redis_client.expire(redis_key, 300) # 5 minute auction timer
        
        channel_name = f"live_bids:{order_id}"
        await self.redis_client.publish(channel_name, json.dumps(bid_data))

    async def get_all_bids(self, order_id: str):
        """If a customer reconnects, grab all existing bids from Redis instantly."""
        redis_key = f"order_bids:{order_id}"
        bids = await self.redis_client.lrange(redis_key, 0, -1)
        return [json.loads(bid) for bid in bids]

redis_manager = RedisPubSubManager()

class ConnectionManager:
    def __init__(self):
        self.customer_bidding_rooms: Dict[str, Set[WebSocket]] = {}
        self.customer_tracking_rooms: Dict[str, Set[WebSocket]] = {}
        self.active_shops: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, room_dict: dict, key: str):
        await websocket.accept()
        if key not in room_dict:
            room_dict[key] = set()
        room_dict[key].add(websocket)

    def disconnect(self, websocket: WebSocket, room_dict: dict, key: str):
        if key in room_dict:
            room_dict[key].discard(websocket)
            if not room_dict[key]:
                del room_dict[key]
    async def send_shop_update(self, shop_id: str, data: dict):
        if shop_id in self.active_shops:
            dead_sockets = set()
            for ws in self.active_shops[shop_id]:
                try:
                    await ws.send_json(data)
                except Exception as e:
                    logger.error(f"Failed to send update to shop {shop_id}: {e}")
                    dead_sockets.add(ws)
            for ws in dead_sockets:
                self.active_shops[shop_id].discard(ws)
            if not self.active_shops[shop_id]:
                del self.active_shops[shop_id]

manager = ConnectionManager()

@router.websocket("/bidding/customer/{order_id}")
async def customer_bidding_endpoint(websocket: WebSocket, order_id: str):
    """Customer connects here to watch pharmacies bid on their cart in real-time."""
    await manager.connect(websocket, manager.customer_bidding_rooms, order_id)
    await redis_manager.connect()
    
    # Hydrate screen if they dropped connection
    existing_bids = await redis_manager.get_all_bids(order_id)
    if existing_bids:
        await websocket.send_json({"type": "REHYDRATE_BIDS", "bids": existing_bids})

    pubsub = redis_manager.redis_client.pubsub()
    channel_name = f"live_bids:{order_id}"
    await pubsub.subscribe(channel_name)
    
    async def redis_listener():
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    bid_data = json.loads(message["data"])
                    await websocket.send_json({"type": "NEW_BID", "data": bid_data})
        except asyncio.CancelledError:
            await pubsub.unsubscribe(channel_name)

    listener_task = asyncio.create_task(redis_listener())

    try:
        while True:
            await websocket.receive_text() # Keep-alive ping/pong
    except WebSocketDisconnect:
        manager.disconnect(websocket, manager.customer_bidding_rooms, order_id)
        listener_task.cancel()

@router.websocket("/bidding/shop/{shop_id}")
async def shop_bidding_endpoint(websocket: WebSocket, shop_id: str):
    """Pharmacies connect here to receive new local orders and submit their bids."""
    await manager.connect(websocket, manager.active_shops, shop_id)
    await redis_manager.connect()

    pubsub = redis_manager.redis_client.pubsub()
    await pubsub.subscribe("shop_orders")
    await pubsub.subscribe(f"shop_channel_{shop_id}")

    async def redis_listener():
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    if message["channel"] == "shop_orders":
                        # Broadcast to all connected shops
                        await websocket.send_json({"type": "new_order_broadcast", "order": data})
                    elif message["channel"] == f"shop_channel_{shop_id}":
                        # Specific update for this shop (e.g. order_updated)
                        await websocket.send_json(data)
        except asyncio.CancelledError:
            await pubsub.unsubscribe("shop_orders")
            await pubsub.unsubscribe(f"shop_channel_{shop_id}")

    listener_task = asyncio.create_task(redis_listener())

    try:
        while True:
            raw_data = await websocket.receive_json()
            action = raw_data.get("action") or raw_data.get("type")
            
            if action == "get_broadcast_orders":
                db = SessionLocal()
                try:
                    
                    # Exclude orders this shop has already bid on
                    bidded_orders = db.query(OrderBid.order_id).filter(OrderBid.shop_id == shop_id).all()
                    bidded_order_ids = [b[0] for b in bidded_orders]
                    
                    query = db.query(Order).filter(Order.order_status == "bidding")
                    if bidded_order_ids:
                        query = query.filter(~Order.order_id.in_(bidded_order_ids))
                        
                    orders = query.order_by(Order.created_at.desc()).limit(20).all()
                    
                    orders_data = []
                    for o in orders:
                        orders_data.append({
                            "order_id": o.order_id,
                            "customer_id": o.customer_id,
                            "receiver_name": o.receiver_name,
                            "receiver_phone": o.receiver_phone,
                            "delivery_address": o.delivery_address,
                            "delivery_lat": o.delivery_lat,
                            "delivery_lng": o.delivery_lng,
                            "items": o.items,
                            "item_total": o.item_total,
                            "order_type": o.order_type,
                            "prescription_url": o.prescription_url,
                            "is_emergency": o.is_emergency,
                            "platform_fee": o.platform_fee,
                            "delivery_fee": o.delivery_fee,
                            "taxes": o.taxes,
                            "total_bill_amount": o.total_bill_amount,
                            "created_at": o.created_at.isoformat() if o.created_at else None
                        })
                    await websocket.send_json({"type": "pending_broadcast_orders", "data": orders_data})
                except Exception as e:
                    logger.error(f"Error fetching broadcast orders: {e}")
                finally:
                    db.close()

            elif action == "get_shop_orders":
                page = raw_data.get("page", 1)
                limit = raw_data.get("limit", 20)
                status = raw_data.get("status")
                
                db = SessionLocal()
                try:
                    query = db.query(Order).filter(Order.shop_id == shop_id)
                    if status:
                        query = query.filter(Order.order_status == status)
                        
                    orders = query.order_by(Order.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
                    
                    orders_data = []
                    for o in orders:
                        orders_data.append({
                            "order_id": o.order_id,
                            "customer_id": o.customer_id,
                            "receiver_name": o.receiver_name,
                            "receiver_phone": o.receiver_phone,
                            "delivery_address": o.delivery_address,
                            "delivery_lat": o.delivery_lat,
                            "delivery_lng": o.delivery_lng,
                            "items": o.items,
                            "item_total": o.item_total,
                            "order_type": o.order_type,
                            "prescription_url": o.prescription_url,
                            "is_emergency": o.is_emergency,
                            "order_status": o.order_status,
                            "platform_fee": o.platform_fee,
                            "delivery_fee": o.delivery_fee,
                            "taxes": o.taxes,
                            "total_bill_amount": o.total_bill_amount,
                            "payment_method": o.payment_mode,
                            "created_at": o.created_at.isoformat() if o.created_at else None
                        })
                    await websocket.send_json({"type": "orders_list", "data": orders_data})
                except Exception as e:
                    logger.error(f"Error fetching shop orders: {e}")
                finally:
                    db.close()

            elif action == "SUBMIT_BID":
                order_id = raw_data.get("order_id")
                new_bid_id = generate_bid_id()
                
                # Save to Postgres Database
                db = SessionLocal()
                bid_payload = None
                try:
                    shop = db.query(PharmaShopUser).filter(PharmaShopUser.shop_id == shop_id).first()
                    
                    new_bid = OrderBid(
                        bid_id=new_bid_id,
                        order_id=order_id,
                        shop_id=shop_id,
                        proposed_items=raw_data.get("proposed_items", []),
                        total_bid_price=raw_data.get("total_bid_price", 0.0),
                    )
                    db.add(new_bid)
                    db.commit()
                    
                    bid_payload = {
                        "quote_id": new_bid_id,
                        "shop_id": shop_id,
                        "order_id": order_id,
                        "shop_name": shop.shop_name if shop else "Pharmacy",
                        "shop_phone": shop.phone if shop else "",
                        "shop_address": shop.address if shop else "",
                        "shop_lat": shop.latitude if shop else None,
                        "shop_lng": shop.longitude if shop else None,
                        "items": raw_data.get("proposed_items", []),
                        "item_total": raw_data.get("total_bid_price", 0.0),
                        "total_bill_amount": raw_data.get("total_bid_price", 0.0),
                        "status": "pending"
                    }
                except Exception as e:
                    with open("bid_error.log", "a") as f:
                        f.write(f"Failed to save bid to DB: {e}\n")
                    logger.error(f"Failed to save bid to DB: {e}")
                    db.rollback()
                finally:
                    db.close()

                if bid_payload:
                    # Publish the bid to the customer
                    await redis_manager.publish_bid(order_id, bid_payload)
                    await websocket.send_json({"type": "BID_RECEIVED", "status": "success"})

            elif action == "REJECT_ORDER":
                order_id = raw_data.get("order_id")
                new_bid_id = generate_bid_id()
                db = SessionLocal()
                try:
                    # Check if already bid
                    existing = db.query(OrderBid).filter(OrderBid.shop_id == shop_id, OrderBid.order_id == order_id).first()
                    if not existing:
                        new_bid = OrderBid(
                            bid_id=new_bid_id,
                            order_id=order_id,
                            shop_id=shop_id,
                            total_bid_price=0.0,
                            bid_status="rejected"
                        )
                        db.add(new_bid)
                        db.commit()
                except Exception as e:
                    logger.error(f"Error rejecting order: {e}")
                    db.rollback()
                finally:
                    db.close()

    except WebSocketDisconnect:
        manager.disconnect(websocket, manager.active_shops, shop_id)
        listener_task.cancel()

@router.websocket("/tracking/customer/{order_id}")
async def customer_tracking_endpoint(websocket: WebSocket, order_id: str):
    """
    Once the order is out for delivery, the customer connects here.
    Your Caby backend will push driver GPS updates to the Redis channel 'live_tracking:{order_id}'.
    """
    await manager.connect(websocket, manager.customer_tracking_rooms, order_id)
    await redis_manager.connect()

    # Hydrate tracking screen with latest order data
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if order:
            await websocket.send_json({
                "type": "ORDER_UPDATED",
                "order": order.to_dict()
            })
    except Exception as e:
        logger.error(f"Error hydrating tracking: {e}")
    finally:
        db.close()

    pubsub = redis_manager.redis_client.pubsub()
    channel_name = f"live_tracking:{order_id}"
    await pubsub.subscribe(channel_name)
    
    async def location_listener():
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    parsed_data = json.loads(message["data"])
                    if isinstance(parsed_data, dict) and "type" in parsed_data:
                        await websocket.send_json(parsed_data)
                    else:
                        await websocket.send_json({"type": "RIDER_LOCATION_UPDATE", "data": parsed_data})
        except asyncio.CancelledError:
            await pubsub.unsubscribe(channel_name)

    listener_task = asyncio.create_task(location_listener())

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, manager.customer_tracking_rooms, order_id)
        listener_task.cancel()

@router.websocket("/labs/{lab_id}")
async def lab_notifications_endpoint(websocket: WebSocket, lab_id: str):
    """
    Pathology Labs connect their tablets here. 
    It sits silently and waits for the Redis Ping we fired in the REST '/book' route.
    """
    # 1. Connect the Lab's WebSocket
    # We can reuse the active_shops dictionary or create a new one for labs
    await manager.connect(websocket, manager.active_shops, lab_id)
    await redis_manager.connect()

    # 2. Subscribe to this specific lab's private channel
    pubsub = redis_manager.redis_client.pubsub()
    channel_name = f"lab_orders:{lab_id}"
    await pubsub.subscribe(channel_name)

    # 3. Background task to push Redis alerts straight to the Lab's tablet
    async def lab_alert_listener():
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    # This contains {"type": "NEW_LAB_BOOKING", "booking": {...}}
                    await websocket.send_text(message["data"])
        except asyncio.CancelledError:
            await pubsub.unsubscribe(channel_name)

    listener_task = asyncio.create_task(lab_alert_listener())

    try:
        while True:
            # Keep connection alive / handle client-side ping-pongs
            await websocket.receive_text() 
    except WebSocketDisconnect:
        manager.disconnect(websocket, manager.active_shops, lab_id)
        listener_task.cancel() # Stop listening when they turn off the tablet
