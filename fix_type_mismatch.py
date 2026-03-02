#!/usr/bin/env python3
"""Fix datasource type mismatch in panels"""

import requests
import json

print("=" * 70)
print("FIXING DATASOURCE TYPE MISMATCH")
print("=" * 70)

# Get datasource
response = requests.get('http://localhost:3000/api/datasources/name/PostgreSQL Warehouse')
ds = response.json()

print(f"\nDatasource Type: {ds['type']}")  # grafana-postgresql-datasource
print(f"Datasource UID: {ds.get('uid')}")

# Get all dashboards and fix panel datasource types
response = requests.get('http://localhost:3000/api/search?type=dash-db')
dashboards = response.json()

for dash in dashboards:
    dash_response = requests.get(f"http://localhost:3000/api/dashboards/uid/{dash['uid']}")
    dashboard_data = dash_response.json()
    dashboard = dashboard_data['dashboard']
    
    print(f"\n Processing Dashboard: {dashboard['title']}")
    modified = False
    
    for panel in dashboard.get('panels', []):
        for target in panel.get('targets', []):
            ds_ref = target.get('datasource', {})
            
            if isinstance(ds_ref, dict):
                old_type = ds_ref.get('type')
                new_type = ds['type']  # Use the actual datasource type
                
                if old_type != new_type:
                    print(f"  Panel '{panel.get('title')}': changing type '{old_type}' -> '{new_type}'")
                    ds_ref['type'] = new_type
                    modified = True
    
    # Save if modified
    if modified:
        save_response = requests.post(
            f"http://localhost:3000/api/dashboards/db",
            json={
                "dashboard": dashboard,
                "overwrite": True,
                "message": "Fixed datasource type references"
            }
        )
        
        if save_response.status_code == 200:
            print(f"  ✓ Dashboard saved successfully")
        else:
            print(f"  ✗ Failed to save: {save_response.status_code}")
            print(f"  Error: {save_response.text[:200]}")

print("\n" + "=" * 70)
print("✓ DATASOURCE TYPES FIXED")
print("=" * 70)
print("\n🔄 Hard refresh your Grafana browser tab (Shift+F5)")
print("\n")
