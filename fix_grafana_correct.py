#!/usr/bin/env python3
"""
Grafana Dashboard Fix - Correct Column Names
"""

import psycopg2
import json
import requests

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "unilever_warehouse",
    "user": "postgres",
    "password": "123456"
}

GRAFANA_URL = "http://localhost:3000"
GRAFANA_AUTH = ("admin", "admin")

print("\n" + "="*80)
print("GRAFANA DASHBOARD FIX - CORRECT COLUMN NAMES")
print("="*80)

# Step 1: Verify data exists
print("\n[STEP 1] VERIFYING DATA")
print("-" * 80)

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM fact_sales")
    record_count = cursor.fetchone()[0]
    print(f"✓ fact_sales has {record_count:,} records")
    
    cursor.execute("SELECT MIN(load_timestamp), MAX(load_timestamp) FROM fact_sales")
    min_ts, max_ts = cursor.fetchone()
    print(f"✓ Date range: {min_ts} to {max_ts}")
    
    cursor.execute("SELECT SUM(revenue) as total_revenue, AVG(revenue) as avg_revenue FROM fact_sales")
    total, avg = cursor.fetchone()
    print(f"✓ Revenue stats - Total: ${total:,.2f}, Average: ${avg:.2f}")
    
    conn.close()
    print("✓ Data verification successful!")
    
except Exception as e:
    print(f"✗ Data verification failed: {e}")

# Step 2: Test queries on actual columns
print("\n[STEP 2] TESTING QUERIES WITH CORRECT COLUMNS")
print("-" * 80)

test_queries = {
    "Total Revenue": "SELECT SUM(revenue) as value FROM fact_sales",
    "Total Transactions": "SELECT COUNT(*) as value FROM fact_sales",
    "Average Order Value": "SELECT AVG(revenue) as value FROM fact_sales",
    "Daily Sales": """
        SELECT DATE(load_timestamp) as time, SUM(revenue) as value
        FROM fact_sales
        GROUP BY DATE(load_timestamp)
        ORDER BY time DESC
    """,
}

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    for name, query in test_queries.items():
        try:
            cursor.execute(query)
            result = cursor.fetchone()
            print(f"✓ {name}: OK (sample: {result})")
        except Exception as e:
            print(f"✗ {name}: {e}")
    
    conn.close()
except Exception as e:
    print(f"✗ Query test failed: {e}")

# Step 3: Get Grafana dashboards and fix them
print("\n[STEP 3] UPDATING GRAFANA DASHBOARDS")
print("-" * 80)

try:
    # Get all dashboards
    response = requests.get(f"{GRAFANA_URL}/api/search", auth=GRAFANA_AUTH, params={"query": ""})
    dashboards = response.json()
    
    for dashboard_info in dashboards:
        if "sales" in dashboard_info.get("title", "").lower() or "etl" in dashboard_info.get("title", "").lower():
            dashboard_id = dashboard_info["id"]
            dashboard_title = dashboard_info["title"]
            
            # Get dashboard details
            response = requests.get(f"{GRAFANA_URL}/api/dashboards/id/{dashboard_id}", auth=GRAFANA_AUTH)
            dashboard = response.json()["dashboard"]
            
            updated = False
            
            # Fix each panel's queries
            for panel in dashboard.get("panels", []):
                for target in panel.get("targets", []):
                    old_query = target.get("rawSql", "")
                    new_query = old_query
                    
                    # Replace incorrect column references
                    new_query = new_query.replace("total_amount", "revenue")
                    new_query = new_query.replace("created_at", "load_timestamp")
                    
                    if new_query != old_query:
                        target["rawSql"] = new_query
                        updated = True
                        print(f"  ✓ Updated panel: {panel.get('title', 'Unknown')}")
            
            # Update dashboard if changes were made
            if updated:
                response = requests.post(
                    f"{GRAFANA_URL}/api/dashboards/db",
                    json={"dashboard": dashboard, "overwrite": True},
                    auth=GRAFANA_AUTH
                )
                
                if response.status_code in [200, 201]:
                    print(f"✓ Updated dashboard: {dashboard_title}")
                else:
                    print(f"✗ Failed to update {dashboard_title}: {response.text}")
    
except Exception as e:
    print(f"✗ Dashboard update failed: {e}")
    
# Step 4: Test Grafana connection
print("\n[STEP 4] VERIFYING GRAFANA CONNECTION")
print("-" * 80)

try:
    # Check datasources
    response = requests.get(f"{GRAFANA_URL}/api/datasources", auth=GRAFANA_AUTH)
    datasources = response.json()
    
    for ds in datasources:
        if "postgres" in ds.get("type", "").lower():
            # Test datasource
            response = requests.post(
                f"{GRAFANA_URL}/api/datasources/{ds['id']}/query",
                json={
                    "queries": [{"refId": "A", "rawSql": "SELECT 1"}]
                },
                auth=GRAFANA_AUTH
            )
            if response.status_code == 200:
                print(f"✓ PostgreSQL datasource '{ds['name']}' is working")
            else:
                print(f"⚠ PostgreSQL datasource issue: {response.text}")
except Exception as e:
    print(f"⚠ Could not verify Grafana: {e}")

print("\n" + "="*80)
print("FIX COMPLETE - Data should now show in Grafana!")
print("="*80)
print("\nNext steps:")
print("1. Go to http://localhost:3000")
print("2. Open your Sales dashboard")
print("3. Press Ctrl+F5 to fully refresh the browser")
print("4. All panels should now show data")
print("\nIf panels are still empty:")
print("- Click 'Refresh' button on the panel")
print("- Check the panel's query editor (click Edit)")
print("- Ensure the datasource is set to 'PostgreSQL Warehouse'")
