import json
import docker

client = docker.from_env()
container = client.containers.get('unilever_grafana')

# Read dashboard file from container
exit_code, output = container.exec_run('cat /etc/grafana/dashboards/data-quality.json')
dashboard = json.loads(output.decode('utf-8'))

print("=" * 70)
print("GRAFANA DASHBOARD QUERIES")
print("=" * 70)

if 'panels' in dashboard:
    for panel in dashboard['panels']:
        panel_title = panel.get('title', 'Unknown')
        print(f"\n[{panel_title}]")
        
        if 'targets' in panel:
            for target in panel['targets']:
                if 'rawSql' in target:
                    print(f"  SQL: {target['rawSql'][:150]}...")
                elif 'rawQuery' in target:
                    print(f"  Query: {target['rawQuery'][:150]}...")
                else:
                    print(f"  Targets: {json.dumps(target)[:150]}...")
else:
    print("No panels found in dashboard")

# Also check which table is being used
print("\n" + "=" * 70)
print("CHECKING TABLE REFERENCES")
print("=" * 70)

dashboard_str = json.dumps(dashboard)
print(f"'data_quality_log' references: {dashboard_str.count('data_quality_log')}")
print(f"'quality_log' references: {dashboard_str.count('quality_log')}")
print(f"'etl_log' references: {dashboard_str.count('etl_log')}")
