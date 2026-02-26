import requests
import json

# Grafana API credentials and URL
GRAFANA_URL = "http://localhost:3000"
ADMIN_USER = "admin"
ADMIN_PASS = "admin"

# Create dashboard with proper queries for data_quality_log table
dashboard_payload = {
    "dashboard": {
        "id": 1,
        "uid": "data-quality",
        "title": "Unilever Data Quality Monitoring",
        "tags": ["etl", "data-quality"],
        "timezone": "browser",
        "schemaVersion": 36,
        "version": 0,
        "refresh": "30s",
        "time": {"from": "now-30d", "to": "now"},
        "timepicker": {
            "refresh_intervals": ["5s", "10s", "30s", "1m", "5m", "15m", "30m", "1h", "2h", "1d"]
        },
        "panels": [
            {
                "id": 1,
                "title": "Total Quality Issues (Last 30 Days)",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                "targets": [
                    {
                        "rawSql": "SELECT SUM(issue_count) as value FROM data_quality_log WHERE timestamp > NOW() - INTERVAL '30 days'",
                        "format": "table",
                        "refId": "A"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 50},
                                {"color": "red", "value": 100}
                            ]
                        }
                    }
                }
            },
            {
                "id": 2,
                "title": "Issue Types Detected",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0},
                "targets": [
                    {
                        "rawSql": "SELECT COUNT(DISTINCT check_type) as value FROM data_quality_log WHERE timestamp > NOW() - INTERVAL '30 days'",
                        "format": "table",
                        "refId": "A"
                    }
                ]
            },
            {
                "id": 3,
                "title": "Tables with Issues",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0},
                "targets": [
                    {
                        "rawSql": "SELECT COUNT(DISTINCT table_name) as value FROM data_quality_log WHERE timestamp > NOW() - INTERVAL '30 days'",
                        "format": "table",
                        "refId": "A"
                    }
                ]
            },
            {
                "id": 4,
                "title": "Quality Checks This Week",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0},
                "targets": [
                    {
                        "rawSql": "SELECT COUNT(*) as value FROM data_quality_log WHERE timestamp > NOW() - INTERVAL '7 days'",
                        "format": "table",
                        "refId": "A"
                    }
                ]
            },
            {
                "id": 5,
                "title": "Quality Issues Over Time",
                "type": "timeseries",
                "gridPos": {"h": 10, "w": 12, "x": 0, "y": 8},
                "targets": [
                    {
                        "rawSql": "SELECT timestamp, check_type, SUM(issue_count) as value FROM data_quality_log WHERE timestamp > NOW() - INTERVAL '30 days' GROUP BY timestamp, check_type ORDER BY timestamp",
                        "format": "table",
                        "refId": "A"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "custom": {"lineWidth": 2},
                        "unit": "short"
                    }
                }
            },
            {
                "id": 6,
                "title": "Issue Distribution by Type",
                "type": "piechart",
                "gridPos": {"h": 10, "w": 12, "x": 12, "y": 8},
                "targets": [
                    {
                        "rawSql": "SELECT check_type, SUM(issue_count) as value FROM data_quality_log WHERE timestamp > NOW() - INTERVAL '30 days' GROUP BY check_type ORDER BY value DESC",
                        "format": "table",
                        "refId": "A"
                    }
                ]
            },
            {
                "id": 7,
                "title": "Recent Quality Issues",
                "type": "table",
                "gridPos": {"h": 10, "w": 24, "x": 0, "y": 18},
                "targets": [
                    {
                        "rawSql": "SELECT run_id, table_name, check_type, issue_count, timestamp FROM data_quality_log WHERE timestamp > NOW() - INTERVAL '7 days' ORDER BY timestamp DESC LIMIT 50",
                        "format": "table",
                        "refId": "A"
                    }
                ]
            }
        ]
    },
    "overwrite": True
}

try:
    print("=" * 60)
    print("GRAFANA DASHBOARD UPDATE")
    print("=" * 60)
    
    # Update dashboard via API
    response = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        json=dashboard_payload,
        auth=(ADMIN_USER, ADMIN_PASS),
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"\n✓ Dashboard updated successfully!")
        print(f"  Dashboard ID: {result.get('id')}")
        print(f"  URL: {result.get('url')}")
        print(f"\n✓ Visit Grafana: http://localhost:3000/d/data-quality")
    else:
        print(f"\n✗ Failed to update dashboard: {response.status_code}")
        print(f"  Response: {response.text}")
        
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("NOTE: Dashboard will now use correct data_quality_log table")
print("All panels configured with proper SQL queries")
print("=" * 60)
