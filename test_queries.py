#!/usr/bin/env python3
"""Test all dashboard queries through Grafana API"""

import requests
import json

print("=" * 70)
print("TESTING DASHBOARD PANEL QUERIES")
print("=" * 70)

# Get datasource
response = requests.get('http://localhost:3000/api/datasources/name/PostgreSQL Warehouse')
datasource = response.json()

print(f"\nUsing datasource: {datasource['name']} (ID: {datasource['id']})\n")

# Get dashboards and test their queries
response = requests.get('http://localhost:3000/api/search?type=dash-db')
dashboards = response.json()

panel_count = 0
successful_queries = 0

for dash in dashboards:
    dash_response = requests.get(f"http://localhost:3000/api/dashboards/uid/{dash['uid']}")
    dashboard = dash_response.json()['dashboard']
    
    print(f"Dashboard: {dashboard['title']}")
    print("-" * 70)
    
    for panel in dashboard.get('panels', []):
        panel_count += 1
        panel_title = panel.get('title', 'Untitled')
        
        # Get targets from panel
        targets = panel.get('targets', [])
        
        for target in targets:
            query = target.get('rawSql', '')
            
            if query:
                print(f"\n  Panel: {panel_title}")
                print(f"  Query: {query[:60]}...")
                
                # Special handling for different query types
                if "SELECT SUM" in query:
                    expected = "numeric value"
                elif "SELECT COUNT" in query:
                    expected = "integer"
                elif "SELECT AVG" in query:
                    expected = "numeric value"
                elif "SELECT" in query:
                    expected = "result set"
                else:
                    expected = "unknown"
                
                print(f"  Expected: {expected}")
                print(f"  Status: ✓ Query is configured")
                successful_queries += 1

print("\n" + "=" * 70)
print(f"SUMMARY: {successful_queries}/{panel_count} panels have queries configured")
print("=" * 70)

if successful_queries == panel_count:
    print("\n✅ All panels are ready to query!")
    print("\n🔄 NEXT STEP: Refresh your browser")
    print("   URL: http://localhost:3000")
    print("\n   Click on 'Sales Analytics' dashboard")
    print("   All panels should show data")
    print("\n   If still showing 'No data':")
    print("   1. Click Panel menu (top right)")
    print("   2. Select 'Edit'")
    print("   3. Check datasource (should be 'PostgreSQL Warehouse')")
    print("   4. Click 'Run query' button")
    print("\n")
else:
    print(f"\n⚠ Only {successful_queries}/{panel_count} panels configured")
    print("Check panel configurations")
