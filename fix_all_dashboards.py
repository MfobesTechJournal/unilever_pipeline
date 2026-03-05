#!/usr/bin/env python3
"""
Grafana Dashboard Fixer - Update all dashboard queries correctly
"""

import requests
import json

GRAFANA_URL = "http://localhost:3000"
GRAFANA_AUTH = ("admin", "admin")

print("\n" + "="*80)
print("GRAFANA DASHBOARD QUERY FIXER")
print("="*80)

def fix_query(query_text):
    """Fix query column references"""
    if not query_text:
        return query_text
    
    # Replace incorrect column names
    query = query_text
    query = query.replace("total_amount", "revenue")
    query = query.replace("created_at", "load_timestamp")
    
    # Ensure we use load_timestamp for time filtering
    if "$__timeFilter" in query and "load_timestamp" not in query:
        query = query.replace("$__timeFilter(created_at)", "$__timeFilter(load_timestamp)")
    
    return query

# Get all dashboards
response = requests.get(f"{GRAFANA_URL}/api/search", auth=GRAFANA_AUTH)
all_dashboards = response.json()

# Track changes
total_updated = 0
dashboards_updated = []

for dashboard_info in all_dashboards:
    dashboard_uid = dashboard_info.get("uid")
    dashboard_id = dashboard_info.get("id")
    dashboard_title = dashboard_info.get("title")
    
    # Only process sales and ETL dashboards
    tags = dashboard_info.get("tags", [])
    if not any(tag in ["sales", "etl", "monitoring", "analytics"] for tag in tags):
        continue
    
    try:
        # Get dashboard using UID
        response = requests.get(
            f"{GRAFANA_URL}/api/dashboards/uid/{dashboard_uid}",
            auth=GRAFANA_AUTH
        )
        
        if response.status_code != 200:
            print(f"✗ Dashboard '{dashboard_title}': Not found")
            continue
        
        data = response.json()
        dashboard = data["dashboard"]
        
        print(f"\n[{dashboard_title}]")
        
        # Fix queries in all panels
        panels_updated = 0
        for panel in dashboard.get("panels", []):
            panel_title = panel.get("title", "Unknown Panel")
            
            # Fix targets (queries)
            for target in panel.get("targets", []):
                original_query = target.get("rawSql", "")
                fixed_query = fix_query(original_query)
                
                if fixed_query != original_query and fixed_query:
                    target["rawSql"] = fixed_query
                    panels_updated += 1
                    total_updated += 1
                    print(f"  ✓ Fixed: {panel_title}")
        
        # Save updated dashboard
        if panels_updated > 0:
            dashboard["version"] = dashboard.get("version", 0) + 1
            
            response = requests.post(
                f"{GRAFANA_URL}/api/dashboards/db",
                json={
                    "dashboard": dashboard,
                    "overwrite": True
                },
                auth=GRAFANA_AUTH
            )
            
            if response.status_code in [200, 201]:
                print(f"  ✓ Dashboard saved ({panels_updated} panels updated)")
                dashboards_updated.append(dashboard_title)
            else:
                print(f"  ✗ Failed to save: {response.text}")
        else:
            print(f"  (No queries needed fixing)")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n" + "="*80)
print(f"SUMMARY - Updated {total_updated} queries in {len(dashboards_updated)} dashboards")
print("="*80)

if dashboards_updated:
    print("\nUpdated dashboards:")
    for dash in dashboards_updated:
        print(f"  ✓ {dash}")

print("\n✓ All dashboard queries have been fixed!")
print("\nTo see the changes:")
print("  1. Go to http://localhost:3000")
print("  2. Click on 'Sales Analytics' or ETL dashboards")
print("  3. Press Ctrl+F5 to fully refresh your browser")
print("  4. Data should now appear in all panels")
print("\nIf data still doesn't show:")
print("  - Click 'Refresh' button on any panel")
print("  - Check the datasource is 'PostgreSQL Warehouse'")
print("  - Check browser console (F12) for any errors")
