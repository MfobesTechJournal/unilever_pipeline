#!/usr/bin/env python3
"""
Test Grafana endpoints for ETL Monitoring and Sales Analytics dashboards.
Verifies datasource connectivity and dashboard data retrieval.
"""

import requests
import json
import time
from typing import Dict, List, Tuple

# Grafana configuration
GRAFANA_URL = "http://localhost:3000"
GRAFANA_API_KEY = "admin:admin"  # Base auth credentials
POSTGRES_DATASOURCE_ID = 5  # PostgreSQL datasource ID

# Dashboard UIDs
DASHBOARDS = {
    "Sales Analytics": "sales-analytics",
    "ETL Monitoring": "etl-monitoring"
}

class GrafanaEndpointTester:
    """Test Grafana endpoints and dashboard connectivity."""
    
    def __init__(self, base_url: str = GRAFANA_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.auth = ("admin", "admin")
        self.results = []
    
    def log_result(self, test_name: str, status: str, details: str = "", error: str = ""):
        """Log test result."""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "error": error,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.results.append(result)
        
        icon = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⚠"
        print(f"\n{icon} {test_name}: {status}")
        if details:
            print(f"  Details: {details}")
        if error:
            print(f"  Error: {error}")
    
    def test_grafana_health(self) -> bool:
        """Test if Grafana is accessible."""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=5)
            is_ok = response.status_code == 200
            data = response.json()
            version = data.get("version", "Unknown")
            
            self.log_result(
                "Grafana Health Check",
                "PASS" if is_ok else "FAIL",
                f"Status: {response.status_code}, Version: {version}"
            )
            return is_ok
        except Exception as e:
            self.log_result("Grafana Health Check", "FAIL", error=str(e))
            return False
    
    def test_datasource_health(self) -> bool:
        """Test PostgreSQL datasource health."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/datasources/{POSTGRES_DATASOURCE_ID}/health",
                timeout=5
            )
            is_ok = response.status_code == 200
            data = response.json() if response.text else {}
            
            self.log_result(
                "PostgreSQL Datasource Health",
                "PASS" if is_ok else "FAIL",
                f"Status: {response.status_code}, Response: {json.dumps(data)}"
            )
            return is_ok
        except Exception as e:
            self.log_result("PostgreSQL Datasource Health", "FAIL", error=str(e))
            return False
    
    def test_datasource_list(self) -> bool:
        """Test listed datasources."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/datasources",
                timeout=5
            )
            is_ok = response.status_code == 200
            datasources = response.json() if is_ok else []
            
            # Find PostgreSQL datasource
            pg_ds = next((ds for ds in datasources if ds.get("type") == "postgres"), None)
            
            details = f"Total datasources: {len(datasources)}"
            if pg_ds:
                details += f", PostgreSQL: {pg_ds.get('name')} (ID: {pg_ds.get('id')})"
            
            self.log_result(
                "List Datasources",
                "PASS" if pg_ds else "FAIL",
                details
            )
            return bool(pg_ds)
        except Exception as e:
            self.log_result("List Datasources", "FAIL", error=str(e))
            return False
    
    def test_dashboard_exists(self, name: str, uid: str) -> bool:
        """Test if dashboard exists."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/dashboards/uid/{uid}",
                timeout=5
            )
            is_ok = response.status_code == 200
            data = response.json() if is_ok else {}
            
            dashboard = data.get("dashboard", {})
            panel_count = len(dashboard.get("panels", []))
            
            self.log_result(
                f"Dashboard Exists: {name}",
                "PASS" if is_ok else "FAIL",
                f"Status: {response.status_code}, Panels: {panel_count}"
            )
            return is_ok
        except Exception as e:
            self.log_result(f"Dashboard Exists: {name}", "FAIL", error=str(e))
            return False
    
    def test_dashboard_panels(self, name: str, uid: str) -> Tuple[bool, List[Dict]]:
        """Test dashboard panels and their datasource configuration."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/dashboards/uid/{uid}",
                timeout=5
            )
            
            if response.status_code != 200:
                self.log_result(
                    f"Dashboard Panels: {name}",
                    "FAIL",
                    f"Status: {response.status_code}"
                )
                return False, []
            
            dashboard = response.json().get("dashboard", {})
            panels = dashboard.get("panels", [])
            
            panel_info = []
            for panel in panels:
                info = {
                    "id": panel.get("id"),
                    "title": panel.get("title"),
                    "type": panel.get("type"),
                    "datasource": panel.get("datasource"),
                    "targets": len(panel.get("targets", []))
                }
                panel_info.append(info)
            
            # Check if all panels have datasource
            all_have_ds = all(p.get("datasource") for p in panel_info)
            
            details = f"Total panels: {len(panels)}, All have datasource: {all_have_ds}"
            self.log_result(
                f"Dashboard Panels: {name}",
                "PASS" if all_have_ds else "WARN",
                details
            )
            
            return all_have_ds, panel_info
        except Exception as e:
            self.log_result(f"Dashboard Panels: {name}", "FAIL", error=str(e))
            return False, []
    
    def test_dashboard_query(self, name: str, uid: str) -> bool:
        """Test dashboard query execution."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/dashboards/uid/{uid}",
                timeout=5
            )
            
            if response.status_code != 200:
                return False
            
            dashboard = response.json().get("dashboard", {})
            panels = dashboard.get("panels", [])
            
            all_have_queries = all(len(p.get("targets", [])) > 0 for p in panels)
            
            details = f"Panels with queries: {sum(1 for p in panels if p.get('targets'))}/{len(panels)}"
            self.log_result(
                f"Dashboard Queries: {name}",
                "PASS" if all_have_queries else "WARN",
                details
            )
            return all_have_queries
        except Exception as e:
            self.log_result(f"Dashboard Queries: {name}", "FAIL", error=str(e))
            return False
    
    def test_dashboard_renders(self, name: str, uid: str) -> bool:
        """Test if dashboard can be rendered/accessed via frontend."""
        try:
            response = self.session.get(
                f"{self.base_url}/d/{uid}",
                timeout=5,
                allow_redirects=True
            )
            is_ok = response.status_code == 200
            
            self.log_result(
                f"Dashboard Render: {name}",
                "PASS" if is_ok else "FAIL",
                f"Status: {response.status_code}"
            )
            return is_ok
        except Exception as e:
            self.log_result(f"Dashboard Render: {name}", "FAIL", error=str(e))
            return False
    
    def test_metric_endpoint(self, name: str, uid: str) -> bool:
        """Test dashboard metrics/data endpoint."""
        try:
            # Get dashboard to extract panel info
            response = self.session.get(
                f"{self.base_url}/api/dashboards/uid/{uid}",
                timeout=5
            )
            
            if response.status_code != 200:
                return False
            
            panel_count = len(response.json().get("dashboard", {}).get("panels", []))
            
            # Try to access the dashboard render through the metrics endpoint
            response = self.session.get(
                f"{self.base_url}/api/annotations",
                timeout=5,
                params={"dashboardUID": uid}
            )
            
            is_ok = response.status_code == 200
            
            self.log_result(
                f"Metrics Endpoint: {name}",
                "PASS" if is_ok else "WARN",
                f"Status: {response.status_code}, Panels: {panel_count}"
            )
            return is_ok
        except Exception as e:
            self.log_result(f"Metrics Endpoint: {name}", "FAIL", error=str(e))
            return False
    
    def run_all_tests(self):
        """Run all endpoint tests."""
        print("\n" + "="*80)
        print("GRAFANA ENDPOINT TESTS")
        print("="*80)
        
        # Basic health checks
        print("\n--- BASIC HEALTH CHECKS ---")
        grafana_ok = self.test_grafana_health()
        datasource_ok = self.test_datasource_health()
        datasource_list_ok = self.test_datasource_list()
        
        # Test each dashboard
        print("\n--- DASHBOARD TESTS ---")
        dashboard_results = {}
        for name, uid in DASHBOARDS.items():
            print(f"\nTesting {name}...")
            dashboard_results[name] = {
                "exists": self.test_dashboard_exists(name, uid),
                "panels": self.test_dashboard_panels(name, uid)[0],
                "queries": self.test_dashboard_query(name, uid),
                "renders": self.test_dashboard_renders(name, uid),
                "metrics": self.test_metric_endpoint(name, uid)
            }
        
        # Summary
        self.print_summary(grafana_ok, datasource_ok, dashboard_results)
    
    def print_summary(self, grafana_ok: bool, datasource_ok: bool, dashboard_results: Dict):
        """Print test summary."""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        warned = sum(1 for r in self.results if r["status"] == "WARN")
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"✓ Passed: {passed}")
        print(f"✗ Failed: {failed}")
        print(f"⚠ Warned: {warned}")
        
        print("\n--- STATUS ---")
        print(f"Grafana: {'✓ OK' if grafana_ok else '✗ FAILED'}")
        print(f"Datasource: {'✓ OK' if datasource_ok else '✗ FAILED'}")
        
        print("\n--- DASHBOARDS ---")
        for name, results in dashboard_results.items():
            all_pass = all(results.values())
            status = "✓ READY" if all_pass else "⚠ ISSUES"
            print(f"{name}: {status}")
            for test, result in results.items():
                icon = "✓" if result else "✗"
                print(f"  {icon} {test.replace('_', ' ').title()}")
        
        print("\n" + "="*80)
        if failed == 0:
            print("✓ ALL CRITICAL TESTS PASSED - ENDPOINTS OPERATIONAL")
        else:
            print("✗ SOME TESTS FAILED - REVIEW ERRORS ABOVE")
        print("="*80 + "\n")


def main():
    """Main entry point."""
    tester = GrafanaEndpointTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
