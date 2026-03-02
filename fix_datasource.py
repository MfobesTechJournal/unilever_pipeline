#!/usr/bin/env python3
"""Fix Grafana PostgreSQL datasource configuration"""

import requests
import json

print("=" * 70)
print("FIXING GRAFANA POSTGRESQL DATASOURCE")
print("=" * 70)

# First, delete the problematic datasource
print("\n1. Removing incorrect datasource...")
response = requests.get('http://localhost:3000/api/datasources/name/PostgreSQL Warehouse')
if response.status_code == 200:
    ds = response.json()
    delete_response = requests.delete(f"http://localhost:3000/api/datasources/{ds['id']}")
    if delete_response.status_code == 200:
        print("   ✓ Old datasource removed")
    else:
        print(f"   ✗ Failed to delete: {delete_response.status_code}")
else:
    print("   ℹ Datasource not found (may already be deleted)")

# Create new datasource with correct configuration
print("\n2. Creating new PostgreSQL datasource...")

datasource_payload = {
    "name": "PostgreSQL Warehouse",
    "type": "postgres",
    "url": "postgres:5432",
    "access": "proxy",
    "isDefault": True,
    "database": "unilever_warehouse",
    "user": "postgres",
    "secureJsonData": {
        "password": "123456"
    },
    "jsonData": {
        "sslmode": "disable",
        "postgresVersion": 1400,
        "maxOpenConns": 100,
        "maxIdleConns": 100,
        "connMaxLifetime": 3600
    }
}

response = requests.post(
    'http://localhost:3000/api/datasources',
    json=datasource_payload
)

if response.status_code == 200:
    result = response.json()
    print(f"   ✓ Datasource created (ID: {result['id']})")
else:
    print(f"   ✗ Failed to create datasource: {response.status_code}")
    print(f"   Error: {response.text}")

# Test the new datasource
print("\n3. Testing datasource connection...")

# Get the datasource ID
response = requests.get('http://localhost:3000/api/datasources/name/PostgreSQL Warehouse')
if response.status_code == 200:
    ds = response.json()
    
    # Test using the health endpoint specific to PostgreSQL
    test_payload = {
        "name": "PostgreSQL Warehouse",
        "type": "postgres",
        "url": "postgres:5432",
        "access": "proxy",
        "database": "unilever_warehouse",
        "user": "postgres",
        "jsonData": {
            "sslmode": "disable"
        },
        "secureJsonData": {
            "password": "123456"
        }
    }
    
    test_response = requests.post(
        f"http://localhost:3000/api/datasources/{ds['id']}/testDatasource",
        json=test_payload
    )
    
    if test_response.status_code == 200:
        print("   ✓ Connection test PASSED")
        print(f"   Response: {test_response.json()}")
    else:
        print(f"   ⚠ Test returned: {test_response.status_code}")
        print(f"   Response: {test_response.text[:200]}")
else:
    print("   ✗ Could not retrieve datasource")

print("\n" + "=" * 70)
print("DATASOURCE CONFIGURATION COMPLETE")
print("=" * 70)
print("\nRefresh Grafana in your browser to see data populate!")
print("\n")
