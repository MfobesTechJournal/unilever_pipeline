#!/usr/bin/env python3
"""Check available datasource plugins and recreate with correct type"""

import requests
import json

print("=" * 70)
print("CHECKING DATASOURCE PLUGINS")
print("=" * 70)

# Get list of plugins
print("\n1. AVAILABLE DATASOURCE PLUGINS")
print("-" * 70)

response = requests.get('http://localhost:3000/api/plugins')
plugins = response.json()

print("Datasource plugins available:")
for plugin in plugins:
    if plugin.get('type') == 'datasource':
        print(f"  • {plugin.get('id'):40} - {plugin.get('name')}")

# Check specifically for postgres
print("\n2. CHECKING FOR POSTGRES PLUGIN")
print("-" * 70)

response = requests.get('http://localhost:3000/api/plugins/postgres')
if response.status_code == 200:
    plugin = response.json()
    print(f"✓ 'postgres' plugin found")
    print(f"  Name: {plugin.get('name')}")
    print(f"  ID: {plugin.get('id')}")
    print(f"  Type: {plugin.get('type')}")
else:
    print(f"✗ 'postgres' plugin not found: {response.status_code}")

# Check for grafana-postgresql-datasource
print("\n3. CHECKING FOR GRAFANA POSTGRESQL DATASOURCE PLUGIN")
print("-" * 70)

response = requests.get('http://localhost:3000/api/plugins/grafana-postgresql-datasource')
if response.status_code == 200:
    plugin = response.json()
    print(f"✓ Plugin found")
    print(f"  Name: {plugin.get('name')}")
    print(f"  ID: {plugin.get('id')}")
    print(f"  Type: {plugin.get('type')}")
else:
    print(f"✗ Plugin not found: {response.status_code}")

# List all datasource types across all datasources
print("\n4. CURRENT DATASOURCES AND THEIR TYPES")
print("-" * 70)

response = requests.get('http://localhost:3000/api/datasources')
datasources = response.json()

for ds in datasources:
    print(f"  • {ds['name']:30} - Type: {ds['type']}")

print("\n" + "=" * 70)
