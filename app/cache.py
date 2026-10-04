import json, os
from redis import Redis
from redis.exceptions import RedisError
_client = None
url = os.getenv("REDIS_URL")
if url:
    try:
        _client = Redis.from_url(url, decode_responses=True, socket_connect_timeout=0.2, socket_timeout=0.2)
        _client.ping()
    except RedisError:
        _client = None

def get_json(key: str):
    if not _client: return None
    try:
        value = _client.get(key)
        return json.loads(value) if value else None
    except (RedisError, ValueError): return None

def set_json(key: str, value, ttl: int = 30):
    if not _client: return
    try: _client.setex(key, ttl, json.dumps(value))
    except RedisError: pass

def delete_pattern(pattern: str):
    if not _client: return
    try:
        keys = list(_client.scan_iter(match=pattern, count=100))
        if keys: _client.delete(*keys)
    except RedisError: pass
