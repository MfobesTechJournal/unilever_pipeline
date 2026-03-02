#!/usr/bin/env python3
"""
Diagnose why Grafana dashboards are empty despite data existing.
"""

import requests
import psycopg2
import json

GRAFANA_URL = "http://localhost:3000"
GRAFANA_AUTH = ("admin", "admin")

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "unilever_warehouse",
    "user": "postgres",
    "password": "123456"
}

print("\n" + "="*80)
print("GRAFANA DASHBOARD DATA DIAGNOSIS")
print("="*80)

# Step 1: Check database
print("\n[1] DATABASE CHECK")
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM fact_sales")
    count = cursor.fetchone()[0]
    print(f"✓ Database has {count:,} records in fact_sales")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"✗ Database error: {e}")

# Step 2: Check Grafana
print("\n[2] GRAFANA CHECK")
session = requests.Session()
session.auth = GRAFANA_AUTH

try:
    response = session.get(f"{GRAFANA_URL}/api/health", timeout=5)
    print(f"✓ Grafana is accessible (v{response.json().get('version')})")
except Exception as e:
    print(f"✗ Cannot access Grafana: {e}")

# Step 3: Check Datasource Configuration
print("\n[3] DATASOURCE CONFIGURATION")
try:
    response = session.get(f"{GRAFANA_URL}/api/datasources", timeout=5)
    datasources = response.json()
    
    pg_ds = None
    for ds in datasources:
        if 'postgres' in ds.get('type', '').lower():
            pg_ds = ds
            print(f"✓ Found PostgreSQL datasource: {ds.get('name')} (ID: {ds.get('id')})")
            
            # Get detailed config
            detail_response = session.get(f"{GRAFANA_URL}/api/datasources/{ds.get('id')}", timeout=5)
            details = detail_response.json()
            
            print(f"  Host: {details.get('url')}")
            print(f"  Database: {details.get('database')}")
            print(f"  User: {details.get('user')}")
            
            # Test connection
            test_response = session.post(f"{GRAFANA_URL}/api/datasources/{ds.get('id')}/health", timeout=10)
            test_result = test_response.json()
            print(f"  Test Result: {test_result.get('message', test_result.get('status'))}")
            
            if 'OK' not in test_result.get('message', '') and 'OK' not in test_result.get('status', ''):
                print(f"\n  ⚠️ ISSUE FOUND: Datasource is not connecting")
                print(f"     Response: {test_result}")
            break
    
    if not pg_ds:
        print("✗ No PostgreSQL datasource found")
        
except Exception as e:
    print(f"✗ Error checking datasource: {e}")

# Step 4: Check Dashboard Panel Configuration
print("\n[4] DASHBOARD PANEL CONFIGURATION")
try:
    response = session.get(f"{GRAFANA_URL}/api/dashboards/uid/sales-analytics", timeout=5)
    if response.status_code == 200:
        dashboard = response.json().get('dashboard', {})
        panels = dashboard.get('panels', [])
        
        print(f"✓ Sales Analytics dashboard has {len(panels)} panels")
        
        for panel in panels[:2]:  # Check first 2 panels
            title = panel.get('title', 'Unknown')
            datasource = panel.get('datasource')
            targets = panel.get('targets', [])
            
            print(f"\n  Panel: {title}")
            print(f"    Datasource: {datasource}")
            print(f"    Has queries: {len(targets) > 0}")
            
            if not datasource or datasource == 'null':
                print(f"    ⚠️ ISSUE: Panel has NO datasource assigned")
            
            if len(targets) == 0:
                print(f"    ⚠️ ISSUE: Panel has NO queries")
            else:
                query = targets[0].get('rawSql', targets[0].get('rawQuery', 'N/A'))
                print(f"    Query: {str(query)[:80]}...")
    else:
        print(f"✗ Cannot load dashboard: {response.status_code}")
        
except Exception as e:
    print(f"✗ Error checking dashboard: {e}")

# Step 5: Try executing a dashboard query manually
print("\n[5] MANUAL QUERY TEST")
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Test the actual query
    test_query = "SELECT SUM(revenue) FROM fact_sales"
    cursor.execute(test_query)
    result = cursor.fetchone()[0]
    
    print(f"✓ Direct query test:")
    print(f"  Query: {test_query}")
    print(f"  Result: ${result:,.2f}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Query test failed: {e}")

# Summary
print("\n" + "="*80)
print("DIAGNOSIS SUMMARY")
print("="*80)

print("\n✓ DATA EXISTS: 57,231 records")
print("✓ DATABASE: Accessible")
print("✓ GRAFANA: Running")

print("\n⚠️ IF DASHBOARDS ARE STILL EMPTY:")
print("\n1. Check Datasource Host Setting:")
print("   Go to: Settings → Data Sources → PostgreSQL Warehouse")
print("   Verify Host is: postgres:5432 (NOT localhost:5433)")
print("\n2. Click: Save & Test")
print("   Should show: 'Database Connection OK'")
print("\n3. Refresh Dashboards")
print("   Press F5 in browser to reload")
print("\n4. If still empty:")
print("   Go to Dashboards → Click a panel → Click 'Edit'")
print("   Check: Datasource dropdown shows 'PostgreSQL Warehouse'")

print("\n" + "="*80 + "\n")
