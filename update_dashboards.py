#!/usr/bin/env python3
"""Update dashboards to use the new PostgreSQL datasource"""

import requests
import json

print("=" * 70)
print("UPDATING DASHBOARDS WITH NEW DATASOURCE")
print("=" * 70)

# Get the correct datasource
print("\n1. Getting datasource info...")
response = requests.get('http://localhost:3000/api/datasources/name/PostgreSQL Warehouse')
if response.status_code == 200:
    datasource = response.json()
    ds_id = datasource['id']
    ds_uid = datasource.get('uid', 'postgres-warehouse')
    print(f"   ✓ Found datasource: {datasource['name']} (ID: {ds_id}, UID: {ds_uid})")
else:
    print(f"   ✗ Could not find datasource: {response.status_code}")
    exit(1)

# Get all dashboards
print("\n2. Updating dashboards...")
response = requests.get('http://localhost:3000/api/search?type=dash-db')
dashboards = response.json()

for dash in dashboards:
    dash_response = requests.get(f"http://localhost:3000/api/dashboards/uid/{dash['uid']}")
    dashboard_data = dash_response.json()
    dashboard = dashboard_data['dashboard']
    
    print(f"\n   Updating: {dashboard['title']}")
    
    # Update all panels to reference the new datasource
    updated = False
    for panel in dashboard.get('panels', []):
        for target in panel.get('targets', []):
            # Update datasource reference
            old_ds = target.get('datasource')
            target['datasource'] = {
                "type": "postgres",
                "uid": ds_uid,
                "name": "PostgreSQL Warehouse"
            }
            if old_ds != target['datasource']:
                updated = True
                print(f"     ✓ Panel '{panel.get('title')}' updated")
    
    # Save the dashboard
    if updated:
        save_response = requests.post(
            f"http://localhost:3000/api/dashboards/db",
            json={
                "dashboard": dashboard,
                "overwrite": True,
                "message": "Updated datasource references"
            }
        )
        
        if save_response.status_code == 200:
            print(f"     ✓ Dashboard saved")
        else:
            print(f"     ✗ Failed to save: {save_response.status_code}")
            print(f"     Error: {save_response.text[:200]}")

print("\n" + "=" * 70)
print("DASHBOARD UPDATE COMPLETE")
print("=" * 70)
print("\n🔄 Refresh your browser to see data in the dashboards!\n")
