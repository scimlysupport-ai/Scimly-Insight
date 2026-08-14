from fastapi.testclient import TestClient
from pathlib import Path
from app.main import app

client = TestClient(app)
path = Path('..') / 'sample.csv'
print('sample exists', path.exists())
with open(path, 'rb') as f:
    files = {'file': ('sample.csv', f, 'text/csv')}
    r = client.post('/api/upload', files=files, headers={'X-Device-Id': 'debug-test'})
    print('upload', r.status_code, r.text)
    if r.status_code == 200:
        file_id = r.json()['id']
        r2 = client.get(f'/api/dataset/{file_id}', headers={'X-Device-Id': 'debug-test'})
        print('dataset', r2.status_code, r2.text[:4000])
        r3 = client.get(f'/api/dataset/{file_id}/recommendations', headers={'X-Device-Id': 'debug-test'})
        print('recommendations', r3.status_code, r3.text[:4000])
        r4 = client.post(f'/api/dataset/{file_id}/dashboard', json={'categorical': {}, 'date_ranges': {}}, headers={'X-Device-Id': 'debug-test'})
        print('dashboard', r4.status_code, r4.text[:8000])
