#!/usr/bin/env python3
"""
Comprehensive Grafana Fix - Fix Column Names, Add Timestamps, Update Queries
"""

import psycopg2
import json
import requests

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "unilever_warehouse",
    "user": "postgres",
    "password": "123456"
}

GRAFANA_URL = "http://localhost:3000"
GRAFANA_AUTH = ("admin", "admin")

print("\n" + "="*80)
print("COMPREHENSIVE GRAFANA FIX")
print("="*80)

# Step 1: Fix Database Schema
print("\n[STEP 1] FIXING DATABASE SCHEMA")
print("-" * 80)

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Check current schema
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'fact_sales'
        ORDER BY column_name
    """)
    columns = cursor.fetchall()
    print("\nCurrent fact_sales columns:")
    for col, dtype in columns:
        print(f"  {col}: {dtype}")
    
    # Check if created_at needs conversion
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'fact_sales' 
        AND column_name = 'created_at'
    """)
    result = cursor.fetchone()
    if result:
        current_type = result[1]
        print(f"\n✓ created_at exists as: {current_type}")
        
        # If not TIMESTAMPTZ, convert it
        if 'time zone' not in current_type.lower():
            print("  Converting to TIMESTAMPTZ...")
            try:
                cursor.execute("""
                    ALTER TABLE fact_sales 
                    ALTER COLUMN created_at TYPE TIMESTAMPTZ 
                    USING created_at AT TIME ZONE 'UTC'
                """)
                conn.commit()
                print("  ✓ Converted created_at to TIMESTAMPTZ")
            except Exception as e:
                print(f"  ⚠ Could not convert: {e}")
                conn.rollback()
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Database schema check failed: {e}")

# Step 2: Test Queries with Correct Column Names
print("\n[STEP 2] TESTING CORRECTED QUERIES")
print("-" * 80)

corrected_queries = {
    "Total Revenue": """
        SELECT SUM(total_amount) as value FROM fact_sales
        WHERE created_at >= NOW() - INTERVAL '90 days'
    """,
    "Total Transactions": """
        SELECT COUNT(*) as value FROM fact_sales
        WHERE created_at >= NOW() - INTERVAL '90 days'
    """,
    "Average Order Value": """
        SELECT AVG(total_amount) as value FROM fact_sales
        WHERE created_at >= NOW() - INTERVAL '90 days'
    """,
    "Daily Sales Trend": """
        SELECT 
            DATE(fs.created_at AT TIME ZONE 'UTC') as time,
            SUM(fs.total_amount) as value
        FROM fact_sales fs
        WHERE $__timeFilter(created_at)
        GROUP BY DATE(fs.created_at AT TIME ZONE 'UTC')
        ORDER BY time DESC
    """,
    "Top 10 Products": """
        SELECT 
            dp.product_name,
            SUM(fs.quantity) as quantity,
            SUM(fs.total_amount) as revenue
        FROM fact_sales fs
        JOIN dim_product dp ON fs.product_id = dp.product_id
        WHERE fs.created_at >= NOW() - INTERVAL '90 days'
        GROUP BY dp.product_name
        ORDER BY revenue DESC
        LIMIT 10
    """,
}

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    for query_name, query in corrected_queries.items():
        # Skip $__timeFilter for now for testing
        test_query = query.replace("$__timeFilter(created_at)", "created_at >= NOW() - INTERVAL '90 days'")
        
        try:
            cursor.execute(test_query)
            results = cursor.fetchall()
            print(f"\n✓ {query_name}")
            print(f"  Returns: {len(results)} rows")
            if results and len(results) > 0:
                print(f"  Sample: {results[0]}")
        except Exception as e:
            print(f"\n✗ {query_name}")
            print(f"  Error: {e}")
    
    # Check data freshness
    print("\n[DATA FRESHNESS CHECK]")
    cursor.execute("""
        SELECT 
            COUNT(*) as total_records,
            MAX(created_at) as latest_record,
            NOW() - MAX(created_at) as age_of_latest
        FROM fact_sales
    """)
    count, latest, age = cursor.fetchone()
    print(f"  Total records: {count:,}")
    print(f"  Latest record: {latest}")
    print(f"  Age: {age}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Query testing failed: {e}")

