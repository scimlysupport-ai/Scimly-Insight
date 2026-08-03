import redis

r = redis.Redis.from_url('redis://localhost:6379/0')
keys = r.keys('*')
print('total_keys', len(keys))
decoded = [k.decode() for k in keys]
print('sample_keys', decoded[:50])
print('dbsize', r.dbsize())
info = r.info()
print('info_keys_sample', {k: info[k] for k in list(info)[:10]})
# show celery-related keys
celery_keys = [k for k in decoded if k.startswith('celery') or 'celery' in k]
print('celery_keys', celery_keys[:50])
progress_keys = [k for k in decoded if k.startswith('scimly:progress')]
print('progress_keys', progress_keys[:50])
