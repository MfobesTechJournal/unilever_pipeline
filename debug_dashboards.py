#!/usr/bin/env python3
import requests
import json

try:
    r = requests.get('http://localhost:3000/api/search', auth=('admin', 'admin'))
    dashboards = r.json()
    
    if dashboards:
        print("Dashboard URIs:")
        for d in dashboards:
            print(f"  - {d.get('title')}: {d.get('uri')}")
            print(f"    Full data: {json.dumps(d, indent=6)}")
            print()
        
except Exception as e:
    print(f"Error: {e}")
