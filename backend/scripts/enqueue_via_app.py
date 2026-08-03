import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.workers.celery_app import app
import requests
import time

# send task via Celery app
res = app.send_task('app.workers.tasks.process_large_file', args=[37])
print('task sent id:', res.id)

# poll progress
url = 'http://127.0.0.1:8001/api/dataset/37/progress'
headers = {'X-Device-Id': 'test-device'}
for i in range(60):
    try:
        r = requests.get(url, headers=headers, timeout=5)
        print(i, r.status_code, r.text)
        data = r.json()
        if data.get('status') in ('ready','failed'):
            print('finished:', data)
            break
    except Exception as e:
        print('poll error', e)
    time.sleep(1)
else:
    print('timeout waiting for progress')
