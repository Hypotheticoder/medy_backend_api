import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis
from typing import Dict, Set

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["Real-Time Engine"])

class RedisPubSubManager:
    def __init__(self, redis_url="redis://localhost:6379"):
        self.redis_url = redis_url
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

    async def redis_listener():
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    order_data = json.loads(message["data"])
                    # In a real app, you would filter by distance using PostGIS here
                    # For now, broadcast to all connected shops
                    await websocket.send_json({"type": "NEW_ORDER", "data": order_data})
        except asyncio.CancelledError:
            await pubsub.unsubscribe("shop_orders")

    listener_task = asyncio.create_task(redis_listener())

    try:
        while True:
            raw_data = await websocket.receive_json()
            action = raw_data.get("action")
            
            if action == "SUBMIT_BID":
                order_id = raw_data.get("order_id")
                bid_payload = {
                    "shop_id": shop_id,
                    "order_id": order_id,
                    "bid_type": raw_data.get("bid_type"), 
                    "proposed_items": raw_data.get("proposed_items"),
                    "total_bid_price": raw_data.get("total_bid_price"),
                    "estimated_ready_time_mins": raw_data.get("estimated_ready_time_mins")
                }
                # Publish the bid to the customer
                await redis_manager.publish_bid(order_id, bid_payload)
                await websocket.send_json({"type": "BID_RECEIVED", "status": "success"})

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

    pubsub = redis_manager.redis_client.pubsub()
    channel_name = f"live_tracking:{order_id}"
    await pubsub.subscribe(channel_name)
    
    async def location_listener():
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    location_data = json.loads(message["data"])
                    await websocket.send_json({"type": "RIDER_LOCATION_UPDATE", "data": location_data})
        except asyncio.CancelledError:
            await pubsub.unsubscribe(channel_name)

    listener_task = asyncio.create_task(location_listener())

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, manager.customer_tracking_rooms, order_id)
        listener_task.cancel()
