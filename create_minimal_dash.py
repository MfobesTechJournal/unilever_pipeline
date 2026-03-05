#!/usr/bin/env python3
"""Create minimal working dashboard"""

import requests
from requests.auth import HTTPBasicAuth
import json

GRAFANA_URL = 'http://localhost:3000'
GRAFANA_USER = 'admin'
GRAFANA_PASS = 'admin'
DATASOURCE_UID = 'ffetjvdi3rojkb'

# Minimal dashboard config
dashboard_config = {
    "dashboard": {
        "id": None,
        "uid": "sales-analytics-v2",
        "title": "Sales Analytics",
        "timezone": "browser",
        "schemaVersion": 30,
        "version": 0,
        "description": "Sales data analytics dashboard",
        "tags": ["sales", "analytics"],
        "panels": [
            {
                "id": 1,
                "title": "Total Sales Revenue",
                "type": "stat",
                "pluginVersion": "9.0.0",
                "gridPos": {
                    "h": 8,
                    "w": 12,
                    "x": 0,
                    "y": 0
                },
                "targets": [
                    {
                        "refId": "A",
                        "datasourceUid": DATASOURCE_UID,
                        "rawSql": "SELECT SUM(revenue) as value FROM fact_sales",
                        "format": "table",
                        "rawQuery": True
                    }
                ],
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": DATASOURCE_UID,
                    "name": "PostgreSQL Warehouse"
                },
                "options": {
                    "orientation": "auto",
                    "textMode": "auto",
                    "colorMode": "background",
                    "graphMode": "none",
                    "justifyMode": "auto",
                    "displayMode": "auto"
                },
                "fieldConfig": {
                    "defaults": {
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None}
                            ]
                        },
                        "unit": "currencyUSD",
                        "noValue": "N/A"
                    },
                    "overrides": []
                }
            }
        ]
    },
    "overwrite": True
}

try:
    print("\n" + "="*70)
    print("CREATING MINIMAL DASHBOARD")
    print("="*70)
    print(f"Dashboard UID: sales-analytics-v2")
    print(f"Datasource: {DATASOURCE_UID}")
    print(f"Panels: 1 (test panel)")
    
    response = requests.post(
        f'{GRAFANA_URL}/api/dashboards/db',
        json=dashboard_config,
        auth=HTTPBasicAuth(GRAFANA_USER, GRAFANA_PASS)
    )
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"\n✓ Dashboard Created!")
        print(f"  ID: {result.get('id')}")
        print(f"  UID: {result.get('uid')}")
        print(f"  Status: {result.get('status')}")
        print(f"  URL: http://localhost:3000/d/{result.get('uid')}")
    else:
        print(f"\n✗ Failed: {response.status_code}")
        print(f"  Response: {response.text}")
        
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("NEXT: Go to http://localhost:3000/d/sales-analytics-v2")
print("="*70 + "\n")
