#!/usr/bin/env python3
"""
Import Grafana dashboards via API
"""
import requests
import json
import os
from pathlib import Path

GRAFANA_URL = "http://localhost:3000"
GRAFANA_API_KEY = "admin:admin"  # User and password
DASHBOARDS_DIR = Path(__file__).parent / "grafana" / "dashboards"

def import_dashboard(dashboard_file):
    """Import a single dashboard"""
    print(f"Importing {dashboard_file.name}...")
    
    with open(dashboard_file, 'r') as f:
        dashboard = json.load(f)
    
    # Prepare the import request
    payload = {
        "dashboard": dashboard,
        "overwrite": True,
        "message": f"Auto-imported {dashboard_file.name}"
    }
    
    try:
        response = requests.post(
            f"{GRAFANA_URL}/api/dashboards/db",
            json=payload,
            auth=("admin", "admin"),
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✓ Successfully imported {dashboard_file.name}")
            print(f"  Dashboard ID: {result.get('id')}")
            print(f"  URL: {result.get('url')}")
            return True
        else:
            print(f"✗ Failed to import {dashboard_file.name}")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error importing {dashboard_file.name}: {e}")
        return False

def main():
    """Main function"""
    print(f"Importing dashboards from {DASHBOARDS_DIR}")
    print(f"Grafana URL: {GRAFANA_URL}\n")
    
    # Find all JSON dashboard files
    dashboard_files = list(DASHBOARDS_DIR.glob("*.json"))
    
    if not dashboard_files:
        print("No dashboard files found!")
        return
    
    success_count = 0
    for dashboard_file in sorted(dashboard_files):
        if import_dashboard(dashboard_file):
            success_count += 1
    
    print(f"\n✓ Successfully imported {success_count}/{len(dashboard_files)} dashboards")

if __name__ == "__main__":
    main()
