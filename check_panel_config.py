#!/usr/bin/env python3
import requests
import json

GRAFANA_URL = "http://localhost:3000"
session = requests.Session()
session.auth = ("admin", "admin")

# Get Sales Analytics dashboard
response = session.get(f"{GRAFANA_URL}/api/dashboards/uid/09bb3434-c1a1-4d3e-8d62-d3392e569d89")
if response.status_code == 200:
    dashboard = response.json()
    panel = dashboard['dashboard']['panels'][0]
    
    print("Current Panel Configuration:")
    print(f"Title: {panel.get('title')}")
    print(f"Datasource: {panel.get('datasource')}")
    print(f"Type: {panel.get('type')}")
    print(f"Targets: {json.dumps(panel.get('targets', []), indent=2)}")
