#!/usr/bin/env python3
"""
Grafana Connection Configuration Helper
Shows current datasource settings and helps troubleshoot connection issues.
"""

import requests
import json
from typing import Dict, Optional

GRAFANA_URL = "http://localhost:3000"
GRAFANA_AUTH = ("admin", "admin")

class GrafanaConnectionHelper:
    """Help configure and verify Grafana connections."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.auth = GRAFANA_AUTH
    
    def check_grafana_access(self) -> bool:
        """Check if Grafana is accessible."""
        try:
            response = self.session.get(f"{GRAFANA_URL}/api/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"✗ Cannot access Grafana: {e}")
            return False
    
    def get_datasources(self) -> list:
        """Get all datasources."""
        try:
            response = self.session.get(f"{GRAFANA_URL}/api/datasources", timeout=5)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"✗ Error fetching datasources: {e}")
            return []
    
    def get_datasource_details(self, ds_id: int) -> Optional[Dict]:
        """Get detailed datasource configuration."""
        try:
            response = self.session.get(f"{GRAFANA_URL}/api/datasources/{ds_id}", timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"✗ Error fetching datasource details: {e}")
            return None
    
    def test_datasource(self, ds_id: int) -> Dict:
        """Test datasource connection."""
        try:
            response = self.session.post(f"{GRAFANA_URL}/api/datasources/{ds_id}/health", timeout=10)
            return response.json()
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
    
    def print_current_configuration(self):
        """Print current Grafana configuration."""
        print("\n" + "="*80)
        print("GRAFANA CONNECTION CONFIGURATION")
        print("="*80)
        
        # Check Grafana access
        print("\n[1] GRAFANA ACCESSIBILITY")
        if not self.check_grafana_access():
            print("✗ Grafana is not accessible at http://localhost:3000")
            print("  Please start Grafana: docker-compose up -d grafana")
            return
        print("✓ Grafana is accessible at http://localhost:3000")
        print("  Admin login: admin / admin")
        
        # Get datasources
        print("\n[2] CURRENT DATASOURCES")
        datasources = self.get_datasources()
        
        if not datasources:
            print("✗ No datasources found")
            print("  Follow the setup instructions below")
            return
        
        postgres_ds = None
        for ds in datasources:
            print(f"\n  • {ds.get('name')} (Type: {ds.get('type')})")
            if ds.get('type') == 'postgres':
                postgres_ds = ds
                print(f"    ID: {ds.get('id')}")
                print(f"    Status: {'✓ Active' if ds.get('isDefault') else 'Configured'}")
        
        if not postgres_ds:
            print("\n✗ PostgreSQL datasource not found!")
            print("  Follow the setup instructions below")
            return
        
        # Get detailed configuration
        print("\n[3] POSTGRESQL DATASOURCE DETAILS")
        details = self.get_datasource_details(postgres_ds.get('id'))
        
        if details:
            print("\n  Current Settings:")
            print(f"  ├─ Name: {details.get('name')}")
            print(f"  ├─ Type: {details.get('type')}")
            print(f"  ├─ Host: {details.get('url')}")
            print(f"  ├─ Database: {details.get('database')}")
            print(f"  ├─ User: {details.get('user')}")
            print(f"  ├─ SSL Mode: {details.get('jsonData', {}).get('sslmode', 'Not Set')}")
            print(f"  ├─ PostgreSQL Version: {details.get('jsonData', {}).get('postgresVersion', 'Not Set')}")
            print(f"  └─ Is Default: {'Yes' if details.get('isDefault') else 'No'}")
        
        # Test connection
        print("\n[4] CONNECTION TEST")
        test_result = self.test_datasource(postgres_ds.get('id'))
        
        if test_result.get('status') == 'OK':
            print(f"✓ {test_result.get('message', 'Database Connection OK')}")
        else:
            print(f"✗ {test_result.get('message', 'Connection Failed')}")
            print("\n  TROUBLESHOOTING:")
            print("  • Verify Host is: postgres:5432 (not localhost:5433)")
            print("  • Verify Database is: unilever_warehouse")
            print("  • Verify User is: postgres")
            print("  • Verify Password is: 123456")
            print("  • Verify SSL Mode is: disable")
            print("  • Verify PostgreSQL version: 14")
        
        # Check dashboards
        print("\n[5] DASHBOARDS STATUS")
        try:
            response = self.session.get(f"{GRAFANA_URL}/api/search?type=dash-db", timeout=5)
            if response.status_code == 200:
                dashboards = response.json()
                print(f"  Found {len(dashboards)} dashboards:")
                for dash in dashboards:
                    print(f"  • {dash.get('title')} (UID: {dash.get('uid')})")
        except Exception as e:
            print(f"  ✗ Error fetching dashboards: {e}")
        
        # Summary
        print("\n" + "="*80)
        print("CONFIGURATION SUMMARY")
        print("="*80)
        
        print("\n✓ REQUIRED SETTINGS (must be exactly as shown):")
        print("  ┌─ Datasource Name: PostgreSQL Warehouse")
        print("  ├─ Type: postgres")
        print("  ├─ Host: postgres:5432          ← CRITICAL: NOT localhost:5433")
        print("  ├─ Database: unilever_warehouse")
        print("  ├─ User: postgres")
        print("  ├─ Password: 123456")
        print("  ├─ SSL Mode: disable")
        print("  └─ PostgreSQL Version: 14")
        
        if postgres_ds and test_result.get('status') == 'OK':
            print("\n✓ ALL SETTINGS CORRECT - CONNECTION WORKING")
        else:
            print("\n⚠ CHECK SETTINGS ABOVE")
    
    def print_setup_instructions(self):
        """Print setup instructions if datasource doesn't exist."""
        print("\n" + "="*80)
        print("GRAFANA DATASOURCE SETUP INSTRUCTIONS")
        print("="*80)
        
        print("\nIf PostgreSQL Warehouse datasource is missing, follow these steps:\n")
        
        print("STEP 1: Go to Grafana Data Sources")
        print("  • Open: http://localhost:3000")
        print("  • Click: Settings icon (⚙️) in left sidebar")
        print("  • Select: Data Sources\n")
        
        print("STEP 2: Add New Data Source")
        print("  • Click: 'Add data source' button")
        print("  • Choose: PostgreSQL\n")
        
        print("STEP 3: Configure Connection")
        print("  Connection:")
        print("    • Host: postgres:5432          ← Use 'postgres', not 'localhost'")
        print("    • Database: unilever_warehouse")
        print("    • User: postgres")
        print("    • Password: 123456\n")
        
        print("  PostgreSQL:")
        print("    • SSL Mode: disable")
        print("    • Version: PostgreSQL 14\n")
        
        print("STEP 4: Test Connection")
        print("  • Click: 'Save & Test' button")
        print("  • Should see: 'Database Connection OK' ✓\n")
        
        print("STEP 5: View Dashboards")
        print("  • Go to: Dashboards menu")
        print("  • You should see:")
        print("    ✓ Sales Analytics")
        print("    ✓ ETL Monitoring")
        print("  • Click to view dashboard data\n")
        
        print("="*80)
        print("\nNeed help? Run: python grafana_connection_helper.py")
        print("="*80 + "\n")


def main():
    """Main entry point."""
    helper = GrafanaConnectionHelper()
    helper.print_current_configuration()
    
    # Check if postgres datasource exists
    datasources = helper.get_datasources()
    postgres_exists = any(ds.get('type') == 'postgres' for ds in datasources)
    
    if not postgres_exists:
        helper.print_setup_instructions()


if __name__ == "__main__":
    main()
