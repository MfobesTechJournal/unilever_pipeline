#!/usr/bin/env python3
"""Test dashboard data queries against real database"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
import requests
from requests.auth import HTTPBasicAuth

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'unilever_warehouse',
    'user': 'postgres',
    'password': '123456'
}

GRAFANA_URL = 'http://localhost:3000'
GRAFANA_USER = 'admin'
GRAFANA_PASS = 'admin'

def test_database_query():
    """Test if dashboard query works directly"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("\n[TEST 1] Database Query Test")
        print("=" * 50)
        
        # Test the exact query from the dashboard
        query = "SELECT SUM(revenue) as value FROM fact_sales"
        cursor.execute(query)
        result = cursor.fetchone()
        
        print(f"Query: {query}")
        print(f"Result: {result}")
        print(f"✓ Database query returns data: {result['value']}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Database query failed: {e}")
        return False

def test_datasource_health():
    """Test Grafana datasource health"""
    try:
        print("\n[TEST 2] Datasource Health Check")
        print("=" * 50)
        
        response = requests.post(
            f'{GRAFANA_URL}/api/datasources/5/health',
            auth=HTTPBasicAuth(GRAFANA_USER, GRAFANA_PASS)
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data.get('message')}")
            print(f"✓ Datasource is healthy")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False

def get_dashboard_panels():
    """Get dashboard panel details"""
    try:
        print("\n[TEST 3] Dashboard Panel Configuration")
        print("=" * 50)
        
        response = requests.get(
            f'{GRAFANA_URL}/api/dashboards/uid/sales-analytics',
            auth=HTTPBasicAuth(GRAFANA_USER, GRAFANA_PASS)
        )
        
        if response.status_code == 200:
            dashboard = response.json()['dashboard']
            print(f"Dashboard: {dashboard['title']}")
            print(f"Panels: {len(dashboard['panels'])}")
            
            for i, panel in enumerate(dashboard['panels']):
                print(f"\n  Panel {i+1}: {panel['title']}")
                print(f"    Type: {panel['type']}")
                print(f"    Datasource: {panel.get('datasource', {})}")
                
                if 'targets' in panel and panel['targets']:
                    target = panel['targets'][0]
                    print(f"    Query: {target.get('rawSql', 'N/A')[:60]}...")
                    
            return True
        else:
            print(f"✗ Failed to get dashboard: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error getting dashboard: {e}")
        return False

def recreate_dashboard():
    """Recreate the dashboard with proper configuration"""
    try:
        print("\n[TEST 4] Recreating Dashboard with Proper Config")
        print("=" * 50)
        
        dashboard_json = {
            "dashboard": {
                "title": "Sales Analytics",
                "uid": "sales-analytics",
                "version": 1,
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Total Sales Revenue",
                        "type": "stat",
                        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                        "datasource": {
                            "type": "postgres",
                            "uid": "postgres-warehouse",
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
                                "color": {"mode": "palette-classic"}
                            }
                        }
                    },
                    {
                        "id": 2,
                        "title": "Total Transactions",
                        "type": "stat",
                        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0},
                        "datasource": {
                            "type": "postgres",
                            "uid": "postgres-warehouse",
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
                                "color": {"mode": "palette-classic"}
                            }
                        }
                    },
                    {
                        "id": 3,
                        "title": "Average Order Value",
                        "type": "stat",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                        "datasource": {
                            "type": "postgres",
                            "uid": "postgres-warehouse",
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
                                "color": {"mode": "palette-classic"}
                            }
                        }
                    }
                ]
            },
            "overwrite": True
        }
        
        response = requests.post(
            f'{GRAFANA_URL}/api/dashboards/db',
            json=dashboard_json,
            auth=HTTPBasicAuth(GRAFANA_USER, GRAFANA_PASS)
        )
        
        if response.status_code in [200, 201]:
            print("✓ Dashboard recreated successfully")
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"✗ Failed to create dashboard: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error recreating dashboard: {e}")
        return False

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("DASHBOARD FIX DIAGNOSTIC")
    print("=" * 50)
    
    test_database_query()
    test_datasource_health()
    get_dashboard_panels()
    
    print("\n[ACTION] Recreating dashboard...")
    recreate_dashboard()
    
    print("\n" + "=" * 50)
    print("DIAGNOSTICS COMPLETE")
    print("Go to http://localhost:3000 → Dashboards → Sales Analytics")
    print("Hard refresh (Ctrl+F5) to see updated dashboard")
    print("=" * 50 + "\n")
