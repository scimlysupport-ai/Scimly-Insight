import requests
url='http://127.0.0.1:8001/api/dashboards'
headers={'X-Device-Id':'test-device','Content-Type':'application/json'}
payload={"file_id":31,"name":"Test Dash from script","widgets":[],"layout":[],"filters":{}}
resp=requests.post(url,json=payload,headers=headers,timeout=10)
print(resp.status_code)
print(resp.text)
