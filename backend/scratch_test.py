import urllib.request
import json

# 1. Login to get token
login_req = urllib.request.Request(
    "https://scimly-insight.onrender.com/api/auth/login",
    data=json.dumps({"email": "test@example.com", "password": "password123"}).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
login_res = urllib.request.urlopen(login_req)
token = json.loads(login_res.read().decode())["access_token"]
print("Login success, token acquired!")

# 2. Upload file with Authorization header
body = (
    b"--boundary\r\n"
    b'Content-Disposition: form-data; name="file"; filename="test.csv"\r\n'
    b"Content-Type: text/csv\r\n\r\n"
    b"Name,Age,Role\r\nAlice,30,Admin\r\nBob,25,User\r\n"
    b"--boundary--\r\n"
)

upload_req = urllib.request.Request(
    "https://scimly-insight.onrender.com/api/upload",
    data=body,
    headers={
        "Content-Type": "multipart/form-data; boundary=boundary",
        "Authorization": f"Bearer {token}",
    },
)

upload_res = urllib.request.urlopen(upload_req)
file_info = json.loads(upload_res.read().decode())
print("Upload success:", file_info)

file_id = file_info["id"]

# 3. Get Dataset Analysis
dataset_req = urllib.request.Request(
    f"https://scimly-insight.onrender.com/api/dataset/{file_id}",
    headers={"Authorization": f"Bearer {token}"},
)
dataset_res = urllib.request.urlopen(dataset_req)
print("Dataset analysis success:", dataset_res.read().decode())

# 4. Get Progress
progress_req = urllib.request.Request(
    f"https://scimly-insight.onrender.com/api/dataset/{file_id}/progress",
    headers={"Authorization": f"Bearer {token}"},
)
progress_res = urllib.request.urlopen(progress_req)
print("Progress endpoint success:", progress_res.read().decode())
