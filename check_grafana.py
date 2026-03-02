#!/usr/bin/env python3
"""Deep diagnostic of datasource connectivity"""

import requests
import json

print("=" * 70)
print("DEEP DATASOURCE DIAGNOSTIC")
print("=" * 70)

# Get datasource details
print("\n1. DATASOURCE CONFIGURATION")
print("-" * 70)

response = requests.get('http://localhost:3000/api/datasources/name/PostgreSQL Warehouse')
ds = response.json()

print(f"Datasource: {ds['name']}")
print(f"Type: {ds['type']}")
print(f"URL: {ds['url']}")
print(f"Database: {ds['database']}")
print(f"User: {ds['user']}")
print(f"ID: {ds['id']}")
print(f"UID: {ds.get('uid', 'N/A')}")
print(f"Access: {ds.get('access', 'N/A')}")

# Check if password is set
has_password = ds.get('secureJsonFields', {}).get('password', False)
print(f"Password set: {has_password}")

if not has_password:
    print("\n⚠️  WARNING: Password not saved!")

# Get a dashboard and check panel datasource references
print("\n2. PANEL DATASOURCE REFERENCES")
print("-" * 70)

response = requests.get('http://localhost:3000/api/search?type=dash-db')
dashboards = response.json()

for dash in dashboards[:1]:  # Just check first dashboard
    dash_response = requests.get(f"http://localhost:3000/api/dashboards/uid/{dash['uid']}")
    dashboard = dash_response.json()['dashboard']
    
    print(f"Dashboard: {dashboard['title']}")
    
    for panel in dashboard.get('panels', [])[:1]:  # Just first panel
        print(f"Panel: {panel.get('title')}")
        
        targets = panel.get('targets', [])
        for target in targets:
            print(f"\nTarget datasource:")
            ds_ref = target.get('datasource')
            print(json.dumps(ds_ref, indent=2))
            
            if isinstance(ds_ref, dict):
                ref_uid = ds_ref.get('uid')
                ref_name = ds_ref.get('name')
                print(f"\nDatasource UID in target: {ref_uid}")
                print(f"Datasource Name in target: {ref_name}")
                print(f"Current datasource UID: {ds.get('uid')}")
                print(f"Current datasource Name: {ds.get('name')}")
                
                if ref_uid != ds.get('uid'):
                    print("\n⚠️  MISMATCH: UIDs don't match!")
                if ref_name != ds.get('name'):
                    print("⚠️  MISMATCH: Names don't match!")

print("\n" + "=" * 70)

