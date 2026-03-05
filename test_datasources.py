#!/usr/bin/env python3
"""
Check Grafana datasources and test connections
"""
import requests
import json

GRAFANA_URL = "http://localhost:3000"
GRAFANA_AUTH = ("admin", "admin")

print("\n" + "="*80)
print("GRAFANA DATASOURCE VERIFICATION")
print("="*80)

try:
    # Get all datasources
    response = requests.get(
        f"{GRAFANA_URL}/api/datasources",
        auth=GRAFANA_AUTH
    )
    
    datasources = response.json()
    print(f"\nFound {len(datasources)} datasource(s)")
    
    for ds in datasources:
        print(f"\n[{ds.get('name')}]")
        print(f"  Type: {ds.get('type')}")
        print(f"  UID: {ds.get('uid')}")
        print(f"  URL: {ds.get('url')}")
        print(f"  Database: {ds.get('database')}")
        print(f"  User: {ds.get('secureJsonFields', {}).get('password', 'Not set')}")
        
        # Test datasource
        if ds.get('type') == 'postgres':
            print(f"\n  Testing connection...")
            test_response = requests.post(
                f"{GRAFANA_URL}/api/datasources/{ds['id']}/query",
                json={
                    "queries": [{
                        "refId": "A",
                        "rawSql": "SELECT COUNT(*) as count FROM fact_sales"
                    }]
                },
                auth=GRAFANA_AUTH
            )
            
            print(f"    Status: {test_response.status_code}")
            if test_response.status_code == 200:
                result = test_response.json()
                print(f"    Result: {json.dumps(result, indent=6)}")
            else:
                print(f"    Error: {test_response.text}")
                
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80)
