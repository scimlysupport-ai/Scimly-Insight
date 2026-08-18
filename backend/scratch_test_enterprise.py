import urllib.request
import urllib.error
import json

base_url = "https://scimly-insight.onrender.com/api"

# Login to get JWT
login_data = json.dumps({"email": "ashishfree30@gmail.com", "password": "Password123!"}).encode()
login_req = urllib.request.Request(
    f"{base_url}/auth/login",
    data=login_data,
    headers={"Content-Type": "application/json"}
)

try:
    res = urllib.request.urlopen(login_req)
    token = json.loads(res.read().decode())["access_token"]
    print("Logged in successfully. Token acquired.")
except Exception as e:
    print("Login failed:", e)
    # Register if login fails
    reg_data = json.dumps({"email": "ashishfree30@gmail.com", "password": "Password123!", "name": "Ashish"}).encode()
    reg_req = urllib.request.Request(f"{base_url}/auth/register", data=reg_data, headers={"Content-Type": "application/json"})
    res = urllib.request.urlopen(reg_req)
    token = json.loads(res.read().decode())["access_token"]
    print("Registered successfully.")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

# 1. Fetch teams
teams_req = urllib.request.Request(f"{base_url}/enterprise/teams", headers=headers)
try:
    teams = json.loads(urllib.request.urlopen(teams_req).read().decode())
    print("Teams:", teams)
    if teams:
        team_id = teams[0]["id"]
        # 2. Test inviting by email
        invite_data = json.dumps({"email": "testinvite@example.com", "role": "member"}).encode()
        inv_req = urllib.request.Request(f"{base_url}/enterprise/teams/{team_id}/members", data=invite_data, headers=headers)
        try:
            inv_res = urllib.request.urlopen(inv_req)
            print("Invite success:", inv_res.read().decode())
        except urllib.error.HTTPError as he:
            print("Invite error code:", he.code)
            print("Invite error body:", he.read().decode())

        # 3. Test listing members
        mem_req = urllib.request.Request(f"{base_url}/enterprise/teams/{team_id}/members", headers=headers)
        members = json.loads(urllib.request.urlopen(mem_req).read().decode())
        print("Members in team:", members)
except urllib.error.HTTPError as he:
    print("Teams fetch error:", he.code, he.read().decode())
