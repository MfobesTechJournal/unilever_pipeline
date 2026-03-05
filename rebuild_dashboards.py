import requests
import json

auth = ('admin', 'admin')
BASE = 'http://localhost:3000'
DS_UID = 'ffetjvdi3rojkb'
DS_TYPE = 'grafana-postgresql-datasource'


def ds(extra=None):
    d = {'type': DS_TYPE, 'uid': DS_UID}
    if extra:
        d.update(extra)
    return d


# ── 1. Delete all existing dashboards ──
print("Deleting all existing dashboards...")
r = requests.get(f'{BASE}/api/search', auth=auth)
for db in r.json():
    uid = db.get('uid')
    if uid:
        requests.delete(f'{BASE}/api/dashboards/uid/{uid}', auth=auth)
        print(f'  Deleted: {db.get("title")}')


# ── 2. Create Sales Analytics dashboard ──
sales_dashboard = {
    'uid': 'sales-main',
    'title': 'Sales Analytics',
    'tags': ['sales', 'unilever'],
    'timezone': 'browser',
    'time': {'from': 'now-2y', 'to': 'now'},
    'refresh': '5m',
    'schemaVersion': 36,
    'panels': [
        {
            'id': 1, 'type': 'stat', 'title': 'Total Revenue',
            'datasource': ds(),
            'gridPos': {'h': 4, 'w': 6, 'x': 0, 'y': 0},
            'fieldConfig': {'defaults': {'unit': 'currencyZAR', 'color': {'mode': 'thresholds'}, 'thresholds': {'mode': 'absolute', 'steps': [{'color': 'green', 'value': None}]}}, 'overrides': []},
            'options': {'reduceOptions': {'calcs': ['lastNotNull']}, 'colorMode': 'background', 'graphMode': 'none'},
            'targets': [{'datasource': ds(), 'rawSql': 'SELECT SUM(revenue) AS value FROM fact_sales', 'format': 'table', 'refId': 'A'}]
        },
        {
            'id': 2, 'type': 'stat', 'title': 'Total Transactions',
            'datasource': ds(),
            'gridPos': {'h': 4, 'w': 6, 'x': 6, 'y': 0},
            'fieldConfig': {'defaults': {'color': {'mode': 'thresholds'}, 'thresholds': {'mode': 'absolute', 'steps': [{'color': 'blue', 'value': None}]}}, 'overrides': []},
            'options': {'reduceOptions': {'calcs': ['lastNotNull']}, 'colorMode': 'background', 'graphMode': 'none'},
            'targets': [{'datasource': ds(), 'rawSql': 'SELECT COUNT(*) AS value FROM fact_sales', 'format': 'table', 'refId': 'A'}]
        },
        {
            'id': 3, 'type': 'stat', 'title': 'Avg Order Value',
            'datasource': ds(),
            'gridPos': {'h': 4, 'w': 6, 'x': 12, 'y': 0},
            'fieldConfig': {'defaults': {'unit': 'currencyZAR', 'color': {'mode': 'thresholds'}, 'thresholds': {'mode': 'absolute', 'steps': [{'color': 'green', 'value': None}]}}, 'overrides': []},
            'options': {'reduceOptions': {'calcs': ['lastNotNull']}, 'colorMode': 'background', 'graphMode': 'none'},
            'targets': [{'datasource': ds(), 'rawSql': 'SELECT AVG(revenue) AS value FROM fact_sales', 'format': 'table', 'refId': 'A'}]
        },
        {
            'id': 4, 'type': 'stat', 'title': 'Total Customers',
            'datasource': ds(),
            'gridPos': {'h': 4, 'w': 6, 'x': 18, 'y': 0},
            'fieldConfig': {'defaults': {'color': {'mode': 'thresholds'}, 'thresholds': {'mode': 'absolute', 'steps': [{'color': 'purple', 'value': None}]}}, 'overrides': []},
            'options': {'reduceOptions': {'calcs': ['lastNotNull']}, 'colorMode': 'background', 'graphMode': 'none'},
            'targets': [{'datasource': ds(), 'rawSql': 'SELECT COUNT(DISTINCT customer_key) AS value FROM fact_sales', 'format': 'table', 'refId': 'A'}]
        },
        {
            'id': 5, 'type': 'timeseries', 'title': 'Daily Revenue',
            'datasource': ds(),
            'gridPos': {'h': 8, 'w': 24, 'x': 0, 'y': 4},
            'fieldConfig': {'defaults': {'color': {'mode': 'palette-classic'}, 'custom': {'lineWidth': 2, 'fillOpacity': 10}}, 'overrides': []},
            'options': {'tooltip': {'mode': 'multi'}, 'legend': {'displayMode': 'list', 'placement': 'bottom'}},
            'targets': [{'datasource': ds(), 'rawSql': "SELECT dd.sale_date AS time, SUM(fs.revenue) AS revenue FROM fact_sales fs JOIN dim_date dd ON fs.date_key = dd.date_key WHERE dd.sale_date BETWEEN $__timeFrom()::date AND $__timeTo()::date GROUP BY dd.sale_date ORDER BY dd.sale_date", 'format': 'time_series', 'refId': 'A'}]
        },
        {
            'id': 6, 'type': 'timeseries', 'title': 'Daily Transactions',
            'datasource': ds(),
            'gridPos': {'h': 8, 'w': 12, 'x': 0, 'y': 12},
            'fieldConfig': {'defaults': {'color': {'mode': 'palette-classic'}, 'custom': {'lineWidth': 2, 'fillOpacity': 10}}, 'overrides': []},
            'options': {'tooltip': {'mode': 'multi'}, 'legend': {'displayMode': 'list', 'placement': 'bottom'}},
            'targets': [{'datasource': ds(), 'rawSql': "SELECT dd.sale_date AS time, COUNT(*) AS transactions FROM fact_sales fs JOIN dim_date dd ON fs.date_key = dd.date_key WHERE dd.sale_date BETWEEN $__timeFrom()::date AND $__timeTo()::date GROUP BY dd.sale_date ORDER BY dd.sale_date", 'format': 'time_series', 'refId': 'A'}]
        },
        {
            'id': 7, 'type': 'piechart', 'title': 'Revenue by Category',
            'datasource': ds(),
            'gridPos': {'h': 8, 'w': 12, 'x': 12, 'y': 12},
            'fieldConfig': {'defaults': {'color': {'mode': 'palette-classic'}}, 'overrides': []},
            'options': {'pieType': 'pie', 'legend': {'displayMode': 'list', 'placement': 'bottom'}},
            'targets': [{'datasource': ds(), 'rawSql': 'SELECT dp.category AS category, SUM(fs.revenue) AS revenue FROM fact_sales fs JOIN dim_product dp ON fs.product_key = dp.product_key GROUP BY dp.category ORDER BY revenue DESC', 'format': 'table', 'refId': 'A'}]
        },
        {
            'id': 8, 'type': 'table', 'title': 'Top 10 Products by Revenue',
            'datasource': ds(),
            'gridPos': {'h': 8, 'w': 12, 'x': 0, 'y': 20},
            'fieldConfig': {'defaults': {}, 'overrides': []},
            'options': {'sortBy': [{'displayName': 'revenue', 'desc': True}]},
            'targets': [{'datasource': ds(), 'rawSql': 'SELECT dp.product_name, dp.category, SUM(fs.quantity) AS total_qty, ROUND(SUM(fs.revenue)::numeric, 2) AS revenue FROM fact_sales fs JOIN dim_product dp ON fs.product_key = dp.product_key GROUP BY dp.product_name, dp.category ORDER BY revenue DESC LIMIT 10', 'format': 'table', 'refId': 'A'}]
        },
        {
            'id': 9, 'type': 'table', 'title': 'Revenue by Province',
            'datasource': ds(),
            'gridPos': {'h': 8, 'w': 12, 'x': 12, 'y': 20},
            'fieldConfig': {'defaults': {}, 'overrides': []},
            'options': {},
            'targets': [{'datasource': ds(), 'rawSql': 'SELECT dc.province, COUNT(*) AS transactions, ROUND(SUM(fs.revenue)::numeric, 2) AS revenue FROM fact_sales fs JOIN dim_customer dc ON fs.customer_key = dc.customer_key GROUP BY dc.province ORDER BY revenue DESC', 'format': 'table', 'refId': 'A'}]
        },
    ]
}

