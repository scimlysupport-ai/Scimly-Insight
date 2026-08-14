import requests
import time
from pathlib import Path

base = 'http://127.0.0.1:8000/api'
path = Path('..') / 'sample.csv'
print('sample exists', path.exists())
with open(path, 'rb') as f:
    files = {'file': ('sample.csv', f, 'text/csv')}
    r = requests.post(base + '/upload', files=files, headers={'X-Device-Id': 'debug-test'}, timeout=120)
    print('upload status', r.status_code)
    print(r.text)
    if r.status_code == 200:
        file_id = r.json()['id']
        time.sleep(2)
        rr = requests.get(base + f'/dataset/{file_id}', headers={'X-Device-Id': 'debug-test'}, timeout=120)
        print('dataset status', rr.status_code)
        print(rr.text[:4000])
        rr2 = requests.get(base + f'/dataset/{file_id}/recommendations', headers={'X-Device-Id': 'debug-test'}, timeout=120)
        print('recommendations status', rr2.status_code)
        print(rr2.text[:4000])
        rr3 = requests.post(base + f'/dataset/{file_id}/dashboard', json={'categorical': {}, 'date_ranges': {}}, headers={'X-Device-Id': 'debug-test'}, timeout=120)
        print('dashboard status', rr3.status_code)
        print(rr3.text[:8000])
