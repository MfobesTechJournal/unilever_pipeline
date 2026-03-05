#!/usr/bin/env python3
"""
Reset Grafana and recreate everything properly
"""

import subprocess
import time
import requests
import json

GRAFANA_URL = "http://localhost:3000"

print("\n" + "="*80)
print("RESETTING GRAFANA")
print("="*80)

# Stop and remove old container
print("\n[1] Stopping old Grafana container...")
try:
    subprocess.run(['docker', 'stop', 'unilever-grafana'], timeout=10)
    subprocess.run(['docker', 'rm', 'unilever-grafana'], timeout=10)
    print("✓ Old container removed")
except Exception as e:
    print(f"✓ Container not found (OK)")

time.sleep(2)

# Start fresh Grafana with default password
print("\n[2] Starting fresh Grafana container...")
try:
    subprocess.Popen([
        'docker', 'run', '-d',
        '--name', 'unilever-grafana',
        '-p', '3000:3000',
        '-e', 'GF_SECURITY_ADMIN_USER=admin',
        '-e', 'GF_SECURITY_ADMIN_PASSWORD=admin',
        '-e', 'GF_SERVER_ROOT_URL=http://localhost:3000',
        'grafana/grafana:latest'
    ])
    print("✓ Container started")
except Exception as e:
    print(f"Error: {e}")

# Wait for Grafana to be ready
print("\n[3] Waiting for Grafana to be ready...")
for attempt in range(60):
    try:
        response = requests.get(f"{GRAFANA_URL}/api/health", timeout=2)
        if response.status_code == 200:
            print("✓ Grafana is ready!")
            break
    except:
        if attempt % 10 == 0:
            print(f"  Waiting... ({attempt}s)")
        time.sleep(1)

# Wait for API
print("\n[4] Waiting for API...")
time.sleep(3)

# Test auth with correct credentials
print("\n[5] Testing authentication...")
response = requests.get(f"{GRAFANA_URL}/api/datasources", auth=("admin", "admin"))
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✓ Authentication successful!")
else:
    print(f"✗ Auth failed: {response.text[:200]}")

# Create datasource
print("\n[6] Creating PostgreSQL datasource...")
try:
    datasource_config = {
        "name": "PostgreSQL Warehouse",
        "type": "postgres",
        "access": "proxy",
        "url": "host.docker.internal:5433",  # For Docker on Windows
        "database": "unilever_warehouse",
        "user": "postgres",
        "secureJsonData": {
            "password": "123456"
        },
        "jsonData": {
            "sslmode": "disable",
            "postgresVersion": 15
        },
        "isDefault": True
    }
    
    response = requests.post(
        f"{GRAFANA_URL}/api/datasources",
        json=datasource_config,
        auth=("admin", "admin")
    )
    
    if response.status_code in [200, 201]:
        ds_info = response.json().get('datasource', response.json())
        ds_id = ds_info['id']
        ds_uid = ds_info['uid']
        print(f"✓ Datasource created!")
        print(f"  ID: {ds_id}")
        print(f"  UID: {ds_uid}")
    else:
        print(f"✗ Error: {response.text}")
        exit(1)
        
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

# Test datasource
print("\n[7] Testing datasource connection...")
try:
    response = requests.post(
        f"{GRAFANA_URL}/api/ds/query",
        json={
            "queries": [{
                "refId": "A",
                "rawSql": "SELECT COUNT(*) as value FROM fact_sales",
                "datasourceUid": ds_uid
            }]
        },
        auth=("admin", "admin")
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✓ Datasource is working!")
        result = response.json()
        print(f"  Result: {json.dumps(result, indent=2)[:300]}")
    else:
        print(f"Response: {response.text[:300]}")
        
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "="*80)
print("✓ GRAFANA RESET COMPLETE")
print("="*80)
print("\nNext: Run dashboard creation script")
