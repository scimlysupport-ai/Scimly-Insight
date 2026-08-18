import urllib.request
import urllib.error
import json

base_url = "https://scimly-insight.onrender.com/api"

# Login
login_data = json.dumps({"email": "ashishfree30@gmail.com", "password": "Password123!"}).encode()
login_req = urllib.request.Request(f"{base_url}/auth/login", data=login_data, headers={"Content-Type": "application/json"})

try:
    res = urllib.request.urlopen(login_req)
    token = json.loads(res.read().decode())["access_token"]
    print("LOGGED IN:", token[:20])
except Exception as e:
    print("Login err:", e)

headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

# Create a test team
create_team_data = json.dumps({"name": "blackrock_test", "description": "test"}).encode()
team_req = urllib.request.Request(f"{base_url}/enterprise/teams", data=create_team_data, headers=headers)
try:
    team_res = urllib.request.urlopen(team_req)
    team = json.loads(team_res.read().decode())
    print("CREATED TEAM:", team)
    team_id = team["id"]
except urllib.error.HTTPError as e:
    print("Create team error:", e.code, e.read().decode())
    # fetch existing
    teams = json.loads(urllib.request.urlopen(urllib.request.Request(f"{base_url}/enterprise/teams", headers=headers)).read().decode())
    team_id = teams[0]["id"]
    print("USING EXISTING TEAM:", team_id)

# Test invite by email
invite_payload = json.dumps({"user_id": None, "email": "newteammate@company.com", "role": "member"}).encode()
inv_req = urllib.request.Request(f"{base_url}/enterprise/teams/{team_id}/members", data=invite_payload, headers=headers)
try:
    inv_res = urllib.request.urlopen(inv_req)
    print("INVITE SUCCESS:", inv_res.read().decode())
except urllib.error.HTTPError as e:
    print("INVITE FAIL:", e.code, e.read().decode())

# List team members
members = json.loads(urllib.request.urlopen(urllib.request.Request(f"{base_url}/enterprise/teams/{team_id}/members", headers=headers)).read().decode())
print("TEAM MEMBERS:", members)

# Remove the invited member
if len(members) > 1:
    target_user_id = members[1]["user_id"]
    del_req = urllib.request.Request(f"{base_url}/enterprise/teams/{team_id}/members/{target_user_id}", headers=headers, method="DELETE")
    try:
        del_res = urllib.request.urlopen(del_req)
        print("DELETE SUCCESS:", del_res.read().decode())
    except urllib.error.HTTPError as e:
        print("DELETE FAIL:", e.code, e.read().decode())
