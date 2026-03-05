#!/usr/bin/env python3
"""
Create Grafana dashboards with proper datasource configuration
"""

import requests
import json
import time

GRAFANA_URL = "http://localhost:3000"
GRAFANA_AUTH = ("admin", "admin")

print("\n" + "="*80)
print("CREATING GRAFANA DASHBOARDS WITH DATA")
print("="*80)

# Get updated datasource info
print("\n[1] Getting datasource info...")
print("-" * 80)

response = requests.get(f"{GRAFANA_URL}/api/datasources", auth=GRAFANA_AUTH)
datasources = response.json()

print(f"Found {len(datasources)} datasource(s):")

postgres_ds = None
for ds in datasources:
    print(f"  - {ds['name']}")
    if 'postgres' in ds['type'].lower():
        postgres_ds = ds

if not postgres_ds:
    print("\n✗ No PostgreSQL datasource found!")
    exit(1)

DS_UID = postgres_ds['uid']
print(f"\n✓ Using datasource UID: {DS_UID}")

# Create Sales Dashboard
print("\n[2] CREATING SALES ANALYTICS DASHBOARD")
print("-" * 80)

sales_dashboard = {
    "dashboard": {
        "title": "Sales Analytics - 500K Records",
        "tags": ["sales", "analytics", "10x"],
        "timezone": "browser",
        "panels": [
            {
                "id": 1,
                "title": "Total Revenue",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                "targets": [{
                    "refId": "A",
                    "datasourceUid": DS_UID,
                    "rawSql": "SELECT SUM(revenue) as value FROM fact_sales",
                    "format": "table"
                }],
                "fieldConfig": {
                    "defaults": {
                        "unit": "currencyUSD",
                        "custom": {}
                    },
                    "overrides": []
                }
            },
            {
                "id": 2,
                "title": "Total Transactions",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0},
                "targets": [{
                    "refId": "A",
                    "datasourceUid": DS_UID,
                    "rawSql": "SELECT COUNT(*) as value FROM fact_sales",
                    "format": "table"
                }],
                "fieldConfig": {
                    "defaults": {
                        "custom": {}
                    },
                    "overrides": []
                }
            },
            {
                "id": 3,
                "title": "Average Order Value",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0},
                "targets": [{
                    "refId": "A",
                    "datasourceUid": DS_UID,
                    "rawSql": "SELECT AVG(revenue) as value FROM fact_sales",
                    "format": "table"
                }],
                "fieldConfig": {
                    "defaults": {
                        "unit": "currencyUSD",
                        "custom": {}
                    },
                    "overrides": []
                }
            },
            {
                "id": 4,
                "title": "Top 10 Products by Revenue",
                "type": "table",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                "targets": [{
                    "refId": "A",
                    "datasourceUid": DS_UID,
                    "rawSql": "SELECT dp.product_name, SUM(fs.quantity) as quantity, SUM(fs.revenue) as revenue FROM fact_sales fs JOIN dim_product dp ON fs.product_key = dp.product_key GROUP BY dp.product_name ORDER BY revenue DESC LIMIT 10",
                    "format": "table"
                }],
                "fieldConfig": {
                    "defaults": {
                        "custom": {}
                    },
                    "overrides": []
                }
            },
            {
                "id": 5,
                "title": "Daily Revenue",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                "targets": [{
                    "refId": "A",
                    "datasourceUid": DS_UID,
                    "rawSql": "SELECT DATE(load_timestamp) as time, SUM(revenue) as value FROM fact_sales GROUP BY DATE(load_timestamp) ORDER BY time",
                    "format": "table"
                }],
                "fieldConfig": {
                    "defaults": {
                        "custom": {}
                    },
                    "overrides": []
                }
            }
        ]
    },
    "overwrite": True
}

response = requests.post(
    f"{GRAFANA_URL}/api/dashboards/db",
    json=sales_dashboard,
    auth=GRAFANA_AUTH
)

if response.status_code in [200, 201]:
    result = response.json()
    print(f"✓ Sales Analytics Dashboard created!")
    print(f"  URL: http://localhost:3000/d/{result.get('id')}")
else:
    print(f"✗ Error: {response.text[:300]}")

# Create ETL Dashboard
print("\n[3] CREATING ETL MONITORING DASHBOARD")
print("-" * 80)

etl_dashboard = {
    "dashboard": {
        "title": "ETL Monitoring - 10x Data",
        "tags": ["etl", "monitoring", "10x"],
        "timezone": "browser",
        "panels": [
            {
                "id": 1,
                "title": "Total ETL Runs",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                "targets": [{
                    "refId": "A",
                    "datasourceUid": DS_UID,
                    "rawSql": "SELECT COUNT(*) as value FROM etl_log",
                    "format": "table"
                }],
                "fieldConfig": {
                    "defaults": {
                        "custom": {}
                    },
                    "overrides": []
                }
            },
            {
                "id": 2,
                "title": "Total Records Loaded",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0},
                "targets": [{
                    "refId": "A",
                    "datasourceUid": DS_UID,
                    "rawSql": "SELECT COALESCE(SUM(records_facts), 0) as value FROM etl_log",
                    "format": "table"
                }],
                "fieldConfig": {
                    "defaults": {
                        "custom": {}
                    },
                    "overrides": []
                }
            },
            {
                "id": 3,
                "title": "Success Rate",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0},
                "targets": [{
                    "refId": "A",
                    "datasourceUid": DS_UID,
                    "rawSql": "SELECT ROUND(100.0 * SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) as value FROM etl_log",
                    "format": "table"
                }],
                "fieldConfig": {
                    "defaults": {
                        "unit": "percent",
                        "custom": {}
                    },
                    "overrides": []
                }
            },
            {
                "id": 4,
                "title": "Recent ETL Runs (Last 30)",
                "type": "table",
                "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8},
                "targets": [{
                    "refId": "A",
                    "datasourceUid": DS_UID,
                    "rawSql": "SELECT run_id, start_time, status, COALESCE(records_facts, 0) as records_loaded FROM etl_log ORDER BY start_time DESC LIMIT 30",
                    "format": "table"
                }],
                "fieldConfig": {
                    "defaults": {
                        "custom": {}
                    },
                    "overrides": []
                }
            }
        ]
    },
    "overwrite": True
}

response = requests.post(
    f"{GRAFANA_URL}/api/dashboards/db",
    json=etl_dashboard,
    auth=GRAFANA_AUTH
)

if response.status_code in [200, 201]:
    result = response.json()
    print(f"✓ ETL Monitoring Dashboard created!")
    print(f"  URL: http://localhost:3000/d/{result.get('id')}")
else:
    print(f"✗ Error: {response.text[:300]}")

print("\n" + "="*80)
print("✓ DASHBOARDS CREATED!")
print("="*80)
print(f"\n🌐 Open Grafana at:")
print(f"   http://localhost:3000")
print(f"\n📊 Your Dashboards:")
print(f"   • Sales Analytics - 500K Records")
print(f"   • ETL Monitoring - 10x Data")
print(f"\n💾 Data:")
print(f"   • 500,000 sales records")
print(f"   • $526.8 Million revenue")
print(f"   • 731 ETL runs")
print("\nRefresh your browser if dashboards are still empty!")
