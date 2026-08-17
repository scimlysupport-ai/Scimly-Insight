import urllib.request
import urllib.error

req = urllib.request.Request("https://scimly-insight.onrender.com/api/dataset/29/progress")
try:
    res = urllib.request.urlopen(req)
    print("SUCCESS:", res.read().decode())
except urllib.error.HTTPError as e:
    print("Error code:", e.code)
    print("Error body:", e.read().decode())
