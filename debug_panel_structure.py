#!/usr/bin/env python3
import requests
import json

try:
    # Get Sales Analytics dashboard
    response = requests.get(
        'http://localhost:3000/api/dashboards/uid/sales-analytics-v2',
        auth=('admin', 'admin')
    )
    
    data = response.json()
    dashboard = data["dashboard"]
    
    print("Sales Analytics Dashboard Structure:")
    print(f"Panels count: {len(dashboard.get('panels', []))}")
    print()
    
    # Check first panel structure
    for idx, panel in enumerate(dashboard.get('panels', [])[:3]):
        print(f"\nPanel {idx}: {panel.get('title')}")
        print(f"  Type: {panel.get('type')}")
        print(f"  Targets: {panel.get('targets', [])}")
        if panel.get('targets'):
            print(f"  First target keys: {list(panel['targets'][0].keys())}")
            print(f"  First target: {json.dumps(panel['targets'][0], indent=4)}")
        
except Exception as e:
    print(f"Error: {e}")