# Step 3: Update Grafana Dashboard Queries
print("\n[STEP 3] UPDATING GRAFANA DASHBOARD QUERIES")
print("-" * 80)

dashboard_file = "11-infrastructure/network/grafana/dashboards/sales-analytics.json"

try:
    with open(dashboard_file, 'r') as f:
        dashboard = json.load(f)
    
    # Updated queries with correct column names and $__timeFilter
    query_updates = {
        "Total Sales Revenue": "SELECT SUM(total_amount) as value FROM fact_sales WHERE $__timeFilter(created_at)",
        "Total Transactions": "SELECT COUNT(*) as value FROM fact_sales WHERE $__timeFilter(created_at)",
        "Average Order Value": "SELECT AVG(total_amount) as value FROM fact_sales WHERE $__timeFilter(created_at)",
        "Daily Sales Trend": """
            SELECT 
                DATE(created_at AT TIME ZONE 'UTC')::TIMESTAMPTZ as time,
                SUM(total_amount) as value
            FROM fact_sales
            WHERE $__timeFilter(created_at)
            GROUP BY DATE(created_at AT TIME ZONE 'UTC')
            ORDER BY time DESC
        """,
        "Top 10 Products": """
            SELECT 
                dp.product_name,
                SUM(fs.quantity) as quantity,
                SUM(fs.total_amount) as revenue
            FROM fact_sales fs
            JOIN dim_product dp ON fs.product_id = dp.product_id
            WHERE $__timeFilter(fs.created_at)
            GROUP BY dp.product_name
            ORDER BY revenue DESC
            LIMIT 10
        """,
    }
    
    updated_count = 0
    for panel in dashboard.get('panels', []):
        title = panel.get('title', '')
        
        if title in query_updates:
            for target in panel.get('targets', []):
                old_query = target.get('rawSql', '')
                new_query = query_updates[title]
                
                if old_query != new_query:
                    print(f"\n✓ Updating: {title}")
                    print(f"  Old: {old_query[:80]}...")
                    print(f"  New: {new_query[:80]}...")
                    target['rawSql'] = new_query
                    updated_count += 1
    
    # Write updated dashboard
    with open(dashboard_file, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"\n✓ Updated {updated_count} queries in dashboard")
    
except Exception as e:
    print(f"✗ Failed to update dashboard: {e}")

# Step 4: Verify Grafana Connection
print("\n[STEP 4] VERIFYING GRAFANA CONNECTION")
print("-" * 80)

try:
    session = requests.Session()
    session.auth = GRAFANA_AUTH
    
    response = session.get(f"{GRAFANA_URL}/api/datasources", timeout=5)
    datasources = response.json()
    
    pg_ds = None
    for ds in datasources:
        if 'postgres' in ds.get('type', '').lower():
            pg_ds = ds
            print(f"✓ Found PostgreSQL datasource: {ds.get('name')} (ID: {ds.get('id')})")
            
            # Test connection
            test_response = session.post(
                f"{GRAFANA_URL}/api/datasources/{ds.get('id')}/health",
                timeout=10
            )
            test_result = test_response.json()
            status = test_result.get('message', test_result.get('status', 'Unknown'))
            print(f"  Connection status: {status}")
            
            if 'OK' in status or 'Database Connection OK' in status:
                print("  ✓ Connection working!")
            break
    
    if not pg_ds:
        print("✗ No PostgreSQL datasource found in Grafana")
    
except Exception as e:
    print(f"✗ Failed to check Grafana connection: {e}")

print("\n" + "="*80)
print("FIX COMPLETE")
print("="*80)
print("\nNext steps:")
print("1. Go to http://localhost:3000")
print("2. Open the Sales Analytics dashboard")
print("3. Refresh with Ctrl+F5 (full refresh)")
print("4. Data should now appear in all panels")
print("\nIf panels are still empty:")
print("- Click Edit on a panel")
print("- Check the query in the Query editor")
print("- Click 'Refresh' button")
print("- Look for any error messages at the bottom")
print("\n" + "="*80 + "\n")
