#!/usr/bin/env python3
"""
Export all dashboard data to JSON files - No Grafana needed!
"""

import psycopg2
import json
from datetime import datetime, timedelta

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "unilever_warehouse",
    "user": "postgres",
    "password": "123456"
}

print("\n" + "="*80)
print("EXPORT DASHBOARD DATA TO JSON")
print("="*80)

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 1. Sales Analytics Data
    print("\n[1] EXPORTING SALES ANALYTICS DATA")
    print("-" * 80)
    
    sales_data = {}
    
    # Total Revenue
    cursor.execute("SELECT SUM(revenue) as value FROM fact_sales")
    sales_data["total_revenue"] = float(cursor.fetchone()[0])
    print(f"✓ Total Revenue: ${sales_data['total_revenue']:,.2f}")
    
    # Transaction Count
    cursor.execute("SELECT COUNT(*) as value FROM fact_sales")
    sales_data["transaction_count"] = cursor.fetchone()[0]
    print(f"✓ Transaction Count: {sales_data['transaction_count']:,}")
    
    # Average Order Value
    cursor.execute("SELECT AVG(revenue) as value FROM fact_sales")
    sales_data["avg_order_value"] = float(cursor.fetchone()[0])
    print(f"✓ Average Order Value: ${sales_data['avg_order_value']:.2f}")
    
    # Daily Sales
    cursor.execute("""
        SELECT DATE(load_timestamp) as date, SUM(revenue) as revenue, COUNT(*) as transactions
        FROM fact_sales
        GROUP BY DATE(load_timestamp)
        ORDER BY date DESC
    """)
    sales_data["daily_sales"] = [
        {"date": str(row[0]), "revenue": float(row[1]), "transactions": row[2]}
        for row in cursor.fetchall()
    ]
    print(f"✓ Daily Sales: {len(sales_data['daily_sales'])} days")
    
    # Top 10 Products
    cursor.execute("""
        SELECT dp.product_name, SUM(fs.quantity) as qty, SUM(fs.revenue) as revenue
        FROM fact_sales fs
        JOIN dim_product dp ON fs.product_key = dp.product_key
        GROUP BY dp.product_name
        ORDER BY revenue DESC
        LIMIT 10
    """)
    sales_data["top_products"] = [
        {"product": row[0], "quantity": row[1], "revenue": float(row[2])}
        for row in cursor.fetchall()
    ]
    print(f"✓ Top Products: {len(sales_data['top_products'])} products")
    
    # Sales by Customer (Top 5)
    cursor.execute("""
        SELECT dc.customer_name, COUNT(*) as transactions, SUM(fs.revenue) as revenue
        FROM fact_sales fs
        JOIN dim_customer dc ON fs.customer_key = dc.customer_key
        GROUP BY dc.customer_name
        ORDER BY revenue DESC
        LIMIT 5
    """)
    sales_data["top_customers"] = [
        {"customer": row[0], "transactions": row[1], "revenue": float(row[2])}
        for row in cursor.fetchall()
    ]
    print(f"✓ Top Customers: {len(sales_data['top_customers'])} customers")
    
    # Save Sales Data
    with open("sales_dashboard_data.json", "w") as f:
        json.dump(sales_data, f, indent=2, default=str)
    print("✓ Saved: sales_dashboard_data.json")
    
    # 2. ETL Monitoring Data
    print("\n[2] EXPORTING ETL MONITORING DATA")
    print("-" * 80)
    
    etl_data = {}
    
    # Total Runs
    cursor.execute("SELECT COUNT(*) as total FROM etl_log")
    etl_data["total_runs"] = cursor.fetchone()[0]
    print(f"✓ Total Runs (All Time): {etl_data['total_runs']}")
    
    # Recent Success Rate
    cursor.execute("""
        SELECT 
            ROUND(100.0 * SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) / 
            NULLIF(COUNT(*), 0), 2) as success_rate
        FROM etl_log
        WHERE start_time >= NOW() - INTERVAL '7 days'
    """)
    etl_data["success_rate_7d"] = cursor.fetchone()[0]
    print(f"✓ Success Rate (7d): {etl_data['success_rate_7d']}%")
    
    # Failed Runs (30d)
    cursor.execute("""
        SELECT COUNT(*) as failed
        FROM etl_log
        WHERE status != 'success' AND start_time >= NOW() - INTERVAL '30 days'
    """)
    etl_data["failed_runs_30d"] = cursor.fetchone()[0]
    print(f"✓ Failed Runs (30d): {etl_data['failed_runs_30d']}")
    
    # Records Loaded
    cursor.execute("""
        SELECT SUM(records_facts) as records_loaded
        FROM etl_log
        WHERE status = 'success'
    """)
    etl_data["total_records_loaded"] = cursor.fetchone()[0] or 0
    print(f"✓ Records Loaded (Total): {etl_data['total_records_loaded']:,}")
    
    # Average Run Duration
    cursor.execute("""
        SELECT ROUND(AVG(EXTRACT(EPOCH FROM (end_time - start_time))), 2) as avg_duration
        FROM etl_log
        WHERE start_time >= NOW() - INTERVAL '7 days'
    """)
    etl_data["avg_duration_7d"] = cursor.fetchone()[0]
    print(f"✓ Average Duration (7d): {etl_data['avg_duration_7d']} seconds")
    
    # Quality Issues (30d)
    cursor.execute("""
        SELECT COUNT(*) as issues
        FROM data_quality_log
        WHERE timestamp >= NOW() - INTERVAL '30 days'
    """)
    etl_data["quality_issues_30d"] = cursor.fetchone()[0]
    print(f"✓ Quality Issues (30d): {etl_data['quality_issues_30d']}")
    
    # Recent Runs (Last 10)
    cursor.execute("""
        SELECT run_id, start_time, status, COALESCE(records_facts, 0) as records
        FROM etl_log
        ORDER BY start_time DESC
        LIMIT 10
    """)
    etl_data["recent_runs"] = [
        {"run_id": row[0], "time": str(row[1]), "status": row[2], "records": int(row[3])}
        for row in cursor.fetchall()
    ]
    print(f"✓ Recent Runs: {len(etl_data['recent_runs'])} runs")
    
    # Daily Runs (Last 7 Days)
    cursor.execute("""
        SELECT DATE(start_time) as date, 
               COUNT(*) as total,
               SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as success,
               SUM(CASE WHEN status!='success' THEN 1 ELSE 0 END) as failed
        FROM etl_log
        WHERE start_time >= NOW() - INTERVAL '7 days'
        GROUP BY DATE(start_time)
        ORDER BY date DESC
    """)
    etl_data["daily_runs"] = [
        {"date": str(row[0]), "total": int(row[1]), "success": int(row[2]) if row[2] else 0, "failed": int(row[3]) if row[3] else 0}
        for row in cursor.fetchall()
    ]
    print(f"✓ Daily Runs: {len(etl_data['daily_runs'])} days")
    
    # Save ETL Data
    with open("etl_dashboard_data.json", "w") as f:
        json.dump(etl_data, f, indent=2, default=str)
    print("✓ Saved: etl_dashboard_data.json")
    
    conn.close()
    
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "="*80)
print("✓ DATA EXPORT COMPLETE!")
print("="*80)
print("\nYour dashboard data has been exported to:")
print("  1. sales_dashboard_data.json")
print("  2. etl_dashboard_data.json")
print("\n📊 You can now:")
print("  • View the JSON files to see your data")
print("  • Open Grafana at http://localhost:3000 and refresh panels")
print("  • The data will populate automatically when Grafana connects")
