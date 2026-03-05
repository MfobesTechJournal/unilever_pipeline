import os

TO_DELETE = [
    'check_dashboard_queries.py','check_database_data.py','check_panel_config.py',
    'check_schema_simple.py','create_dashboards.py','create_final_dashboards.py',
    'create_minimal_dash.py','create_simple_dashboard.py','dashboard_server.py',
    'debug_dashboards.py','debug_datasource.py','debug_panel_structure.py',
    'deploy_to_cloud_grafana.py','diagnose_datasource.py','diagnose_empty_dashboards.py',
    'export_dashboard_data.py','final_verification.py','fix_all_dashboards.py',
    'fix_dashboard_queries_final.py','fix_datasource.py','fix_datasource_db.py',
    'fix_datasource_host.py','fix_ds_type.py','fix_grafana_comprehensive.py',
    'fix_grafana_correct.py','fix_grafana_datasource.py','fix_type_mismatch.py',
    'force_reload_dashboards.py','full_system_check.py','generate_10x_data.py',
    'generate_unilever_data.py','grafana_connection_helper.py','list_dashboards.py',
    'list_tables.py','load_etl_logs.py','load_etl_logs_v2.py','load_sales_data.py',
    'populate_dashboard_data.py','postgres_bridge.py','rebuild_dashboards.py',
    'recreate_dashboard_final.py','recreate_dashboards.py','remove_secrets.py',
    'reset_grafana.py','setup_grafana.py','setup_grafana_agent.py','simple_bridge.py',
    'start_grafana_with_dashboards.py','tcp_bridge.py','test_dashboard_fix.py',
    'test_dashboard_queries.py','test_datasources.py','test_ds_create.py',
    'test_grafana_endpoints.py','test_grafana_queries.py','update_dashboard_datasources.py',
    'update_dashboards.py','upload_sales_dashboard.py','upload_sales_dashboard_cloud.py',
    'validate_grafana_fix.py','validate_system.py','verify_connection.py',
    'verify_dashboard_data.py','verify_dashboards.py',
    'etl_dashboard_data.json','etl_monitoring_dashboard.json',
    'etl_monitoring_v2.json','etl_monitoring_v3.json','sales_dashboard_data.json',
    'CLOUD_CONNECTION_OPTIONS.md','COMPLETION_SUMMARY.md','DASHBOARD_POPULATION_REPORT.md',
    'DELIVERY_SUMMARY.md','FIXES_SUMMARY.md','GRAFANA_ACTION_CHECKLIST.md',
    'GRAFANA_BEFORE_AND_AFTER.md','GRAFANA_CONNECTION_GUIDE.md',
    'GRAFANA_DASHBOARD_FIX_SUMMARY.md','GRAFANA_FIX_COMPLETE.md',
    'GRAFANA_QUICK_FIX_GUIDE.md','GRAFANA_TEST_RESULTS.md','IMPLEMENTATION_SUMMARY.md',
    'OPERATIONAL_SUMMARY.md','PRODUCTION_README.md','PRODUCTION_READY.md',
    'README_PRODUCTION.md','RUN_LOCALLY_FIRST.md','START_PRODUCTION.md',
    'STREAMLIT_README.md','TODO_COMPLETION_SUMMARY.md',
]

deleted = 0
for f in TO_DELETE:
    if os.path.exists(f):
        os.remove(f)
        print('Deleted:', f)
        deleted += 1

print(f'\nDone. Deleted {deleted} files.')
