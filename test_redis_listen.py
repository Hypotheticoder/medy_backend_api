import asyncio
import redis.asyncio as aioredis
import json

async def main():
    client = await aioredis.from_url("redis://localhost:6379", decode_responses=True)
    pubsub = client.pubsub()
    await pubsub.psubscribe("shop_channel_*")
    print("Listening to shop_channel_*...")
    async for message in pubsub.listen():
        print(message)

asyncio.run(main())
