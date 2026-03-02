#!/usr/bin/env python3
"""
Recreate Grafana dashboards from scratch with corrected JSON.
This ensures panels are properly configured to display data.
"""

import requests
import json

GRAFANA_URL = "http://localhost:3000"
GRAFANA_AUTH = ("admin", "admin")

# Sales Analytics Dashboard
SALES_DASHBOARD = {
    "dashboard": {
        "title": "Sales Analytics",
        "tags": ["analytics", "sales"],
        "timezone": "browser",
        "panels": [
            {
                "id": 1,
                "title": "Total Sales Revenue",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                "datasource": "PostgreSQL Warehouse",
                "targets": [
                    {
                        "rawSql": "SELECT SUM(revenue)::numeric as value FROM fact_sales",
                        "refId": "A"
                    }
                ],
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
            },
            {
                "id": 2,
                "title": "Total Transactions",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0},
                "datasource": "PostgreSQL Warehouse",
                "targets": [
                    {
                        "rawSql": "SELECT COUNT(*) as value FROM fact_sales",
                        "refId": "A"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [{"color": "blue", "value": None}]
                        }
                    }
                }
            },
            {
                "id": 3,
                "title": "Average Order Value",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0},
                "datasource": "PostgreSQL Warehouse",
                "targets": [
                    {
                        "rawSql": "SELECT AVG(revenue)::numeric as value FROM fact_sales",
                        "refId": "A"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "unit": "currencyUSD",
                        "color": {"mode": "thresholds"},
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [{"color": "purple", "value": None}]
                        }
                    }
                }
            },
            {
                "id": 4,
                "title": "Daily Sales Trend",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                "datasource": "PostgreSQL Warehouse",
                "targets": [
                    {
                        "rawSql": "SELECT dd.sale_date as time, SUM(fs.revenue) as value FROM fact_sales fs JOIN dim_date dd ON fs.date_key = dd.date_key GROUP BY dd.sale_date ORDER BY dd.sale_date DESC LIMIT 30",
                        "refId": "A"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "unit": "currencyUSD",
                        "color": {"mode": "palette-classic"}
                    }
                }
            },
            {
                "id": 5,
                "title": "Top 10 Products",
                "type": "table",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                "datasource": "PostgreSQL Warehouse",
                "targets": [
                    {
                        "rawSql": "SELECT dp.product_name, SUM(fs.revenue)::numeric as total_revenue FROM fact_sales fs JOIN dim_product dp ON fs.product_key = dp.product_key GROUP BY dp.product_name ORDER BY total_revenue DESC LIMIT 10",
                        "refId": "A"
                    }
                ]
            }
        ]
    }
}

# ETL Monitoring Dashboard
ETL_DASHBOARD = {
    "dashboard": {
        "title": "ETL Monitoring",
        "tags": ["etl", "pipeline"],
        "timezone": "browser",
        "panels": [
            {
                "id": 1,
                "title": "ETL Logs",
                "type": "table",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                "datasource": "PostgreSQL Warehouse",
                "targets": [
                    {
                        "rawSql": "SELECT log_id, etl_process, status, load_timestamp FROM etl_log ORDER BY load_timestamp DESC LIMIT 100",
                        "refId": "A"
                    }
                ]
            },
            {
                "id": 2,
                "title": "Data Quality Issues",
                "type": "table",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                "datasource": "PostgreSQL Warehouse",
                "targets": [
                    {
                        "rawSql": "SELECT quality_check_id, check_name, issue_description, severity, detected_at FROM data_quality_log ORDER BY detected_at DESC LIMIT 100",
                        "refId": "A"
                    }
                ]
            }
        ]
    }
}

print("\n" + "="*80)
print("RECREATING GRAFANA DASHBOARDS")
print("="*80)

session = requests.Session()
session.auth = GRAFANA_AUTH

# Delete existing dashboards
print("\n[1] Deleting existing dashboards...")
for uid in ["sales-analytics", "etl-monitoring"]:
    try:
        response = session.delete(f"{GRAFANA_URL}/api/dashboards/uid/{uid}")
        if response.status_code in [200, 404]:
            print(f"  ✓ Deleted: {uid}")
    except Exception as e:
        print(f"  ⚠ Could not delete {uid}: {e}")

# Create Sales Analytics Dashboard
print("\n[2] Creating Sales Analytics Dashboard...")
try:
    response = session.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        json=SALES_DASHBOARD,
        timeout=10
    )
    
    if response.status_code in [200, 201]:
        data = response.json()
        print(f"✓ Dashboard created (ID: {data.get('id')}, UID: {data.get('uid')})")
    else:
        print(f"✗ Failed: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
except Exception as e:
    print(f"✗ Error: {e}")

# Create ETL Monitoring Dashboard
print("\n[3] Creating ETL Monitoring Dashboard...")
try:
    response = session.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        json=ETL_DASHBOARD,
        timeout=10
    )
    
    if response.status_code in [200, 201]:
        data = response.json()
        print(f"✓ Dashboard created (ID: {data.get('id')}, UID: {data.get('uid')})")
    else:
        print(f"✗ Failed: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
except Exception as e:
    print(f"✗ Error: {e}")

# Verify dashboards
print("\n[4] Verifying dashboards...")
try:
    response = session.get(f"{GRAFANA_URL}/api/search?type=dash-db")
    dashboards = response.json()
    
    for dash in dashboards:
        uid = dash.get('uid')
        title = dash.get('title')
        print(f"  ✓ {title} (UID: {uid})")
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\n" + "="*80)
print("NEXT STEPS:")
print("="*80)
print("\n1. Open http://localhost:3000")
print("2. Go to Dashboards")
print("3. Click 'Sales Analytics'")
print("4. Wait 5-10 seconds for data to load")
print("5. If data appears, you're DONE!")
print("\n" + "="*80 + "\n")
