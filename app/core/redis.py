"""
Redis 클라이언트. refresh token 저장/블랙리스트, 캐싱 등에 사용 예정.
"""
import redis

from app.core.config import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_redis():
    return redis_client