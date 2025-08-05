import redis.asyncio as redis
from ..config import settings

class RedisClient:
    def __init__(self):
        self.client = redis.from_url(settings.redis_url, decode_responses=True)

    async def get(self, key):
        return await self.client.get(key)

    async def setex(self, key, ttl, value):
        await self.client.setex(key, ttl, value)
