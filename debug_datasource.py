#!/usr/bin/env python3
import requests
import json

GRAFANA_URL = "http://localhost:3000"
GRAFANA_AUTH = ("admin", "admin")

response = requests.get(f"{GRAFANA_URL}/api/datasources", auth=GRAFANA_AUTH)
print("Status:", response.status_code)
print("Response Type:", type(response.json()))
print("Response:", json.dumps(response.json(), indent=2)[:1000])
