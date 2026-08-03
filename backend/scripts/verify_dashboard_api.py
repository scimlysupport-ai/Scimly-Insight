import os
import sys
import time
import requests

BASE = 'http://127.0.0.1:8001'
HEADERS = {'X-Device-Id': 'test-device'}

def create_upload():
    filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'sample.csv'))
    with open(filepath, 'rb') as f:
        resp = requests.post(f'{BASE}/api/upload', headers=HEADERS, files={'file': ('sample.csv', f)})
    resp.raise_for_status()
    return resp.json()['id']


def create_dashboard(file_id):
    payload = {
        'file_id': file_id,
        'name': 'API test dashboard',
        'widgets': [
            {'chart': 'kpi', 'title': 'Test widget', 'column': 'col1'}
        ],
        'layout': [{'i': 'widget-1', 'x': 0, 'y': 0, 'w': 6, 'h': 4}],
        'filters': {}
    }
    resp = requests.post(f'{BASE}/api/dashboards', headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()


def get_dashboard(dashboard_id):
    resp = requests.get(f'{BASE}/api/dashboards/{dashboard_id}', headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def update_dashboard(dashboard_id):
    payload = {'name': 'Updated name'}
    resp = requests.put(f'{BASE}/api/dashboards/{dashboard_id}', headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()


def list_dashboards(file_id):
    resp = requests.get(f'{BASE}/api/dashboards', headers=HEADERS, params={'file_id': file_id})
    resp.raise_for_status()
    return resp.json()


def duplicate_dashboard(dashboard_id):
    resp = requests.post(f'{BASE}/api/dashboards/{dashboard_id}/duplicate', headers=HEADERS, json={})
    resp.raise_for_status()
    return resp.json()


def delete_dashboard(dashboard_id):
    resp = requests.delete(f'{BASE}/api/dashboards/{dashboard_id}', headers=HEADERS)
    return resp.status_code


if __name__ == '__main__':
    file_id = create_upload()
    print('uploaded file_id', file_id)
    dash = create_dashboard(file_id)
    print('created dashboard', dash)
    got = get_dashboard(dash['id'])
    print('got dashboard', got['name'])
    updated = update_dashboard(dash['id'])
    print('updated dashboard', updated['name'])
    listed = list_dashboards(file_id)
    print('listed count', len(listed))
    dup = duplicate_dashboard(dash['id'])
    print('duplicated dashboard id', dup['id'])
    code = delete_dashboard(dash['id'])
    print('deleted dashboard status', code)
