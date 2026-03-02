#!/usr/bin/env python3
"""
Create simple, working Grafana dashboards with minimal configuration
"""

import requests
import json

GRAFANA_URL = "http://localhost:3000"
session = requests.Session()
session.auth = ("admin", "admin")

print("\n" + "="*80)
print("CREATING MINIMAL WORKING DASHBOARDS")
print("="*80)

# First, delete existing dashboards
print("\n[1] Deleting existing dashboards...")
for uid in ["09bb3434-c1a1-4d3e-8d62-d3392e569d89", "424b5744-27f0-4675-a03d-ae47b2b7d847"]:
    try:
        session.delete(f"{GRAFANA_URL}/api/dashboards/uid/{uid}")
        print(f"  ✓ Deleted")
    except:
        pass

# Simple Sales Analytics Dashboard - MINIMAL CONFIGURATION
SALES_SIMPLE = {
    "dashboard": {
        "uid": "sales-analytics",
        "title": "Sales Analytics",
        "tags": ["sales"],
        "timezone": "browser",
        "panels": [
            {
                "id": 1,
                "title": "Total Sales Revenue",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                "cacheLevel": "StandardVariablesCacheLevel",
                "datasource": "PostgreSQL Warehouse",
                "targets": [{
                    "refId": "A",
                    "rawSql": "SELECT SUM(revenue) as value FROM fact_sales"
                }],
                "fieldConfig": {
                    "defaults": {
                        "unit": "currencyUSD",
                        "color": {"mode": "thresholds"},
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [{"color": "green", "value": None}]
                        }
                    }
                }
            }
        ]
    }
}

print("\n[2] Creating Sales Analytics Dashboard (minimal)...")
try:
    response = session.post(f"{GRAFANA_URL}/api/dashboards/db", json=SALES_SIMPLE, timeout=10)
    if response.status_code in [200, 201]:
        data = response.json()
        print(f"  ✓ Created dashboard ID: {data.get('id')}, UID: {data.get('uid')}")
    else:
        print(f"  ✗ Failed: {response.status_code}")
        print(f"    {response.text[:200]}")
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\n[3] Verifying dashboard was created...")
try:
    response = session.get(f"{GRAFANA_URL}/api/dashboards/uid/sales-analytics", timeout=5)
    if response.status_code == 200:
        dash = response.json()['dashboard']
        panel = dash['panels'][0]
        print(f"  ✓ Dashboard exists")
        print(f"    Title: {panel.get('title')}")
        print(f"    Datasource: {panel.get('datasource')}")
        print(f"    Has target: {len(panel.get('targets', [])) > 0}")
        if panel.get('targets'):
            print(f"    Query: {panel['targets'][0].get('rawSql')[:80]}...")
    else:
        print(f"  ✗ Dashboard not found: {response.status_code}")
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\n" + "="*80)
print("FINAL TEST:")
print("="*80)
print("\n1. Go to http://localhost:3000/d/sales-analytics")
print("2. Wait 5 seconds")
print("3. If you see a number, SUCCESS!")
print("4. If still 'No data', check browser console (F12) for errors")
print("\n" + "="*80 + "\n")
