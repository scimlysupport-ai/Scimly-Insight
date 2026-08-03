import os
import time
import requests

BASE = 'http://127.0.0.1:8001'

def register_user(email, password, name):
    payload = {
        'email': email,
        'password': password,
        'name': name,
    }
    resp = requests.post(f'{BASE}/api/auth/register', json=payload)
    resp.raise_for_status()
    return resp.json()


def login_user(email, password):
    payload = {'email': email, 'password': password}
    resp = requests.post(f'{BASE}/api/auth/login', json=payload)
    resp.raise_for_status()
    return resp.json()


def fetch_me(token):
    resp = requests.get(f'{BASE}/api/auth/me', headers={'Authorization': f'Bearer {token}'})
    resp.raise_for_status()
    return resp.json()


if __name__ == '__main__':
    timestamp = int(time.time())
    email = f'test+auth{timestamp}@example.com'
    password = 'Password123!'
    name = 'Test Auth'

    print('Registering user', email)
    reg = register_user(email, password, name)
    print('Registered:', reg['user']['email'], 'token length', len(reg['access_token']))

    print('Logging in user')
    login = login_user(email, password)
    print('Logged in:', login['user']['email'], 'token length', len(login['access_token']))

    print('Fetching /auth/me')
    me = fetch_me(login['access_token'])
    print('Me:', me)
