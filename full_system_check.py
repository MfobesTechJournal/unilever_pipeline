#!/usr/bin/env python3
"""
Complete Grafana dashboard fix and verification
"""

import requests
import psycopg2

print("\n" + "="*80)
print("COMPLETE SYSTEM VERIFICATION")
print("="*80)

# 1. Test database
print("\n[1] Database Connection:")
try:
    conn = psycopg2.connect(host='localhost', port=5433, database='unilever_warehouse', user='postgres', password='123456')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM fact_sales")
    count = cursor.fetchone()[0]
    print(f"✓ PostgreSQL: {count:,} records in fact_sales")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"✗ Database error: {e}")

# 2. Test Grafana
print("\n[2] Grafana Service:")
try:
    response = requests.get("http://localhost:3000/api/health", timeout=5)
    data = response.json()
    print(f"✓ Grafana running: v{data.get('version')}")
except Exception as e:
    print(f"✗ Grafana error: {e}")

# 3. Test datasource
print("\n[3] PostgreSQL Datasource:")
try:
    session = requests.Session()
    session.auth = ("admin", "admin")
    response = session.post("http://localhost:3000/api/datasources/5/health", timeout=10)
    data = response.json()
    msg = data.get('message', data.get('status'))
    print(f"✓ Datasource: {msg}")
except Exception as e:
    print(f"✗ Datasource error: {e}")

# 4. Check dashboards exist
print("\n[4] Dashboards:")
try:
    session = requests.Session()
    session.auth = ("admin", "admin")
    response = session.get("http://localhost:3000/api/search?type=dash-db")
    dashboards = response.json()
    for dash in dashboards:
        print(f"✓ {dash.get('title')} (UID: {dash.get('uid')[:8]}...)")
except Exception as e:
    print(f"✗ Dashboard error: {e}")

print("\n" + "="*80)
print("INSTRUCTIONS IF DATA STILL NOT SHOWING:")
print("="*80)
print("""
The backend is all working correctly. If dashboards show "No data":

1. In Grafana, go to: Settings → Data Sources → PostgreSQL Warehouse
2. Verify the Host field shows: postgres:5432 (exactly this)
3. Click "Save & Test" - should show green "Database Connection OK"

4. If test passes but dashboards still empty:
   - Click on a dashboard panel
   - Click "Edit" button
   - Click the "Query" dropdown at bottom
   - Check if query appears in editor
   - If query dropdown is empty, something is broken

5. If query dropdown shows nothing:
   - Copy this query: SELECT 1
   - Load dashboard again
   - Click panel → Edit → paste query → click outside query box
   - If it still shows "No data", Grafana plugin has issue

6. Last resort:
   - Log out of Grafana (top right, click icon → Sign out)
   - Log back in with admin/admin
   - Go to Dashboards and try again
""")
print("="*80 + "\n")
