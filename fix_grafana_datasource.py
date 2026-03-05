#!/usr/bin/env python3
"""
Fix Grafana datasource and dashboard queries
"""

import requests
import json

GRAFANA_URL = "http://localhost:3000"
GRAFANA_AUTH = ("admin", "admin")

print("\n" + "="*80)
print("FIXING GRAFANA DATASOURCE AND DASHBOARDS")
print("="*80)

# Step 1: Check datasources
print("\n[1] CHECKING DATASOURCES")
print("-" * 80)

try:
    response = requests.get(f"{GRAFANA_URL}/api/datasources", auth=GRAFANA_AUTH)
    datasources = response.json()
    
    print(f"Found {len(datasources)} datasource(s):")
    
    postgres_ds = None
    for ds in datasources:
        print(f"  - {ds.get('name')} ({ds.get('type')})")
        if 'postgres' in ds.get('type', '').lower():
            postgres_ds = ds
    
    if not postgres_ds:
        print("\n✗ No PostgreSQL datasource found!")
        exit(1)
    
    print(f"\n✓ PostgreSQL datasource ID: {postgres_ds['id']}")
    print(f"  UID: {postgres_ds['uid']}")
    print(f"  URL: {postgres_ds['url']}")
    print(f"  Database: {postgres_ds['database']}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

# Step 2: Test datasource connection
print("\n[2] TESTING DATASOURCE CONNECTION")
print("-" * 80)

try:
    test_payload = {
        "queries": [
            {
                "refId": "A",
                "rawSql": "SELECT 1",
                "datasourceUid": postgres_ds['uid']
            }
        ]
    }
    
    response = requests.post(
        f"{GRAFANA_URL}/api/ds/query",
        json=test_payload,
        auth=GRAFANA_AUTH
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    
    if response.status_code == 200:
        print("\n✓ Datasource connection is working!")
    else:
        print("\n⚠ Datasource connection issue detected")
        
except Exception as e:
    print(f"Error: {e}")

# Step 3: Get all dashboards and fix them
print("\n[3] FIXING DASHBOARDS")
print("-" * 80)

try:
    response = requests.get(f"{GRAFANA_URL}/api/search?type=dash-db", auth=GRAFANA_AUTH)
    dashboards = response.json()
    
    print(f"Found {len(dashboards)} dashboard(s)")
    
    for dashboard_info in dashboards:
        dashboard_id = dashboard_info['id']
        dashboard_title = dashboard_info['title']
        
        print(f"\n[{dashboard_title}]")
        
        # Get full dashboard
        response = requests.get(
            f"{GRAFANA_URL}/api/dashboards/id/{dashboard_id}",
            auth=GRAFANA_AUTH
        )
        
        data = response.json()
        dashboard = data['dashboard']
        
        # Fix all panels
        panels_fixed = 0
        for panel in dashboard.get('panels', []):
            for target in panel.get('targets', []):
                # Make sure datasourceUid is set
                if 'datasourceUid' not in target or not target['datasourceUid']:
                    target['datasourceUid'] = postgres_ds['uid']
                    panels_fixed += 1
                    print(f"  ✓ Fixed: {panel.get('title')}")
        
        # Save dashboard
        if panels_fixed > 0:
            dashboard['version'] = dashboard.get('version', 1) + 1
            
            response = requests.post(
                f"{GRAFANA_URL}/api/dashboards/db",
                json={"dashboard": dashboard, "overwrite": True},
                auth=GRAFANA_AUTH
            )
            
            if response.status_code in [200, 201]:
                print(f"  ✓ Dashboard saved!")
            else:
                print(f"  ✗ Error saving: {response.text[:200]}")
        else:
            print(f"  (No panels needed fixing)")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Step 4: Verify with actual queries
print("\n[4] VERIFYING WITH ACTUAL QUERIES")
print("-" * 80)

test_queries = {
    "Total ETL Runs": "SELECT COUNT(*) as value FROM etl_log",
    "Total Sales": "SELECT SUM(revenue) as value FROM fact_sales",
    "Total Records": "SELECT COUNT(*) as value FROM fact_sales",
}

try:
    for query_name, query_text in test_queries.items():
        payload = {
            "queries": [
                {
                    "refId": "A",
                    "rawSql": query_text,
                    "datasourceUid": postgres_ds['uid'],
                    "format": "table"
                }
            ]
        }
        
        response = requests.post(
            f"{GRAFANA_URL}/api/ds/query",
            json=payload,
            auth=GRAFANA_AUTH
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ {query_name}")
        else:
            print(f"✗ {query_name}: {response.status_code}")
            
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80)
print("✓ GRAFANA FIX COMPLETE")
print("="*80)
print("\nNext steps:")
print("  1. Refresh your browser (Ctrl+F5)")
print("  2. Go back to your dashboards")
print("  3. Click 'Refresh' button")
print("  4. Data should now appear!")
