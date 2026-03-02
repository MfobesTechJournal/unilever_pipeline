#!/usr/bin/env python3
"""Update dashboard JSON to add datasource references to panels"""

import json

# Update Sales Analytics dashboard
sales_file = '11-infrastructure/network/grafana/dashboards/sales-analytics.json'

with open(sales_file, 'r') as f:
    sales_dashboard = json.load(f)

# Add datasource to all panels
for panel in sales_dashboard.get('panels', []):
    if not panel.get('datasource'):
        panel['datasource'] = 'PostgreSQL Warehouse'

# Write back
with open(sales_file, 'w') as f:
    json.dump(sales_dashboard, f, indent=2)

print(f"Updated {sales_file}")
print(f"  Added datasource reference to {len(sales_dashboard.get('panels', []))} panels")

# Update ETL Monitoring dashboard
etl_file = '11-infrastructure/network/grafana/dashboards/etl-monitoring.json'

with open(etl_file, 'r') as f:
    etl_dashboard = json.load(f)

# Add datasource to all panels
for panel in etl_dashboard.get('panels', []):
    if not panel.get('datasource'):
        panel['datasource'] = 'PostgreSQL Warehouse'

# Write back
with open(etl_file, 'w') as f:
    json.dump(etl_dashboard, f, indent=2)

print(f"\nUpdated {etl_file}")
print(f"  Added datasource reference to {len(etl_dashboard.get('panels', []))} panels")

print("\n✓ Dashboard updates completed")
