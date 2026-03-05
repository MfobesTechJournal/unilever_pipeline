#!/usr/bin/env python3
"""Recreate dashboard with fixed color modes and correct datasource type"""

import requests
from requests.auth import HTTPBasicAuth

GRAFANA_URL = 'http://localhost:3000'
GRAFANA_USER = 'admin'
GRAFANA_PASS = 'admin'
DATASOURCE_UID = 'ffetjvdi3rojkb'

dashboard_config = {
    "dashboard": {
        "id": None,
        "uid": "sales-analytics",
        "title": "Sales Analytics",
        "version": 4,
        "timezone": "browser",
        "panels": [
            {
                "id": 1,
                "title": "Total Sales Revenue",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": DATASOURCE_UID,
                    "name": "PostgreSQL Warehouse"
                },
                "targets": [
                    {
                        "refId": "A",
                        "rawSql": "SELECT SUM(revenue) as value FROM fact_sales",
                        "format": "table"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "mappings": [],
                        "color": {
                            "mode": "fixed",
                            "fixedColor": "green"
                        },
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
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": DATASOURCE_UID,
                    "name": "PostgreSQL Warehouse"
                },
                "targets": [
                    {
                        "refId": "A",
                        "rawSql": "SELECT COUNT(*) as value FROM fact_sales",
                        "format": "table"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "mappings": [],
                        "color": {
                            "mode": "fixed",
                            "fixedColor": "blue"
                        },
                        "unit": "short",
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
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": DATASOURCE_UID,
                    "name": "PostgreSQL Warehouse"
                },
                "targets": [
                    {
                        "refId": "A",
                        "rawSql": "SELECT AVG(revenue) as value FROM fact_sales",
                        "format": "table"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "mappings": [],
                        "color": {
                            "mode": "fixed",
                            "fixedColor": "orange"
                        },
                        "unit": "currencyUSD",
                        "custom": {}
                    },
                    "overrides": []
                }
            },
            {
                "id": 4,
                "title": "Daily Sales Trend",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": DATASOURCE_UID,
                    "name": "PostgreSQL Warehouse"
                },
                "targets": [
                    {
                        "refId": "A",
                        "rawSql": "SELECT dd.sale_date as time, SUM(fs.revenue) as value FROM fact_sales fs JOIN dim_date dd ON fs.date_key = dd.date_key GROUP BY dd.sale_date ORDER BY time DESC LIMIT 30",
                        "format": "table"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "drawStyle": "line",
                            "lineInterpolation": "linear"
                        },
                        "color": {
                            "mode": "palette-classic"
                        }
                    },
                    "overrides": []
                }
            },
            {
                "id": 5,
                "title": "Top 10 Products",
                "type": "table",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
                "datasource": {
                    "type": "grafana-postgresql-datasource",
                    "uid": DATASOURCE_UID,
                    "name": "PostgreSQL Warehouse"
                },
                "targets": [
                    {
                        "refId": "A",
                        "rawSql": "SELECT dp.product_name, SUM(fs.revenue) as total_revenue, SUM(fs.quantity) as total_quantity FROM fact_sales fs JOIN dim_product dp ON fs.product_key = dp.product_key GROUP BY dp.product_name ORDER BY total_revenue DESC LIMIT 10",
                        "format": "table"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "mappings": [],
                        "color": {
                            "mode": "palette-classic"
                        }
                    },
                    "overrides": []
                }
            }
        ]
    },
    "overwrite": True
}

try:
    print(f"\n{'='*70}")
    print("RECREATING DASHBOARD - FIXED VERSION")
    print(f"{'='*70}")
    print(f"Datasource Type: grafana-postgresql-datasource")
    print(f"Datasource UID: {DATASOURCE_UID}")
    print(f"Color Modes: fixed (stat panels), palette-classic (chart panels)")
    print(f"Panels: {len(dashboard_config['dashboard']['panels'])}")
    
    response = requests.post(
        f'{GRAFANA_URL}/api/dashboards/db',
        json=dashboard_config,
        auth=HTTPBasicAuth(GRAFANA_USER, GRAFANA_PASS)
    )
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"\n✓ Dashboard Created Successfully!")
        print(f"  ID: {result.get('id')}")
        print(f"  UID: {result.get('uid')}")
        print(f"  Status: {result.get('status')}")
        print(f"  Version: {result.get('version')}")
    else:
        print(f"\n✗ Failed: {response.status_code}")
        print(f"  Error: {response.text}")
        
except Exception as e:
    print(f"\n✗ Error: {e}")

print(f"\n{'='*70}")
print("NEXT STEPS:")
print("1. Go to http://localhost:3000")
print("2. Navigate to Dashboards → Sales Analytics")  
print("3. Hard refresh (Ctrl+F5)")
print("4. Data should now display in all 5 panels")
print(f"{'='*70}\n")
