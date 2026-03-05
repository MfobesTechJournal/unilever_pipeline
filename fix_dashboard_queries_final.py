#!/usr/bin/env python3
"""
Update dashboard queries with correct column names
"""

import requests
import json
import time

GRAFANA_URL = "http://localhost:3000"
GRAFANA_AUTH = ("admin", "admin")

print("\n" + "="*80)
print("UPDATING DASHBOARD QUERIES - CORRECT COLUMNS")
print("="*80)

# Wait for Grafana to be ready
print("\nWaiting for Grafana to be ready...")
for attempt in range(30):
    try:
        requests.get(f"{GRAFANA_URL}/api/health", timeout=2)
        print("✓ Grafana is ready!")
        break
    except:
        if attempt % 5 == 0:
            print(f"  Attempt {attempt}...")
        time.sleep(1)
else:
    print("✗ Grafana not responding - Please start it manually at http://localhost:3000")
    exit(1)

# Define query fixes for each dashboard
dashboard_fixes = {
    "sales-analytics-v2": {  # Sales Analytics
        "Total Sales Revenue": "SELECT SUM(revenue) as value FROM fact_sales",
        "Total Transactions": "SELECT COUNT(*) as value FROM fact_sales",
        "Average Order Value": "SELECT AVG(revenue) as value FROM fact_sales",
        "Daily Sales Trend": """
            SELECT DATE(load_timestamp) as time, SUM(revenue) as value
            FROM fact_sales
            GROUP BY DATE(load_timestamp)
            ORDER BY time DESC
        """,
        "Top 10 Products": """
            SELECT dp.product_name, SUM(fs.quantity) as quantity, SUM(fs.revenue) as revenue
            FROM fact_sales fs
            JOIN dim_product dp ON fs.product_key = dp.product_key
            GROUP BY dp.product_name
            ORDER BY revenue DESC
            LIMIT 10
        """,
    },
    "etl-monitoring-v2": {  # ETL Monitoring
        "Pipeline Health Overview": "SELECT COUNT(*) as total FROM etl_log",
        "Success Rate (30d)": """
            SELECT ROUND(100.0 * SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) / 
            NULLIF(COUNT(*), 0), 2) as success_rate
            FROM etl_log
            WHERE start_time >= NOW() - INTERVAL '30 days'
        """,
        "Failed Runs (30d)": """
            SELECT COUNT(*) as failed
            FROM etl_log
            WHERE status != 'success' AND start_time >= NOW() - INTERVAL '30 days'
        """,
        "Avg Run Duration (7d)": """
            SELECT ROUND(AVG(EXTRACT(EPOCH FROM (end_time - start_time)))::NUMERIC, 2) as avg_duration
            FROM etl_log
            WHERE start_time >= NOW() - INTERVAL '7 days'
        """,
        "Records Loaded (Last Run)": """
            SELECT SUM(records_facts) as records_loaded
            FROM etl_log
            ORDER BY start_time DESC
            LIMIT 1
        """,
        "Quality Issues (30d)": """
            SELECT COUNT(*) as issues
            FROM data_quality_log
            WHERE timestamp >= NOW() - INTERVAL '30 days'
        """,
        "Total Runs (All Time)": "SELECT COUNT(*) as total_runs FROM etl_log",
        "Pipeline Run History": """
            SELECT start_time as time, status, COALESCE(records_facts, 0) as records
            FROM etl_log
            ORDER BY start_time DESC
            LIMIT 100
        """,
    }
}

# Process each dashboard
for dashboard_uid, panel_fixes in dashboard_fixes.items():
    print(f"\n[{dashboard_uid}]")
    print("-" * 80)
    
    try:
        # Get dashboard
        response = requests.get(
            f"{GRAFANA_URL}/api/dashboards/uid/{dashboard_uid}",
            auth=GRAFANA_AUTH,
            timeout=5
        )
        
        if response.status_code != 200:
            print(f"✗ Dashboard not found: {response.status_code}")
            continue
        
        data = response.json()
        dashboard = data["dashboard"]
        updated_count = 0
        
        # Update panels
        for panel in dashboard.get("panels", []):
            panel_title = panel.get("title", "")
            
            if panel_title in panel_fixes:
                new_query = panel_fixes[panel_title]
                
                for target in panel.get("targets", []):
                    if "rawSql" in target:
                        target["rawSql"] = new_query
                        updated_count += 1
                        print(f"  ✓ Updated: {panel_title}")
        
        # Save dashboard
        if updated_count > 0:
            dashboard["version"] = dashboard.get("version", 0) + 1
            
            response = requests.post(
                f"{GRAFANA_URL}/api/dashboards/db",
                json={"dashboard": dashboard, "overwrite": True},
                auth=GRAFANA_AUTH,
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                print(f"  ✓ Saved! ({updated_count} panels updated)")
            else:
                print(f"  ⚠ Save status: {response.status_code}")
        else:
            print(f"  (No matching panels found)")
            
    except Exception as e:
        print(f"  ⚠ Error: {e}")

print("\n" + "="*80)
print("✓ DASHBOARD QUERIES UPDATED!")
print("="*80)
print("\nNext steps:")
print("  1. Go to http://localhost:3000")
print("  2. Open 'Sales Analytics' or 'ETL Monitoring' dashboard")
print("  3. Press Ctrl+F5 to fully refresh")
print("  4. Data should now appear in all panels! 📊")
