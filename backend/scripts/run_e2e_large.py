import requests
import time
import sys

BASE = 'http://127.0.0.1:8001'
HEADERS = {'X-Device-Id': 'test-device'}
FILEPATH = r'C:\Users\ashuc\OneDrive\Desktop\PROJECT X\large_test.csv'

with open(FILEPATH, 'rb') as f:
    files = {'file': ('large_test.csv', f)}
    resp = requests.post(f'{BASE}/api/upload', headers=HEADERS, files=files)

print('upload status:', resp.status_code)
print(resp.text)
resp.raise_for_status()
file_id = resp.json().get('id')
print('uploaded id=', file_id)

for i in range(600):
    r = requests.get(f'{BASE}/api/dataset/{file_id}/progress', headers=HEADERS)
    print('poll', i, '->', r.status_code, r.text)
    if r.status_code == 200:
        try:
            data = r.json()
            if data.get('status') not in ('processing','uploaded'):
                print('finished:', data)
                break
            # If uploaded and progress 0, it's still ok; continue polling
        except Exception:
            pass
    time.sleep(1)
else:
    print('timeout waiting for progress')
