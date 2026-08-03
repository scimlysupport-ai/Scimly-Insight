from app.workers.tasks import process_large_file
import requests
import time

# enqueue
process_large_file.delay(37)
print('enqueued 37')

# poll progress
url = 'http://127.0.0.1:8001/api/dataset/37/progress'
headers = {'X-Device-Id': 'test-device'}
for i in range(30):
    try:
        r = requests.get(url, headers=headers, timeout=5)
        print(i, r.status_code, r.text)
    except Exception as e:
        print('poll error', e)
    time.sleep(1)
