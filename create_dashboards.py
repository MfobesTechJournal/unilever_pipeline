#!/usr/bin/env python3
"""
Create Grafana dashboards and datasource directly via API
"""

import requests
import json
import time
import sys

GRAFANA_URL = "http://localhost:3000"
AUTH = ("admin", "admin")

def wait_for_grafana():
    """Wait for Grafana to be ready"""
    print("⏳ Waiting for Grafana...", end=" ", flush=True)
    for i in range(30):
        try:
            response = requests.get(f"{GRAFANA_URL}/api/health", timeout=2)
            if response.status_code == 200:
                print("✓\n")
                return True
        except:
            pass
        time.sleep(1)
    print("✗")
    return False

def create_datasource():
    """Create PostgreSQL datasource"""
    print("📊 Creating PostgreSQL datasource...", end=" ", flush=True)
    
    url = f"{GRAFANA_URL}/api/datasources"
    payload = {
        "name": "PostgreSQL Warehouse",
        "type": "postgres",
        "url": "postgres:5432",
        "access": "proxy",
        "isDefault": True,
        "jsonData": {
            "sslmode": "disable",
            "postgresVersion": 1400,
        },
        "secureJsonData": {
            "password": "123456"
        },
        "database": "unilever_warehouse",
        "user": "postgres"
    }
    
    try:
        response = requests.post(url, json=payload, auth=AUTH, timeout=10)
        if response.status_code in [200, 201]:
            print("✓")
            return response.json().get('id')
        else:
            print(f"⚠ ({response.status_code})")
            # Try to get existing datasource
            response = requests.get(url, auth=AUTH, timeout=10)
            if response.status_code == 200:
                sources = response.json()
                for source in sources:
                    if source['name'] == 'PostgreSQL Warehouse':
                        print("  (Already exists)")
                        return source['id']
            return None
    except Exception as e:
        print(f"✗ {e}")
        return None

def create_sales_dashboard():
    """Create Sales Analytics dashboard"""
    print("📈 Creating Sales Analytics dashboard...", end=" ", flush=True)
    
    dashboard_json = {
        "dashboard": {
            "title": "Sales Analytics",
            "tags": ["sales", "analytics"],
            "timezone": "browser",
            "panels": [
                {
                    "id": 1,
                    "title": "Total Sales Revenue",
                    "type": "stat",
                    "gridPos": {"x": 0, "y": 0, "w": 8, "h": 4},
                    "datasource": "PostgreSQL Warehouse",
                    "targets": [
                        {
                            "rawSql": "SELECT SUM(revenue)::TEXT as value FROM fact_sales;",
                            "format": "table",
                            "refId": "A"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "currencyUSD",
                            "custom": {}
                        }
                    },
                    "options": {
                        "colorMode": "background",
                        "graphMode": "none"
                    }
                },
                {
                    "id": 2,
                    "title": "Total Transactions",
                    "type": "stat",
                    "gridPos": {"x": 8, "y": 0, "w": 8, "h": 4},
                    "datasource": "PostgreSQL Warehouse",
                    "targets": [
                        {
                            "rawSql": "SELECT COUNT(*)::TEXT as value FROM fact_sales;",
                            "format": "table",
                            "refId": "A"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "short",
                            "custom": {}
                        }
                    },
                    "options": {
                        "colorMode": "background",
                        "graphMode": "none"
                    }
                },
                {
                    "id": 3,
                    "title": "Average Order Value",
                    "type": "stat",
                    "gridPos": {"x": 16, "y": 0, "w": 8, "h": 4},
                    "datasource": "PostgreSQL Warehouse",
                    "targets": [
                        {
                            "rawSql": "SELECT ROUND(AVG(revenue)::NUMERIC, 2)::TEXT as value FROM fact_sales;",
                            "format": "table",
                            "refId": "A"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "currencyUSD",
                            "custom": {}
                        }
                    },
                    "options": {
                        "colorMode": "background",
                        "graphMode": "none"
                    }
                },
                {
                    "id": 4,
                    "title": "Sales by Day",
                    "type": "timeseries",
                    "gridPos": {"x": 0, "y": 4, "w": 12, "h": 8},
                    "datasource": "PostgreSQL Warehouse",
                    "targets": [
                        {
                            "rawSql": "SELECT dd.sale_date as time, SUM(fs.revenue) as revenue FROM fact_sales fs JOIN dim_date dd ON fs.date_key = dd.date_key GROUP BY dd.sale_date ORDER BY dd.sale_date;",
                            "format": "timeseries",
                            "refId": "A"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "currencyUSD",
                            "custom": {}
                        }
                    }
                },
                {
                    "id": 5,
                    "title": "Top 10 Products",
                    "type": "table",
                    "gridPos": {"x": 12, "y": 4, "w": 12, "h": 8},
                    "datasource": "PostgreSQL Warehouse",
                    "targets": [
                        {
                            "rawSql": "SELECT dp.product_name, SUM(fs.quantity) as quantity, ROUND(SUM(fs.revenue)::NUMERIC, 2) as revenue FROM fact_sales fs JOIN dim_product dp ON fs.product_key = dp.product_key GROUP BY dp.product_name ORDER BY revenue DESC LIMIT 10;",
                            "format": "table",
                            "refId": "A"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "custom": {}
                        }
                    }
                }
            ],
            "schemaVersion": 36,
            "version": 0,
            "refresh": "30s",
            "time": {
                "from": "now-30d",
                "to": "now"
            }
        },
        "overwrite": True
    }
    
    try:
        response = requests.post(
            f"{GRAFANA_URL}/api/dashboards/db",
            json=dashboard_json,
            auth=AUTH,
            timeout=10
        )
        if response.status_code in [200, 201]:
            print("✓")
            return True
        else:
            print(f"✗ ({response.status_code})")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ {e}")
        return False

