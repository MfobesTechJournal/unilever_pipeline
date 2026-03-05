#!/usr/bin/env python3
"""
Fix PostgreSQL datasource - add missing database configuration
"""

import requests
import json

GRAFANA_URL = "http://localhost:3000"
session = requests.Session()
session.auth = ("admin", "admin")

print("\n" + "="*80)
print("FIXING POSTGRESQL DATASOURCE DATABASE CONFIGURATION")
print("="*80)

print("\nGetting datasource configuration...")
response = session.get(f"{GRAFANA_URL}/api/datasources/5")

if response.status_code == 200:
    datasource = response.json()
    
    print(f"\nBefore:")
    print(f"  Database: '{datasource.get('database')}'")
    print(f"  URL: '{datasource.get('url')}'")
    
    # Fix the datasource
    datasource['database'] = 'unilever_warehouse'
    datasource['url'] = 'postgres:5432'
    datasource['user'] = 'postgres'
    
    if 'secureJsonData' not in datasource:
        datasource['secureJsonData'] = {}
    datasource['secureJsonData']['password'] = '123456'
    
    if 'jsonData' not in datasource:
        datasource['jsonData'] = {}
    datasource['jsonData']['sslmode'] = 'disable'
    datasource['jsonData']['postgresVersion'] = 1400
    
    # Update
    update_response = session.put(
        f"{GRAFANA_URL}/api/datasources/5",
        json=datasource
    )
    
    if update_response.status_code in [200, 201]:
        print(f"\nAfter:")
        print(f"  Database: 'unilever_warehouse'")
        print(f"  URL: 'postgres:5432'")
        print("✓ Datasource updated!")
        
        # Test
        print("\nTesting connection...")
        test_resp = session.post(f"{GRAFANA_URL}/api/datasources/5/health", timeout=10)
        test_data = test_resp.json()
        msg = test_data.get('message', 'Unknown')
        print(f"  Result: {msg}")
        
        if 'OK' in msg:
            print("\n✓✓✓ CONNECTION WORKING! ✓✓✓")
            print("\nGo to http://localhost:3000 → Dashboards → Sales Analytics")
            print("Refresh with Ctrl+F5")
            print("Data should now appear!")
        
    else:
        print(f"✗ Failed to update: {update_response.status_code}")

print("\n" + "="*80 + "\n")
