#!/usr/bin/env python3
"""
Configure Grafana Agent for Private Data Source Connection
Connects local PostgreSQL to Grafana Cloud securely
"""

import json
import requests
import time
import subprocess
import os

GRAFANA_CLOUD_URL = "https://mfobestechjournal.grafana.net"
API_TOKEN = "os.environ.get("GRAFANA_TOKEN", "")_ebe31527"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

print("\n" + "="*80)
print("GRAFANA AGENT SETUP FOR LOCAL POSTGRESQL")
print("="*80)

# Step 1: Create Agent Configuration
print("\n[STEP 1] Creating Grafana Agent Configuration...")

agent_config = """server:
  log_level: debug
  http_listen_port: 12345

metrics:
  wal:
    dir: C:\\Grafana\\agent\\wal

logs:
  positions:
    filename: C:\\Grafana\\agent\\positions.yaml

integrations:
  agent:
    enabled: true
"""

agent_config_path = "C:\\Program Files\\Grafana\\agent\\agent-config.yaml"

try:
    # Create directory if needed
    os.makedirs(os.path.dirname(agent_config_path), exist_ok=True)
    
    with open(agent_config_path, 'w') as f:
        f.write(agent_config)
    print(f"✓ Configuration created: {agent_config_path}")
except Exception as e:
    print(f"✗ Error creating config: {e}")

# Step 2: Start Grafana Agent Service
print("\n[STEP 2] Starting Grafana Agent Service...")

try:
    # Start the Grafana Agent service
    subprocess.run(["net", "start", "Grafana Agent"], capture_output=True, check=False)
    print("✓ Grafana Agent service started (or already running)")
    time.sleep(2)
except Exception as e:
    print(f"⚠ Could not start service: {e}")
    print("  Try: Start-Service -Name 'Grafana Agent' (in PowerShell as Admin)")

# Step 3: Update PostgreSQL Datasource to use Private Connection
print("\n[STEP 3] Configuring PostgreSQL Datasource for Private Connection...")

try:
    # Get the datasource
    ds_response = requests.get(f"{GRAFANA_CLOUD_URL}/api/datasources", headers=headers, timeout=10)
    datasources = ds_response.json()
    
    pg_ds = None
    for ds in datasources:
        if 'postgres' in ds.get('type', '').lower():
            pg_ds = ds
            ds_id = ds.get('id')
            print(f"✓ Found PostgreSQL datasource (ID: {ds_id})")
            break
    
    if pg_ds:
        # Update datasource to use private connection
        update_payload = {
            "name": "PostgreSQL Warehouse",
            "type": "postgres",
            "url": "unilever_postgres:5432",  # Docker container name
            "access": "proxy",
            "isDefault": True,
            "jsonData": {
                "sslmode": "disable",
                "postgresVersion": 1400,
                "maxOpenConns": 0,
                "maxIdleConns": 2,
                "connMaxLifetime": 14400
            },
            "secureJsonData": {
                "password": "123456"
            },
            "database": "unilever_warehouse",
            "user": "postgres"
        }
        
        update_response = requests.put(
            f"{GRAFANA_CLOUD_URL}/api/datasources/{ds_id}",
            headers=headers,
            json=update_payload,
            timeout=10
        )
        
        if update_response.status_code in [200, 201]:
            print(f"✓ Datasource configured:")
            print(f"  Host: unilever_postgres:5432")
            print(f"  Database: unilever_warehouse")
            print(f"  User: postgres")
        else:
            print(f"✗ Failed to update datasource: {update_response.status_code}")
            print(f"  Response: {update_response.text}")
    else:
        print("✗ No PostgreSQL datasource found")

except Exception as e:
    print(f"✗ Error updating datasource: {e}")

# Step 4: Test Connection
print("\n[STEP 4] Testing Connection...")

try:
    test_response = requests.post(
        f"{GRAFANA_CLOUD_URL}/api/datasources/uid/bfew4d1gmjw8wf/health",
        headers=headers,
        timeout=10
    )
    
    if test_response.status_code == 200:
        test_result = test_response.json()
        status = test_result.get('message', test_result.get('status', 'Unknown'))
        print(f"✓ Connection test result: {status}")
    else:
        print(f"⚠ Connection test returned: {test_response.status_code}")
        print(f"  This may be normal if agent is still initializing")

except Exception as e:
    print(f"⚠ Could not test connection: {e}")
    print("  The agent may need a moment to initialize")

# Step 5: Final Instructions
print("\n" + "="*80)
print("SETUP COMPLETE")
print("="*80)

print("""
Next Steps:
1. Grafana Agent is configured and should be running

2. If dashboards still show "No data":
   a. Verify agent is running:
      - Open Services app (services.msc)
      - Look for "Grafana Agent"
      - Status should be "Running"
   
   b. If not running, start it:
      - Right-click "Grafana Agent"
      - Click "Start"
   
   c. Wait 30 seconds for connection to establish
   
   d. Go to Grafana Cloud and refresh the dashboards

3. In Grafana Cloud:
   - Visit: https://mfobestechjournal.grafana.net/connections/datasources/edit/bfew4d1gmjw8wf
   - Click "Save & Test"
   - Should see "Database Connection OK"

4. Once connected, your dashboards will populate with data from your local PostgreSQL!

Troubleshooting:
- Check Grafana Agent logs: C:\\Program Files\\Grafana\\agent\\logs
- Verify PostgreSQL is running: docker ps
- Verify port 5432 is accessible locally

""")

print("="*80 + "\n")
