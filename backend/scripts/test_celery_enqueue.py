from app.workers.celery_app import app

result = app.send_task('app.workers.tasks.process_large_file', args=[999999], kwargs={})
print('task id', result.id)
print('result status', result.status)
print('result info', getattr(result, 'info', None))
print('waiting for result...')
try:
    res = result.get(timeout=10, propagate=False)
    print('result returned:', res)
except Exception as exc:
    print('result wait exception:', type(exc).__name__, exc)
print('final status', result.status)
print('ready', result.ready())
print('failed', result.failed())
