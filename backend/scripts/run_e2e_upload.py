import requests
import time

BASE = 'http://127.0.0.1:8001'
HEADERS = {'X-Device-Id': 'test-device'}

with open('..\\sample.csv', 'rb') as f:
    files = {'file': ('sample.csv', f)}
    resp = requests.post(f'{BASE}/api/upload', headers=HEADERS, files=files)

print('upload status:', resp.status_code)
print(resp.text)
resp.raise_for_status()
file_id = resp.json().get('id')
print('uploaded id=', file_id)

for i in range(60):
    r = requests.get(f'{BASE}/api/dataset/{file_id}/progress', headers=HEADERS)
    print('poll', i, '->', r.status_code, r.text)
    if r.status_code == 200:
        try:
            data = r.json()
            if data.get('status') != 'processing':
                print('finished:', data)
                break
        except Exception:
            pass
    time.sleep(1)
else:
    print('timeout waiting for progress')
