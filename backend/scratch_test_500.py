import urllib.request
import urllib.error

req = urllib.request.Request("https://scimly-insight.onrender.com/api/dataset/19/progress")
try:
    urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    print("Error Code:", e.code)
    print("Error Body:", e.read().decode())
