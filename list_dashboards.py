#!/usr/bin/env python3
import requests
import json

try:
    r = requests.get('http://localhost:3000/api/search', auth=('admin', 'admin'))
    dashboards = r.json()
    
    if dashboards:
        print("Grafana Dashboards:")
        for d in dashboards:
            print(f"  - {d.get('title')} (ID: {d.get('id')})")
    else:
        print("No dashboards found")
        
except Exception as e:
    print(f"Error: {e}")
