#!/usr/bin/env python3
"""Verify Grafana dashboards are created and accessible"""

import requests
import json

print("=" * 60)
print("GRAFANA DASHBOARD VERIFICATION")
print("=" * 60)

try:
    # List all dashboards
    print("\n✓ Checking dashboards...")
    response = requests.get('http://localhost:3000/api/search?type=dash-db')
    
    if response.status_code == 200:
        dashboards = response.json()
        print(f"\n✓ Found {len(dashboards)} dashboard(s):\n")
        
        for dash in dashboards:
            print(f"  • {dash['title']}")
            print(f"    URL: /d/{dash['uid']}")
            
            # Get dashboard details
            dash_response = requests.get(f"http://localhost:3000/api/dashboards/uid/{dash['uid']}")
            if dash_response.status_code == 200:
                dash_detail = dash_response.json()
                panels = dash_detail['dashboard'].get('panels', [])
                print(f"    Panels: {len(panels)}")
                for panel in panels:
                    print(f"      - {panel.get('title', 'Untitled')}")
            print()
        
        print("=" * 60)
        print("✓ SUCCESS: Dashboards are ready!")
        print("=" * 60)
        print("\nAccess Grafana at: http://localhost:3000")
        print("Select a dashboard to view the data")
            
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"✗ Error: {e}")
