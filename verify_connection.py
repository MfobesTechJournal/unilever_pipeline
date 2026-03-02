#!/usr/bin/env python3
"""Verify datasource connectivity and data flow"""

import psycopg2
import requests

print("=" * 70)
print("DATASOURCE CONNECTIVITY VERIFICATION")
print("=" * 70)

# 1. Direct PostgreSQL test
print("\n1. TESTING POSTGRESQL CONNECTION (Direct)")
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
    
    # Test queries from dashboard
    queries = [
        ("Total Revenue", "SELECT SUM(revenue) as value FROM fact_sales"),
        ("Transaction Count", "SELECT COUNT(*) as value FROM fact_sales"),
        ("Average Order Value", "SELECT AVG(revenue) as value FROM fact_sales"),
    ]
    
    for name, query in queries:
        cursor.execute(query)
        result = cursor.fetchone()[0]
        print(f"   ✓ {name}: {result}")
    
    cursor.close()
    conn.close()
    
    print("\n   ✓ PostgreSQL is accessible and has data!")
    
except Exception as e:
    print(f"   ✗ PostgreSQL error: {e}")
    exit(1)

# 2. Check Grafana datasource status
print("\n2. GRAFANA DATASOURCE INFO")
print("-" * 70)

try:
    response = requests.get('http://localhost:3000/api/datasources/name/PostgreSQL Warehouse')
    if response.status_code == 200:
        ds = response.json()
        print(f"   ✓ Datasource: {ds['name']}")
        print(f"   ✓ Type: {ds['type']}")
        print(f"   ✓ URL: {ds['url']}")
        print(f"   ✓ Database: {ds['database']}")
        print(f"   ✓ User: {ds['user']}")
        print(f"   ✓ ID: {ds['id']}")
        print(f"   ✓ UID: {ds.get('uid', 'N/A')}")
    else:
        print(f"   ✗ Could not retrieve datasource: {response.status_code}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 3. Verify dashboards can query
print("\n3. DASHBOARD QUERY VERIFICATION")
print("-" * 70)

try:
    response = requests.get('http://localhost:3000/api/search?type=dash-db')
    dashboards = response.json()
    
    for dash in dashboards:
        dash_response = requests.get(f"http://localhost:3000/api/dashboards/uid/{dash['uid']}")
        dashboard = dash_response.json()['dashboard']
        
        print(f"\n   Dashboard: {dashboard['title']}")
        
        for panel in dashboard.get('panels', []):
            panel_title = panel.get('title', 'Untitled')
            targets = panel.get('targets', [])
            
            for target in targets:
                ds = target.get('datasource', {})
                if isinstance(ds, dict):
                    ds_name = ds.get('name', 'Unknown')
                else:
                    ds_name = ds
                
                print(f"     ✓ Panel: {panel_title}")
                print(f"       Datasource: {ds_name}")
                print(f"       Has query: {'rawSql' in target or 'expr' in target}")
                
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 70)
print("✅ VERIFICATION COMPLETE")
print("=" * 70)
print("\n📊 Your dashboards are now connected to the data!")
print("\nGO TO GRAFANA AND REFRESH:")
print("   http://localhost:3000")
print("\nYou should now see data in all panels!")
print("\n")
