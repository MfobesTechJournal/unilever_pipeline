import os
#!/usr/bin/env python3
"""
Deploy Sales Analytics Dashboard to Grafana Cloud
Fixed version to handle dashboard upload properly
"""

import requests
import json

GRAFANA_CLOUD_URL = "https://mfobestechjournal.grafana.net"
API_TOKEN = "os.environ.get("GRAFANA_TOKEN", "")_ebe31527"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

print("\n" + "="*80)
print("UPLOADING SALES ANALYTICS DASHBOARD")
print("="*80)

try:
    # Load the dashboard
    print("\n[1] Loading Sales Analytics dashboard...")
    with open("11-infrastructure/network/grafana/dashboards/sales-analytics.json", 'r') as f:
        dashboard_json = json.load(f)
    
    # Clean up dashboard for cloud upload
    # Remove ID if it exists (cloud will assign its own)
    if 'id' in dashboard_json:
        del dashboard_json['id']
    
    # Ensure it has a UID
    dashboard_json['uid'] = 'sales-analytics-unilever'
    
    print(f"✓ Dashboard loaded: {dashboard_json.get('title')}")
    print(f"  UID: {dashboard_json.get('uid')}")
    print(f"  Panels: {len(dashboard_json.get('panels', []))}")
    
    # Prepare payload
    dashboard_payload = {
        "dashboard": dashboard_json,
        "overwrite": True
    }
    
    print("\n[2] Uploading to Grafana Cloud...")
    response = requests.post(
        f"{GRAFANA_CLOUD_URL}/api/dashboards/db",
        headers=headers,
        json=dashboard_payload,
        timeout=10
    )
    
    print(f"  Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        result = response.json()
        dashboard_id = result.get('id')
        dashboard_url = result.get('url', '')
        print(f"\n✓ SUCCESS!")
        print(f"  Dashboard ID: {dashboard_id}")
        print(f"  URL: {GRAFANA_CLOUD_URL}{dashboard_url}")
        print(f"\nAccess at: {GRAFANA_CLOUD_URL}{dashboard_url}")
    else:
        print(f"✗ Failed: {response.status_code}")
        print(f"  Message: {response.text}")

except FileNotFoundError:
    print("✗ File not found: 11-infrastructure/network/grafana/dashboards/sales-analytics.json")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "="*80 + "\n")