# ── 3. Create ETL Monitoring dashboard ──
etl_dashboard = {
    'uid': 'etl-main',
    'title': 'ETL Monitoring',
    'tags': ['etl', 'monitoring', 'unilever'],
    'timezone': 'browser',
    'time': {'from': 'now-2y', 'to': 'now'},
    'refresh': '5m',
    'schemaVersion': 36,
    'panels': [
        {
            'id': 1, 'type': 'stat', 'title': 'Success Rate (30d)',
            'datasource': ds(),
            'gridPos': {'h': 4, 'w': 4, 'x': 0, 'y': 0},
            'fieldConfig': {'defaults': {'unit': 'percent', 'color': {'mode': 'thresholds'}, 'thresholds': {'mode': 'absolute', 'steps': [{'color': 'red', 'value': None}, {'color': 'yellow', 'value': 90}, {'color': 'green', 'value': 95}]}}, 'overrides': []},
            'options': {'reduceOptions': {'calcs': ['lastNotNull']}, 'colorMode': 'background', 'graphMode': 'none'},
            'targets': [{'datasource': ds(), 'rawSql': "SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success') / NULLIF(COUNT(*), 0), 1) AS value FROM etl_log WHERE start_time >= NOW() - INTERVAL '30 days'", 'format': 'table', 'refId': 'A'}]
        },
        {
            'id': 2, 'type': 'stat', 'title': 'Failed Runs (30d)',
            'datasource': ds(),
            'gridPos': {'h': 4, 'w': 4, 'x': 4, 'y': 0},
            'fieldConfig': {'defaults': {'color': {'mode': 'thresholds'}, 'thresholds': {'mode': 'absolute', 'steps': [{'color': 'green', 'value': None}, {'color': 'yellow', 'value': 3}, {'color': 'red', 'value': 6}]}}, 'overrides': []},
            'options': {'reduceOptions': {'calcs': ['lastNotNull']}, 'colorMode': 'background', 'graphMode': 'none'},
            'targets': [{'datasource': ds(), 'rawSql': "SELECT COUNT(*) AS value FROM etl_log WHERE status = 'failed' AND start_time >= NOW() - INTERVAL '30 days'", 'format': 'table', 'refId': 'A'}]
        },
        {
            'id': 3, 'type': 'stat', 'title': 'Avg Run Duration (7d)',
            'datasource': ds(),
            'gridPos': {'h': 4, 'w': 4, 'x': 8, 'y': 0},
            'fieldConfig': {'defaults': {'unit': 's', 'color': {'mode': 'thresholds'}, 'thresholds': {'mode': 'absolute', 'steps': [{'color': 'green', 'value': None}, {'color': 'yellow', 'value': 300}, {'color': 'red', 'value': 420}]}}, 'overrides': []},
            'options': {'reduceOptions': {'calcs': ['lastNotNull']}, 'colorMode': 'background', 'graphMode': 'none'},
            'targets': [{'datasource': ds(), 'rawSql': "SELECT ROUND(AVG(EXTRACT(EPOCH FROM (end_time - start_time)))) AS value FROM etl_log WHERE status = 'success' AND start_time >= NOW() - INTERVAL '7 days'", 'format': 'table', 'refId': 'A'}]
        },
        {
            'id': 4, 'type': 'stat', 'title': 'Records Loaded (Last Run)',
            'datasource': ds(),
            'gridPos': {'h': 4, 'w': 4, 'x': 12, 'y': 0},
            'fieldConfig': {'defaults': {'color': {'mode': 'thresholds'}, 'thresholds': {'mode': 'absolute', 'steps': [{'color': 'green', 'value': None}]}}, 'overrides': []},
            'options': {'reduceOptions': {'calcs': ['lastNotNull']}, 'colorMode': 'background', 'graphMode': 'none'},
            'targets': [{'datasource': ds(), 'rawSql': "SELECT COALESCE(records_facts, 0) AS value FROM etl_log WHERE status = 'success' ORDER BY start_time DESC LIMIT 1", 'format': 'table', 'refId': 'A'}]
        },
        {
            'id': 5, 'type': 'stat', 'title': 'Quality Issues (30d)',
            'datasource': ds(),
            'gridPos': {'h': 4, 'w': 4, 'x': 16, 'y': 0},
            'fieldConfig': {'defaults': {'color': {'mode': 'thresholds'}, 'thresholds': {'mode': 'absolute', 'steps': [{'color': 'green', 'value': None}, {'color': 'yellow', 'value': 10}, {'color': 'red', 'value': 25}]}}, 'overrides': []},
            'options': {'reduceOptions': {'calcs': ['lastNotNull']}, 'colorMode': 'background', 'graphMode': 'none'},
            'targets': [{'datasource': ds(), 'rawSql': "SELECT COALESCE(SUM(dql.issue_count), 0) AS value FROM data_quality_log dql JOIN etl_log el ON dql.run_id = el.run_id WHERE el.start_time >= NOW() - INTERVAL '30 days'", 'format': 'table', 'refId': 'A'}]
        },
        {
            'id': 6, 'type': 'stat', 'title': 'Total Runs (All Time)',
            'datasource': ds(),
            'gridPos': {'h': 4, 'w': 4, 'x': 20, 'y': 0},
            'fieldConfig': {'defaults': {'color': {'mode': 'thresholds'}, 'thresholds': {'mode': 'absolute', 'steps': [{'color': 'green', 'value': None}]}}, 'overrides': []},
            'options': {'reduceOptions': {'calcs': ['lastNotNull']}, 'colorMode': 'background', 'graphMode': 'none'},
            'targets': [{'datasource': ds(), 'rawSql': 'SELECT COUNT(*) AS value FROM etl_log', 'format': 'table', 'refId': 'A'}]
        },
        {
            'id': 7, 'type': 'timeseries', 'title': 'Daily Runs - Success vs Failed',
            'datasource': ds(),
            'gridPos': {'h': 8, 'w': 16, 'x': 0, 'y': 4},
            'fieldConfig': {'defaults': {'color': {'mode': 'palette-classic'}, 'custom': {'lineWidth': 2, 'fillOpacity': 10}}, 'overrides': [{'matcher': {'id': 'byName', 'options': 'failed_runs'}, 'properties': [{'id': 'color', 'value': {'fixedColor': 'red', 'mode': 'fixed'}}]}, {'matcher': {'id': 'byName', 'options': 'success_runs'}, 'properties': [{'id': 'color', 'value': {'fixedColor': 'green', 'mode': 'fixed'}}]}]},
            'options': {'tooltip': {'mode': 'multi'}, 'legend': {'displayMode': 'list', 'placement': 'bottom'}},
            'targets': [{'datasource': ds(), 'rawSql': "SELECT DATE_TRUNC('day', start_time) AS time, COUNT(*) FILTER (WHERE status = 'success') AS success_runs, COUNT(*) FILTER (WHERE status = 'failed') AS failed_runs FROM etl_log WHERE start_time BETWEEN $__timeFrom() AND $__timeTo() GROUP BY 1 ORDER BY 1", 'format': 'time_series', 'refId': 'A'}]
        },
        {
            'id': 8, 'type': 'piechart', 'title': 'Run Status Distribution (30d)',
            'datasource': ds(),
            'gridPos': {'h': 8, 'w': 8, 'x': 16, 'y': 4},
            'fieldConfig': {'defaults': {'color': {'mode': 'palette-classic'}}, 'overrides': []},
            'options': {'pieType': 'pie', 'legend': {'displayMode': 'list', 'placement': 'bottom'}},
            'targets': [{'datasource': ds(), 'rawSql': "SELECT status, COUNT(*) AS count FROM etl_log WHERE start_time >= NOW() - INTERVAL '30 days' GROUP BY status", 'format': 'table', 'refId': 'A'}]
        },
        {
            'id': 9, 'type': 'timeseries', 'title': 'Records Loaded Per Day',
            'datasource': ds(),
            'gridPos': {'h': 8, 'w': 12, 'x': 0, 'y': 12},
            'fieldConfig': {'defaults': {'color': {'mode': 'palette-classic'}, 'custom': {'lineWidth': 2, 'fillOpacity': 10}}, 'overrides': []},
            'options': {'tooltip': {'mode': 'multi'}, 'legend': {'displayMode': 'list', 'placement': 'bottom'}},
            'targets': [{'datasource': ds(), 'rawSql': "SELECT DATE_TRUNC('day', start_time) AS time, SUM(records_facts) AS facts, SUM(records_customers) AS customers, SUM(records_products) AS products FROM etl_log WHERE start_time BETWEEN $__timeFrom() AND $__timeTo() AND status = 'success' GROUP BY 1 ORDER BY 1", 'format': 'time_series', 'refId': 'A'}]
        },
        {
            'id': 10, 'type': 'timeseries', 'title': 'Run Duration Over Time',
            'datasource': ds(),
            'gridPos': {'h': 8, 'w': 12, 'x': 12, 'y': 12},
            'fieldConfig': {'defaults': {'unit': 's', 'color': {'mode': 'palette-classic'}, 'custom': {'lineWidth': 2, 'fillOpacity': 10}}, 'overrides': []},
            'options': {'tooltip': {'mode': 'multi'}, 'legend': {'displayMode': 'list', 'placement': 'bottom'}},
            'targets': [{'datasource': ds(), 'rawSql': "SELECT DATE_TRUNC('day', start_time) AS time, AVG(EXTRACT(EPOCH FROM (end_time - start_time))) AS avg_duration FROM etl_log WHERE start_time BETWEEN $__timeFrom() AND $__timeTo() GROUP BY 1 ORDER BY 1", 'format': 'time_series', 'refId': 'A'}]
        },
        {
            'id': 11, 'type': 'table', 'title': 'Recent ETL Runs',
            'datasource': ds(),
            'gridPos': {'h': 10, 'w': 24, 'x': 0, 'y': 20},
            'fieldConfig': {'defaults': {}, 'overrides': []},
            'options': {},
            'targets': [{'datasource': ds(), 'rawSql': "SELECT run_id, start_time, end_time, status, records_facts, records_customers, records_products, records_quality_issues, error_message FROM etl_log ORDER BY start_time DESC LIMIT 50", 'format': 'table', 'refId': 'A'}]
        },
        {
            'id': 12, 'type': 'table', 'title': 'Recent Data Quality Issues',
            'datasource': ds(),
            'gridPos': {'h': 10, 'w': 24, 'x': 0, 'y': 30},
            'fieldConfig': {'defaults': {}, 'overrides': []},
            'options': {},
            'targets': [{'datasource': ds(), 'rawSql': "SELECT dql.log_id, el.start_time AS run_time, dql.table_name, dql.check_type, dql.issue_count, dql.issue_description FROM data_quality_log dql JOIN etl_log el ON dql.run_id = el.run_id WHERE dql.issue_count > 0 ORDER BY el.start_time DESC LIMIT 50", 'format': 'table', 'refId': 'A'}]
        },
    ]
}

# ── 4. Push both dashboards ──
print("\nCreating fresh dashboards...")
for dashboard in [sales_dashboard, etl_dashboard]:
    payload = {'dashboard': dashboard, 'overwrite': True, 'folderId': 0}
    r = requests.post(f'{BASE}/api/dashboards/db', auth=auth, json=payload)
    result = r.json()
    print(f"  {dashboard['title']}: {r.status_code} {result.get('status')} -> {result.get('url', '')}")

print("\nDone! Open Grafana and check the dashboards.")
