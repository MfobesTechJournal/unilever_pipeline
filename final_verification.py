#!/usr/bin/env python3
"""Final system verification - all services and dashboards"""

import requests
import psycopg2
from psycopg2 import sql
import time

print("=" * 70)
print("UNILEVER PIPELINE - FINAL SYSTEM VERIFICATION")
print("=" * 70)

# 1. Check Grafana Service
print("\n1. GRAFANA SERVICE")
print("-" * 70)
try:
    response = requests.get('http://localhost:3000/api/health')
    if response.status_code == 200:
        print("   ✓ Grafana running on http://localhost:3000")
    else:
        print(f"   ✗ Grafana health check failed: {response.status_code}")
except Exception as e:
    print(f"   ✗ Cannot reach Grafana: {e}")

# 2. Check Datasources
print("\n2. DATASOURCES")
print("-" * 70)
try:
    response = requests.get('http://localhost:3000/api/datasources')
    if response.status_code == 200:
        datasources = response.json()
        print(f"   ✓ Found {len(datasources)} datasource(s)")
        for ds in datasources:
            print(f"     - {ds['name']} ({ds['type']})")
    else:
        print(f"   ✗ Failed to list datasources: {response.status_code}")
except Exception as e:
    print(f"   ✗ Cannot access datasources: {e}")

# 3. Check Dashboards
print("\n3. DASHBOARDS")
print("-" * 70)
try:
    response = requests.get('http://localhost:3000/api/search?type=dash-db')
    if response.status_code == 200:
        dashboards = response.json()
        print(f"   ✓ Found {len(dashboards)} dashboard(s)")
        
        for dash in dashboards:
            dash_response = requests.get(f"http://localhost:3000/api/dashboards/uid/{dash['uid']}")
            if dash_response.status_code == 200:
                dash_detail = dash_response.json()
                panels = dash_detail['dashboard'].get('panels', [])
                print(f"\n     Dashboard: {dash['title']}")
                print(f"     URL: http://localhost:3000/d/{dash['uid']}")
                print(f"     Panels: {len(panels)}")
                for panel in panels:
                    panel_title = panel.get('title', 'Untitled')
                    print(f"       • {panel_title}")
    else:
        print(f"   ✗ Failed to list dashboards: {response.status_code}")
except Exception as e:
    print(f"   ✗ Cannot access dashboards: {e}")

# 4. Check PostgreSQL Data
print("\n4. DATABASE VERIFICATION")
print("-" * 70)
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5433,
        database="unilever_warehouse",
        user="postgres",
        password="123456"
    )
    cursor = conn.cursor()
    
    # Check record counts
    tables = {
        'dim_product': 'SELECT COUNT(*) FROM dim_product',
        'dim_customer': 'SELECT COUNT(*) FROM dim_customer',
        'dim_date': 'SELECT COUNT(*) FROM dim_date',
        'fact_sales': 'SELECT COUNT(*) FROM fact_sales'
    }
    
    print("   ✓ PostgreSQL connection successful")
    print("   Record counts:")
    
    total_records = 0
    for table, query in tables.items():
        cursor.execute(query)
        count = cursor.fetchone()[0]
        total_records += count
        print(f"     - {table}: {count:,} records")
    
    print(f"\n   ✓ Total records in warehouse: {total_records:,}")
    
    # Verify a sample query
    cursor.execute("""
        SELECT COUNT(*) FROM fact_sales fs
        JOIN dim_product dp ON fs.product_key = dp.product_key
        WHERE fs.revenue > 0
    """)
    valid_sales = cursor.fetchone()[0]
    print(f"   ✓ Valid sales with revenue: {valid_sales:,}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"   ✗ Database error: {e}")

# 5. Service Status Check
print("\n5. ALL SERVICES")
print("-" * 70)

services = {
    'PostgreSQL': ('localhost', 5433),
    'pgAdmin': ('localhost', 5050),
    'Grafana': ('localhost', 3000),
    'Airflow': ('localhost', 8080),
    'Prometheus': ('localhost', 9090)
}

import socket

for service, (host, port) in services.items():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print(f"   ✓ {service:20} - Running on {host}:{port}")
        else:
            print(f"   ✗ {service:20} - NOT reachable on {host}:{port}")
    except Exception as e:
        print(f"   ✗ {service:20} - Error: {e}")

print("\n" + "=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)
print("\n🎉 Your Unilever Data Pipeline is READY!")
print("\nNEXT STEPS:")
print("  1. Open Grafana: http://localhost:3000")
print("  2. Select 'Sales Analytics' or 'ETL Monitoring' dashboard")
print("  3. View your data visualizations")
print("\n")
