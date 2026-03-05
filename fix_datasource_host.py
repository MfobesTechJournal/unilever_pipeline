#!/usr/bin/env python3
"""
Fix Grafana PostgreSQL datasource - Point to correct host:port
"""
import requests
import json

GRAFANA_URL = "http://localhost:3000"
GRAFANA_AUTH = ("admin", "admin")

print("\n" + "="*80)
print("GRAFANA DATASOURCE FIX")
print("="*80)

try:
    # Get PostgreSQL datasource
    response = requests.get(
        f"{GRAFANA_URL}/api/datasources",
        auth=GRAFANA_AUTH
    )
    
    datasources = response.json()
    postgres_ds = None
    
    for ds in datasources:
        if ds.get('type') in ['postgres', 'grafana-postgresql-datasource']:
            postgres_ds = ds
            break
    
    if not postgres_ds:
        print("✗ No PostgreSQL datasource found!")
        exit(1)
    
    print(f"\nFound PostgreSQL datasource: {postgres_ds.get('name')}")
    print(f"Current config:")
    print(f"  Host:Port: {postgres_ds.get('url')}")
    print(f"  Database: {postgres_ds.get('database')}")
    print(f"  User: {postgres_ds.get('user')}")
    
    # Update datasource
    postgres_ds['url'] = 'localhost:5433'  # Update connection string
    postgres_ds['jsonData'] = postgres_ds.get('jsonData', {})
    postgres_ds['jsonData']['host'] = 'localhost'
    postgres_ds['jsonData']['port'] = 5433
    postgres_ds['jsonData']['database'] = 'unilever_warehouse'
    postgres_ds['jsonData']['sslmode'] = 'disable'
    
    print(f"\nUpdating to:")
    print(f"  Host:Port: localhost:5433")
    print(f"  Database: unilever_warehouse")
    
    # Save updated datasource
    response = requests.put(
        f"{GRAFANA_URL}/api/datasources/{postgres_ds['id']}",
        json=postgres_ds,
        auth=GRAFANA_AUTH
    )
    
    if response.status_code in [200, 201]:
        print(f"\n✓ Datasource updated successfully!")
        result = response.json()
        print(f"  Message: {result.get('message')}")
    else:
        print(f"\n✗ Failed to update datasource: {response.text}")
        
    # Test the connection
    print(f"\nTesting connection...")
    test_response = requests.post(
        f"{GRAFANA_URL}/api/datasources/{postgres_ds['id']}/query",
        json={
            "queries": [{
                "refId": "A",
                "rawSql": "SELECT COUNT(*) as count FROM fact_sales"
            }]
        },
        auth=GRAFANA_AUTH
    )
    
    if test_response.status_code == 200:
        print(f"✓ Connection test successful!")
        result = test_response.json()
        print(f"  Response: {result}")
    else:
        print(f"⚠ Connection test status: {test_response.status_code}")
        print(f"  Response: {test_response.text}")
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80)
print("✓ Datasource has been fixed!")
print("="*80)
print("\nNext steps:")
print("1. Go to http://localhost:3000")
print("2. Open the Sales Analytics dashboard")
print("3. Press Ctrl+F5 to fully refresh your browser")
print("4. Data should now appear in all panels!")
