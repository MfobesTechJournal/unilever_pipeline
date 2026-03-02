#!/usr/bin/env python3
"""Diagnose Grafana datasource connectivity issues"""

import requests
import json

print("=" * 70)
print("GRAFANA DATASOURCE DIAGNOSTIC")
print("=" * 70)

# 1. Get datasources
print("\n1. CHECKING DATASOURCES")
print("-" * 70)

response = requests.get('http://localhost:3000/api/datasources')
datasources = response.json()

print(f"Found {len(datasources)} datasource(s):\n")

for ds in datasources:
    print(f"   • {ds['name']}")
    print(f"     Type: {ds['type']}")
    print(f"     URL: {ds.get('url', 'N/A')}")
    print(f"     Database: {ds.get('database', 'N/A')}")
    
    # Test datasource
    test_response = requests.post(
        f"http://localhost:3000/api/datasources/{ds['id']}/query",
        json={
            "queries": [
                {
                    "refId": "A",
                    "rawSql": "SELECT 1 as test"
                }
            ]
        }
    )
    
    if test_response.status_code == 200:
        print(f"     ✓ Connection test: PASSED")
    else:
        print(f"     ✗ Connection test: FAILED ({test_response.status_code})")
        print(f"     Error: {test_response.text[:200]}")
    print()

# 2. Get dashboards and check panel queries
print("\n2. CHECKING DASHBOARD PANELS")
print("-" * 70)

response = requests.get('http://localhost:3000/api/search?type=dash-db')
dashboards = response.json()

for dash in dashboards:
    dash_response = requests.get(f"http://localhost:3000/api/dashboards/uid/{dash['uid']}")
    dashboard = dash_response.json()['dashboard']
    
    print(f"\nDashboard: {dashboard['title']}")
    
    for panel in dashboard.get('panels', []):
        print(f"  Panel: {panel.get('title', 'Untitled')}")
        
        targets = panel.get('targets', [])
        for target in targets:
            query = target.get('rawSql', target.get('expr', 'No query found'))
            print(f"    Query: {query[:80]}...")
            
            # Extract datasource
            ds_name = target.get('datasource', {})
            if isinstance(ds_name, dict):
                ds_name = ds_name.get('name', 'Unknown')
            
            print(f"    Datasource: {ds_name}")

print("\n" + "=" * 70)
print("END DIAGNOSTIC")
print("=" * 70)
