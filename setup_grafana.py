#!/usr/bin/env python3
"""
Setup Grafana datasources and dashboards for Unilever Pipeline.
Runs against http://localhost:3000 (admin/admin)
"""

import requests
import json
import time
from typing import Dict, Any

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASSWORD = "admin"

def setup_datasource() -> Dict[str, Any]:
    """Configure PostgreSQL datasource in Grafana"""
    print("Setting up PostgreSQL datasource...")
    
    url = f"{GRAFANA_URL}/api/datasources"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "name": "PostgreSQL Warehouse",
        "type": "postgres",
        "url": "postgres:5433",
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
    
    try:
        response = requests.post(url, json=payload, auth=(GRAFANA_USER, GRAFANA_PASSWORD), timeout=10)
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"  ✓ PostgreSQL datasource created (ID: {data.get('id')})")
            return data
        else:
            print(f"  ✗ Error: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        print(f"  ✗ Failed to connect to Grafana: {e}")
        return {}

def create_dashboard() -> Dict[str, Any]:
    """Create sales analytics dashboard"""
    print("Creating Sales Analytics dashboard...")
    
    url = f"{GRAFANA_URL}/api/dashboards/db"
    headers = {"Content-Type": "application/json"}
    
    dashboard = {
        "dashboard": {
            "title": "Sales Analytics",
            "tags": ["sales", "analytics"],
            "timezone": "browser",
            "panels": [
                {
                    "id": 1,
                    "title": "Total Sales Revenue",
                    "type": "stat",
                    "gridPos": {"x": 0, "y": 0, "w": 6, "h": 4},
                    "targets": [
                        {
                            "datasource": "PostgreSQL Warehouse",
                            "rawSql": "SELECT SUM(revenue) as value FROM fact_sales",
                            "refId": "A"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "palette-classic"},
                            "unit": "currencyUSD"
                        }
                    },
                    "options": {"colorMode": "background", "graphMode": "none", "orientation": "auto"}
                },
                {
                    "id": 2,
                    "title": "Total Transactions",
                    "type": "stat",
                    "gridPos": {"x": 6, "y": 0, "w": 6, "h": 4},
                    "targets": [
                        {
                            "datasource": "PostgreSQL Warehouse",
                            "rawSql": "SELECT COUNT(*) as value FROM fact_sales",
                            "refId": "A"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "palette-classic"},
                            "unit": "short"
                        }
                    },
                    "options": {"colorMode": "background", "graphMode": "none", "orientation": "auto"}
                },
                {
                    "id": 3,
                    "title": "Average Order Value",
                    "type": "stat",
                    "gridPos": {"x": 12, "y": 0, "w": 6, "h": 4},
                    "targets": [
                        {
                            "datasource": "PostgreSQL Warehouse",
                            "rawSql": "SELECT AVG(revenue) as value FROM fact_sales",
                            "refId": "A"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "palette-classic"},
                            "unit": "currencyUSD"
                        }
                    },
                    "options": {"colorMode": "background", "graphMode": "none", "orientation": "auto"}
                },
                {
                    "id": 4,
                    "title": "Daily Sales Trend",
                    "type": "timeseries",
                    "gridPos": {"x": 0, "y": 4, "w": 12, "h": 8},
                    "targets": [
                        {
                            "datasource": "PostgreSQL Warehouse",
                            "rawSql": "SELECT dd.sale_date as time, SUM(fs.revenue) as revenue FROM fact_sales fs JOIN dim_date dd ON fs.date_key = dd.date_key GROUP BY dd.sale_date ORDER BY dd.sale_date",
                            "refId": "A"
                        }
                    ]
                },
                {
                    "id": 5,
                    "title": "Top 10 Products",
                    "type": "table",
                    "gridPos": {"x": 12, "y": 4, "w": 12, "h": 8},
                    "targets": [
                        {
                            "datasource": "PostgreSQL Warehouse",
                            "rawSql": "SELECT dp.product_name, SUM(fs.quantity) as quantity, SUM(fs.revenue) as revenue FROM fact_sales fs JOIN dim_product dp ON fs.product_key = dp.product_key GROUP BY dp.product_name ORDER BY revenue DESC LIMIT 10",
                            "refId": "A"
                        }
                    ]
                }
            ],
            "refresh": "30s",
            "schemaVersion": 36,
            "version": 0
        },
        "overwrite": True
    }
    
    try:
        response = requests.post(url, json=dashboard, auth=(GRAFANA_USER, GRAFANA_PASSWORD), timeout=10)
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"  ✓ Sales Analytics dashboard created")
            return data
        else:
            print(f"  ✗ Error: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        print(f"  ✗ Failed to create dashboard: {e}")
        return {}

def create_etl_dashboard() -> Dict[str, Any]:
    """Create ETL monitoring dashboard"""
    print("Creating ETL Monitoring dashboard...")
    
    url = f"{GRAFANA_URL}/api/dashboards/db"
    headers = {"Content-Type": "application/json"}
    
    dashboard = {
        "dashboard": {
            "title": "ETL Monitoring",
            "tags": ["etl", "pipeline"],
            "timezone": "browser",
            "panels": [
                {
                    "id": 1,
                    "title": "ETL Logs",
                    "type": "table",
                    "gridPos": {"x": 0, "y": 0, "w": 24, "h": 6},
                    "targets": [
                        {
                            "datasource": "PostgreSQL Warehouse",
                            "rawSql": "SELECT execution_date, process_name, status, record_count, error_message FROM etl_log ORDER BY execution_date DESC LIMIT 50",
                            "refId": "A"
                        }
                    ]
                },
                {
                    "id": 2,
                    "title": "Data Quality Issues",
                    "type": "table",
                    "gridPos": {"x": 0, "y": 6, "w": 24, "h": 6},
                    "targets": [
                        {
                            "datasource": "PostgreSQL Warehouse",
                            "rawSql": "SELECT check_date, table_name, rule_name, failure_count, details FROM data_quality_log WHERE failure_count > 0 ORDER BY check_date DESC LIMIT 50",
                            "refId": "A"
                        }
                    ]
                }
            ],
            "refresh": "1m",
            "schemaVersion": 36,
            "version": 0
        },
        "overwrite": True
    }
    
    try:
        response = requests.post(url, json=dashboard, auth=(GRAFANA_USER, GRAFANA_PASSWORD), timeout=10)
        if response.status_code in [200, 201]:
            print(f"  ✓ ETL Monitoring dashboard created")
            return response.json()
        else:
            print(f"  ✗ Error: {response.status_code}")
            return {}
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return {}

if __name__ == "__main__":
    print("=" * 60)
    print("GRAFANA SETUP - Unilever Pipeline")
    print("=" * 60)
    print(f"Target: {GRAFANA_URL}")
    print()
    
    # Wait for Grafana to be ready
    for i in range(30):
        try:
            response = requests.get(f"{GRAFANA_URL}/api/health", timeout=2)
            if response.status_code == 200:
                print("✓ Grafana is ready")
                break
        except:
            if i == 29:
                print("✗ Grafana did not respond after 30 attempts")
                exit(1)
            time.sleep(1)
    
    print()
    setup_datasource()
    time.sleep(2)
    
    print()
    create_dashboard()
    time.sleep(2)
    
    print()
    create_etl_dashboard()
    
    print()
    print("=" * 60)
    print("✓ Grafana setup complete!")
    print(f"   Access at: http://localhost:3000")
    print(f"   Login: admin / admin")
    print("=" * 60)
