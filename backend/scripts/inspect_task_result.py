import redis
from app.config import settings

task_id = 'd6087f1b-9841-440d-b869-28a80e0b1f9a'
client = redis.Redis.from_url(settings.CELERY_RESULT_BACKEND, decode_responses=True)
print('db', client.connection_pool.connection_kwargs.get('db'))
print('exists', client.exists(f'celery-task-meta-{task_id}'))
print('value', client.get(f'celery-task-meta-{task_id}'))
