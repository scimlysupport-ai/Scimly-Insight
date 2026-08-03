import time
import requests

BASE = 'http://127.0.0.1:8001'
HEADERS = {'X-Device-Id': 'test-device'}
FILE_ID = 46

for i in range(30):
    resp = requests.get(f'{BASE}/api/dataset/{FILE_ID}/progress', headers=HEADERS, timeout=10)
    print(i, resp.status_code, resp.text)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('status') in ('ready', 'failed'):
            print('final:', data)
            break
    time.sleep(2)
else:
    print('timeout waiting for final status')