def create_etl_dashboard():
    """Create ETL Monitoring dashboard"""
    print("🔧 Creating ETL Monitoring dashboard...", end=" ", flush=True)
    
    dashboard_json = {
        "dashboard": {
            "title": "ETL Monitoring",
            "tags": ["etl", "pipeline"],
            "timezone": "browser",
            "panels": [
                {
                    "id": 1,
                    "title": "Recent ETL Executions",
                    "type": "table",
                    "gridPos": {"x": 0, "y": 0, "w": 24, "h": 8},
                    "datasource": "PostgreSQL Warehouse",
                    "targets": [
                        {
                            "rawSql": "SELECT execution_date, process_name, status, record_count, COALESCE(error_message, 'N/A') as error_message FROM etl_log ORDER BY execution_date DESC LIMIT 50;",
                            "format": "table",
                            "refId": "A"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "custom": {}
                        }
                    }
                },
                {
                    "id": 2,
                    "title": "Data Quality Issues",
                    "type": "table",
                    "gridPos": {"x": 0, "y": 8, "w": 24, "h": 8},
                    "datasource": "PostgreSQL Warehouse",
                    "targets": [
                        {
                            "rawSql": "SELECT check_date, table_name, rule_name, failure_count, COALESCE(details, 'N/A') as details FROM data_quality_log WHERE failure_count > 0 ORDER BY check_date DESC LIMIT 50;",
                            "format": "table",
                            "refId": "A"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "custom": {}
                        }
                    }
                }
            ],
            "schemaVersion": 36,
            "version": 0,
            "refresh": "1m",
            "time": {
                "from": "now-30d",
                "to": "now"
            }
        },
        "overwrite": True
    }
    
    try:
        response = requests.post(
            f"{GRAFANA_URL}/api/dashboards/db",
            json=dashboard_json,
            auth=AUTH,
            timeout=10
        )
        if response.status_code in [200, 201]:
            print("✓")
            return True
        else:
            print(f"✗ ({response.status_code})")
            return False
    except Exception as e:
        print(f"✗ {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("GRAFANA DASHBOARD SETUP")
    print("="*60 + "\n")
    
    if not wait_for_grafana():
        print("❌ Grafana not responding")
        sys.exit(1)
    
    ds_id = create_datasource()
    time.sleep(1)
    
    success = True
    success = create_sales_dashboard() and success
    time.sleep(1)
    success = create_etl_dashboard() and success
    
    print()
    if success:
        print("="*60)
        print("✅ Dashboards created successfully!")
        print("="*60)
        print("\n🌍 Visit: http://localhost:3000")
        print("📊 Go to: Dashboards → Sales Analytics")
        print("\n")
    else:
        print("⚠️  Some dashboards may not have created properly")
        print("Check http://localhost:3000/dashboards\n")
