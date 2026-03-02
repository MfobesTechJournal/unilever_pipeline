#!/usr/bin/env python3
"""Upload Sales Analytics dashboard via API"""

import requests
import json

sales_file = '11-infrastructure/network/grafana/dashboards/sales-analytics.json'

with open(sales_file, 'r') as f:
    dashboard_json = json.load(f)

print(f"Dashboard title: {dashboard_json.get('title')}")
print(f"Dashboard uid: {dashboard_json.get('uid')}")
print(f"Number of panels: {len(dashboard_json.get('panels', []))}")

# Check first panel
first_panel = dashboard_json['panels'][0]
print(f"\nFirst panel datasource: {first_panel.get('datasource')}")

# Upload as new dashboard or update existing
payload = {
    'dashboard': dashboard_json,
    'overwrite': True,
    'message': 'Updated with datasource references'
}

print(f"\nUploading...")

response = requests.post(
    'http://localhost:3000/api/dashboards/db',
    json=payload,
    headers={'Content-Type': 'application/json'}
)

print(f"Response status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Also try PUT if POST fails
if response.status_code != 200 and response.status_code != 201:
    print(f"\nTrying PUT method...")
    response = requests.put(
        'http://localhost:3000/api/dashboards/db',
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    print(f"PUT Response status: {response.status_code}")
    print(f"Response: {response.text[:300]}")
