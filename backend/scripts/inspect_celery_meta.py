import json
import redis

from app.config import settings

client = redis.Redis.from_url(settings.CELERY_RESULT_BACKEND, decode_responses=True)
keys = sorted(client.keys('celery-task-meta-*'))
print('meta keys', len(keys))
for k in keys:
    raw = client.get(k)
    if raw is None:
        continue
    try:
        data = json.loads(raw)
    except Exception as exc:
        print(k, 'parse error', exc, raw)
        continue
    status = data.get('status')
    print(k, 'status=', status, 'date_done=', data.get('date_done'))
    if status == 'FAILURE':
        print('  exception:', data.get('result'))
        print('  traceback:', data.get('traceback'))
    elif status == 'SUCCESS':
        print('  result:', data.get('result'))
    print('---')
