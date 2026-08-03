import redis
from app.config import settings

client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
print('broker_url', settings.REDIS_URL)
print('db', client.connection_pool.connection_kwargs.get('db'))
print('ping', client.ping())
keys = sorted(client.keys('*'))
print('total_keys', len(keys))
print('keys_sample', keys[:50])
print('celery_list_len', client.llen('celery'))
print('celery_list', client.lrange('celery', 0, -1))
print('celery_queues', [k for k in keys if 'celery' in k.lower()])
print('progress_keys', [k for k in keys if k.startswith('scimly:progress:')])
