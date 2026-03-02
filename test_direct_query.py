#!/usr/bin/env python3
"""Try to execute a query directly through Grafana API"""

import requests
import json

print("=" * 70)
print("TESTING DIRECT DATASOURCE QUERY")
print("=" * 70)

# Get datasource
response = requests.get('http://localhost:3000/api/datasources/name/PostgreSQL Warehouse')
ds = response.json()
ds_id = ds['id']

print(f"\nDatasource ID: {ds_id}")
print(f"Datasource UID: {ds.get('uid')}")

# Method 1: Try query endpoint
print("\n1. TRYING /api/datasources/{id}/query")
print("-" * 70)

payload = {
    "queries": [
        {
            "refId": "A",
            "rawSql": "SELECT COUNT(*) as cnt FROM fact_sales LIMIT 1",
            "format": "table"
        }
    ],
    "range": {
        "from": "2024-01-01T00:00:00Z",
        "to": "2024-12-31T23:59:59Z"
    }
}

response = requests.post(
    f"http://localhost:3000/api/datasources/{ds_id}/query",
    json=payload
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")

# Method 2: Try using the render endpoint for metrics
print("\n2. TRYING /api/datasources/{id}/testDatasource")
print("-" * 70)

payload = {
    "name": ds['name'],
    "type": ds['type'],
    "url": ds['url'],
    "database": ds['database'],
    "user": ds['user'],
    "jsonData": ds.get('jsonData', {}),
    "secureJsonData": {
        "password": "123456"
    }
}

response = requests.post(
    f"http://localhost:3000/api/datasources/{ds_id}/testDatasource",
    json=payload
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

# Method 3: Look at what a successful query from a dashboard looks like
print("\n3. CHECKING IF DASHBOARDS HAVE BEEN QUERIED")
print("-" * 70)

response = requests.get('http://localhost:3000/api/dashboards/uid/d8585c53-b4d6-4e3d-af89-520c01744644')
dashboard = response.json()['dashboard']

print(f"Dashboard: {dashboard['title']}")

for panel in dashboard['panels'][:1]:
    print(f"\nPanel: {panel.get('title')}")
    
    # Get the full target
    target = panel.get('targets', [{}])[0]
    print(f"\nFull target config:")
    print(json.dumps(target, indent=2))
