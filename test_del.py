from datetime import datetime, timezone
import requests
import json
import jwt 
import params 



payload = {
    "clientToken": params.CLIENT_BM,
    "clientKey": params.TOKEN_BM,
    "userToken": params.USER_BM
}

# Génération du JWT (HS256 par défaut)
jwt_header_value = jwt.encode(payload, params.TOKEN_BM, algorithm="HS256")
url = "https://ui.boondmanager.com/api/opportunities"
headers = {
    "X-Jwt-Client-BoondManager": jwt_header_value,
    "Accept": "application/json"
}


response = requests.get(url=url, headers=headers)
print(f"Status Code: {response.status_code}")
if response.headers.get("Content-Type", "").startswith("application/json"):
    data = response.json()
else:
    print("Server did NOT return JSON!")
    print(response.text[:500])

if response.status_code == 200:
    try:
        data = response.json()
        filtered = []
        for item in data.get("data", []):
            upd = item["attributes"]["updateDate"]
            upd_dt = datetime.fromisoformat(upd.replace("Z", "+00:00"))
            state = item["attributes"]["state"]
            if upd_dt > datetime(2025, 11, 17, tzinfo=timezone.utc):
                filtered.append(item)
        print(json.dumps(filtered, indent=4, ensure_ascii=False))
    except ValueError as e:  
        print(f"JSON Decode Error: {e}")
else:
    print(f"API Error: {response.status_code}")
    
