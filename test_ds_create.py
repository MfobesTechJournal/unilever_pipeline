#!/usr/bin/env python3
import requests
import json

response = requests.post(
    "http://localhost:3000/api/datasources",
    json={
        "name": "Test Datasource",
        "type": "postgres",
        "access": "proxy",
        "url": "localhost:5433",
        "database": "unilever_warehouse",
        "user": "postgres",
        "secureJsonData": {
            "password": "123456"
        }
    },
    auth=("admin", "admin")
)

print("Status:", response.status_code)
print("Response:", json.dumps(response.json(), indent=2))
