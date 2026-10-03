from redis import Redis

from backend.config import get_settings

_client: Redis | None = None


def get_redis() -> Redis:
    global _client
    if _client is None:
        _client = Redis.from_url(get_settings().redis_url, decode_responses=True, protocol=2)
    return _client


def set_redis_client(client: Redis) -> None:
    global _client
    _client = client


def store_token(jti: str, user_id: int, ttl_seconds: int) -> None:
    get_redis().set(f"auth:token:{jti}", str(user_id), ex=ttl_seconds)


def token_exists(jti: str) -> bool:
    return bool(get_redis().exists(f"auth:token:{jti}"))


def delete_token(jti: str) -> None:
    get_redis().delete(f"auth:token:{jti}")
