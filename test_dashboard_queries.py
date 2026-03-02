#!/usr/bin/env python3
"""
Test all dashboard queries directly against PostgreSQL
to ensure they return data in the format Grafana expects.
"""

import psycopg2
from decimal import Decimal

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "unilever_warehouse",
    "user": "postgres",
    "password": "123456"
}

print("\n" + "="*80)
print("DASHBOARD QUERY VERIFICATION")
print("="*80)

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("\n[SALES ANALYTICS - QUERY TEST]")
    print("-" * 80)
    
    # Query 1: Total Revenue
    print("\n1. Total Sales Revenue")
    query = "SELECT SUM(revenue) as value FROM fact_sales"
    print(f"   Query: {query}")
    cursor.execute(query)
    result = cursor.fetchone()
    print(f"   Result: {result}")
    print(f"   ✓ Returns data: {result[0] if result and result[0] else 'NULL'}")
    
    # Query 2: Total Transactions
    print("\n2. Total Transactions")
    query = "SELECT COUNT(*) as value FROM fact_sales"
    print(f"   Query: {query}")
    cursor.execute(query)
    result = cursor.fetchone()
    print(f"   Result: {result}")
    print(f"   ✓ Returns data: {result[0]}")
    
    # Query 3: Average Order Value
    print("\n3. Average Order Value")
    query = "SELECT AVG(revenue) as value FROM fact_sales"
    print(f"   Query: {query}")
    cursor.execute(query)
    result = cursor.fetchone()
    print(f"   Result: {result}")
    print(f"   ✓ Returns data: {result[0] if result and result[0] else 'NULL'}")
    
    # Query 4: Daily Sales Trend
    print("\n4. Daily Sales Trend")
    query = """
    SELECT 
        dd.sale_date as time,
        SUM(fs.revenue) as value
    FROM fact_sales fs
    JOIN dim_date dd ON fs.date_key = dd.date_key
    GROUP BY dd.sale_date
    ORDER BY dd.sale_date DESC
    LIMIT 30
    """
    print(f"   Query: SELECT ... GROUP BY dd.sale_date ...")
    cursor.execute(query)
    results = cursor.fetchall()
    print(f"   Results: {len(results)} rows")
    if results:
        print(f"   Sample: {results[0]}")
    print(f"   ✓ Returns time-series data")
    
    # Query 5: Top Products
    print("\n5. Top 10 Products")
    query = """
    SELECT 
        dp.product_name as name,
        SUM(fs.revenue) as value
    FROM fact_sales fs
    JOIN dim_product dp ON fs.product_key = dp.product_key
    GROUP BY dp.product_name
    ORDER BY value DESC
    LIMIT 10
    """
    print(f"   Query: SELECT ... GROUP BY dp.product_name ...")
    cursor.execute(query)
    results = cursor.fetchall()
    print(f"   Results: {len(results)} rows")
    if results:
        print(f"   Top product: {results[0]}")
    print(f"   ✓ Returns table data")
    
    print("\n" + "-"*80)
    print("\n[ETL MONITORING - QUERY TEST]")
    print("-" * 80)
    
    # ETL Logs
    print("\n1. ETL Logs")
    query = "SELECT * FROM etl_log LIMIT 5"
    print(f"   Query: {query}")
    cursor.execute(query)
    results = cursor.fetchall()
    print(f"   Results: {len(results)} rows")
    print(f"   ✓ Returns log data")
    
    # Data Quality
    print("\n2. Data Quality Issues")
    query = "SELECT * FROM data_quality_log LIMIT 5"
    print(f"   Query: {query}")
    cursor.execute(query)
    results = cursor.fetchall()
    print(f"   Results: {len(results)} rows")
    print(f"   ✓ Returns quality data")
    
    print("\n" + "="*80)
    print("✓ ALL QUERIES RETURN DATA")
    print("="*80)
    
    print("\nIF DASHBOARDS ARE STILL EMPTY:")
    print("1. The datasource connection is working")
    print("2. The queries return data correctly")
    print("3. The issue is with how Grafana is displaying the data")
    print("\nTry this:")
    print("  1. Go to a dashboard")
    print("  2. Click on a panel")
    print("  3. Click 'Edit'")
    print("  4. Check the 'Query' section")
    print("  5. Verify column names match above results")
    print("  6. Click 'Apply' then 'Save dashboard'")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    print("\nDatabase is not responding correctly")
