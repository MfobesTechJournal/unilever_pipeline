#!/usr/bin/env python3
import requests
import json

GRAFANA_URL = "http://localhost:3000"
GRAFANA_AUTH = ("admin", "admin")

# Get Sales Analytics dashboard queries
print("\n" + "="*80)
print("SALES ANALYTICS DASHBOARD - QUERIES")
print("="*80)

try:
    response = requests.get(
        f"{GRAFANA_URL}/api/dashboards/uid/sales-analytics-v2",
        auth=GRAFANA_AUTH
    )
    
    data = response.json()
    dashboard = data["dashboard"]
    
    print(f"\nDashboard: {dashboard.get('title')}")
    print(f"Panels: {len(dashboard.get('panels', []))}")
    
    for idx, panel in enumerate(dashboard.get('panels', [])):
        print(f"\n[Panel {idx}] {panel.get('title')}")
        print(f"  Type: {panel.get('type')}")
        
        for target_idx, target in enumerate(panel.get('targets', [])):
            print(f"  Target {target_idx}:")
            print(f"    Query: {target.get('rawSql', 'N/A')[:150]}")
            
except Exception as e:
    print(f"Error: {e}")

# Get ETL Monitoring dashboard queries
print("\n" + "="*80)
print("ETL MONITORING DASHBOARD - QUERIES (First 3 Panels)")
print("="*80)

try:
    response = requests.get(
        f"{GRAFANA_URL}/api/dashboards/uid/etl-monitoring-v2",
        auth=GRAFANA_AUTH
    )
    
    data = response.json()
    dashboard = data["dashboard"]
    
    print(f"\nDashboard: {dashboard.get('title')}")
    print(f"Total Panels: {len(dashboard.get('panels', []))}")
    
    for idx, panel in enumerate(dashboard.get('panels', [])[:3]):
        print(f"\n[Panel {idx}] {panel.get('title')}")
        print(f"  Type: {panel.get('type')}")
        
        for target_idx, target in enumerate(panel.get('targets', [])):
            query = target.get('rawSql', 'N/A')
            if query != 'N/A':
                print(f"  Target {target_idx}:")
                print(f"    {query[:200]}")
            
except Exception as e:
    print(f"Error: {e}")
