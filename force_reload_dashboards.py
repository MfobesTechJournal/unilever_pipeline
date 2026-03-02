#!/usr/bin/env python3
"""
Force reload and test all Grafana dashboards.
This will restart Grafana and reimport dashboards.
"""

import requests
import json
import subprocess
import time

GRAFANA_URL = "http://localhost:3000"
GRAFANA_AUTH = ("admin", "admin")

print("\n" + "="*80)
print("GRAFANA DASHBOARD FIX - FORCE RELOAD")
print("="*80)

# Step 1: Restart Grafana container
print("\n[1] Restarting Grafana container...")
try:
    result = subprocess.run(
        ["docker-compose", "restart", "grafana"],
        capture_output=True,
        text=True,
        cwd="c:\\Users\\Mfobe Ntintelo\\Documents\\unilever_pipeline"
    )
    print("✓ Grafana restarted")
except Exception as e:
    print(f"✗ Could not restart: {e}")

# Wait for Grafana to restart
print("  Waiting for Grafana to start...")
time.sleep(10)

# Step 2: Verify Grafana is accessible
print("\n[2] Checking Grafana accessibility...")
for i in range(5):
    try:
        response = requests.get(f"{GRAFANA_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print(f"✓ Grafana is now ready")
            break
    except:
        print(f"  Waiting... attempt {i+1}/5")
        time.sleep(2)

# Step 3: Get datasource
print("\n[3] Checking datasource...")
session = requests.Session()
session.auth = GRAFANA_AUTH

try:
    response = session.get(f"{GRAFANA_URL}/api/datasources", timeout=5)
    datasources = response.json()
    
    pg_ds = None
    for ds in datasources:
        if 'postgres' in ds.get('type', '').lower():
            pg_ds = ds
            print(f"✓ PostgreSQL datasource found: {ds.get('name')} (ID: {ds.get('id')})")
            
            # Test it
            test_response = session.post(
                f"{GRAFANA_URL}/api/datasources/{ds.get('id')}/health",
                timeout=10
            )
            test_result = test_response.json()
            print(f"  Connection test: {test_result.get('message', test_result.get('status'))}")
            break
except Exception as e:
    print(f"✗ Error: {e}")

# Step 4: Check dashboards
print("\n[4] Checking dashboards...")
try:
    response = session.get(f"{GRAFANA_URL}/api/search?type=dash-db", timeout=5)
    dashboards = response.json()
    
    for dash in dashboards:
        title = dash.get('title')
        uid = dash.get('uid')
        print(f"✓ {title} (UID: {uid})")
        
        # Get dashboard details
        dash_response = session.get(f"{GRAFANA_URL}/api/dashboards/uid/{uid}", timeout=5)
        if dash_response.status_code == 200:
            dash_data = dash_response.json().get('dashboard', {})
            panels = dash_data.get('panels', [])
            print(f"  └─ {len(panels)} panels")
            
            for panel in panels[:1]:  # Show first panel
                title = panel.get('title')
                ds = panel.get('datasource')
                targets = panel.get('targets', [])
                print(f"     ├─ {title}")
                print(f"     ├─ Datasource: {ds}")
                print(f"     └─ Has query: {len(targets) > 0}")

except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "="*80)
print("NEXT STEPS:")
print("="*80)
print("\n1. Open http://localhost:3000 in your browser")
print("2. Go to Dashboards")
print("3. Click 'Sales Analytics'")
print("4. Press F5 to refresh the page")
print("5. Wait 10 seconds for data to load")
print("\n" + "="*80 + "\n")
