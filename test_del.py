import requests
import json
import jwt
import params

# ---------------------
# Authentification JWT
# ---------------------
payload = {
    "clientToken": params.CLIENT_BM,
    "clientKey": params.TOKEN_BM,
    "userToken": params.USER_BM
}

jwt_header_value = jwt.encode(payload, params.TOKEN_BM, algorithm="HS256")

url = "https://ui.boondmanager.com/api/opportunities"

headers = {
    "X-Jwt-Client-BoondManager": jwt_header_value,
    "Accept": "application/json"
}

# ---------------------
# Requête API
# ---------------------
response = requests.get(url=url, headers=headers)

print(f"Status Code: {response.status_code}")

# Check JSON
if not response.headers.get("Content-Type", "").startswith("application/json"):
    print("Server did NOT return JSON!")
    print(response.text[:500])
    exit()

data = response.json()

# ---------------------
# Champs à filtrer
# ---------------------
fields = [
    "creationDate",
    "title",
    "company",
    "state",
    "numberOfActivePositionings",
    "place",
    "startDate",
    "duration",
    "turnoverWeightedExcludingTax",
    "mainManager",
    "turnoverEstimatedExcludingTax",
    "estimatesExcludingTax",
    "closingDate",
    "answerDate",
    "activityAreas",
    "expertiseArea",
    "tools",
    "origin",
    "hrManager",
    "pole",
    "agency",
    "updateDate",
]

# ---------------------
# Filtrage + affichage
# ---------------------
print("\n=== OPPORTUNITES AVEC state = 0 ===\n")

for item in data.get("data", []):
    attrs = item.get("attributes", {})

    if attrs.get("state") == 0:
        print("------ OPPORTUNITY ------")
        for f in fields:
            print(f"{f}: {attrs.get(f)}")
        print("-------------------------\n")
