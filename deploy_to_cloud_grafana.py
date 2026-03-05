#!/usr/bin/env python3
"""
Deploy Dashboards to Grafana Cloud
Uploads both Sales Analytics and ETL Monitoring dashboards with fixed queries
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GRAFANA_CLOUD_URL = os.getenv("GRAFANA_CLOUD_URL")
API_TOKEN = os.getenv("GRAFANA_API_TOKEN")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

if not API_TOKEN:
    raise ValueError("Missing GRAFANA_API_TOKEN environment variable")

# Setup headers
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

print("\n" + "="*80)
print("GRAFANA CLOUD DEPLOYMENT")
print("="*80)

# Step 1: Test Connection
print("\n[STEP 1] Testing Grafana Cloud Connection...")
try:
    response = requests.get(f"{GRAFANA_CLOUD_URL}/api/health", headers=headers, timeout=10)
    if response.status_code == 200:
        print("✓ Successfully connected to Grafana Cloud")
    else:
        print(f"✗ Connection failed: {response.status_code}")
        print(f"  Response: {response.text}")
        exit(1)
except Exception as e:
    print(f"✗ Failed to connect: {e}")
    exit(1)

# Step 2: Fix PostgreSQL Datasource
print("\n[STEP 2] Configuring PostgreSQL Datasource...")
try:
    ds_response = requests.get(f"{GRAFANA_CLOUD_URL}/api/datasources", headers=headers, timeout=10)
    datasources = ds_response.json()

    pg_ds = None
    for ds in datasources:
        if 'postgres' in ds.get('type', '').lower():
            pg_ds = ds
            print(f"✓ Found PostgreSQL datasource: {ds.get('name')} (ID: {ds.get('id')})")
            break

    if not pg_ds:
        print("ℹ No PostgreSQL datasource found, will need to create one")
    else:
        ds_id = pg_ds['id']

        update_payload = {
            "name": "PostgreSQL Warehouse",
            "type": "postgres",
            "url": "localhost:5433",
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
                "password": POSTGRES_PASSWORD
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
            print("✓ PostgreSQL datasource updated")
        else:
            print(f"✗ Failed to update datasource: {update_response.status_code}")
            print(f"  Response: {update_response.text}")

except Exception as e:
    print(f"✗ Error managing datasource: {e}")

# Step 3: Upload Sales Analytics Dashboard
print("\n[STEP 3] Uploading Sales Analytics Dashboard...")
try:
    with open("11-infrastructure/network/grafana/dashboards/sales-analytics.json", 'r') as f:
        dashboard_json = json.load(f)

    dashboard_payload = {
        "dashboard": dashboard_json,
        "overwrite": True
    }

    response = requests.post(
        f"{GRAFANA_CLOUD_URL}/api/dashboards/db",
        headers=headers,
        json=dashboard_payload,
        timeout=10
    )

    if response.status_code in [200, 201]:
        result = response.json()
        dashboard_id = result.get('id')
        dashboard_url = result.get('url', '')
        print(f"✓ Sales Analytics dashboard uploaded (ID: {dashboard_id})")
        print(f"  URL: {GRAFANA_CLOUD_URL}{dashboard_url}")
    else:
        print(f"✗ Failed to upload dashboard: {response.status_code}")
        print(f"  Response: {response.text}")

except FileNotFoundError:
    print("✗ Sales Analytics dashboard file not found")
except Exception as e:
    print(f"✗ Error uploading dashboard: {e}")

# Step 4: Upload ETL Monitoring Dashboard
print("\n[STEP 4] Uploading ETL Monitoring Dashboard...")
try:
    with open("08-monitoring-alerting/grafana/dashboards/etl-monitoring.json", 'r') as f:
        dashboard_json = json.load(f)

    dashboard_payload = {
        "dashboard": dashboard_json,
        "overwrite": True
    }

    response = requests.post(
        f"{GRAFANA_CLOUD_URL}/api/dashboards/db",
        headers=headers,
        json=dashboard_payload,
        timeout=10
    )

    if response.status_code in [200, 201]:
        result = response.json()
        dashboard_id = result.get('id')
        dashboard_url = result.get('url', '')
        print(f"✓ ETL Monitoring dashboard uploaded (ID: {dashboard_id})")
        print(f"  URL: {GRAFANA_CLOUD_URL}{dashboard_url}")
    else:
        print(f"✗ Failed to upload dashboard: {response.status_code}")
        print(f"  Response: {response.text}")

except FileNotFoundError:
    print("✗ ETL Monitoring dashboard file not found")
except Exception as e:
    print(f"✗ Error uploading dashboard: {e}")

print("\n" + "="*80)
print("DEPLOYMENT COMPLETE")
print("="*80)
print(f"\nAccess dashboards at: {GRAFANA_CLOUD_URL}")