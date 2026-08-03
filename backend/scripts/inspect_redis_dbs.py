import redis

for db in [0, 1]:
    client = redis.Redis.from_url(f'redis://localhost:6379/{db}', decode_responses=True)
    print('DB', db, 'PING', client.ping())
    keys = sorted(client.keys('*'))
    print('TOTAL KEYS', len(keys))
    print('KEYS SAMPLE', keys[:50])
    print('CELERY LIST LEN', client.llen('celery'))
    try:
        print('CELERY LIST', client.lrange('celery', 0, -1))
    except Exception as exc:
        print('CELERY LIST ERROR', exc)
    print('TASK META KEYS', [k for k in keys if k.startswith('celery-task-meta-')])
    print('QUEUE KEYS', [k for k in keys if 'celery' in k.lower()])
    print('---')
