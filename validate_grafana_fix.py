#!/usr/bin/env python3
"""
Validate Grafana Fix - Test Database Connection and Query Results
Run this AFTER updating dashboards to verify the fix works
"""

import psycopg2
import requests
import sys

def test_database():
    """Test database connection and queries"""
    print("\n" + "="*80)
    print("[DATABASE VALIDATION]")
    print("="*80)
    
    DB_CONFIG = {
        "host": "localhost",
        "port": 5433,
        "database": "unilever_warehouse",
        "user": "postgres",
        "password": "123456"
    }
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("\n✓ Database connection successful")
        
        # Test 1: Check table structure
        print("\n[1] Verifying fact_sales columns:")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'fact_sales'
            AND column_name IN ('revenue', 'product_key', 'date_key', 'load_timestamp')
            ORDER BY column_name
        """)
        results = cursor.fetchall()
        for col, dtype in results:
            print(f"    ✓ {col}: {dtype}")
        
        # Test 2: Check data exists
        print("\n[2] Checking for recent data:")
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                MAX(load_timestamp) as latest_record
            FROM fact_sales
        """)
        total, latest = cursor.fetchone()
        print(f"    Total records: {total:,}")
        print(f"    Latest record: {latest}")
        
        if latest is None:
            print("    ⚠️  WARNING: No data in fact_sales table!")
            cursor.close()
            conn.close()
            return False
        
        print(f"    ✓ Recent data found")
        
        # Test 3: Test all corrected queries
        print("\n[3] Testing corrected database queries:")
        
        test_queries = {
            "Total Revenue": "SELECT SUM(revenue) as value FROM fact_sales WHERE load_timestamp >= NOW() - INTERVAL '90 days'",
            "Total Transactions": "SELECT COUNT(*) as value FROM fact_sales WHERE load_timestamp >= NOW() - INTERVAL '90 days'",
            "Average Order Value": "SELECT AVG(revenue) as value FROM fact_sales WHERE load_timestamp >= NOW() - INTERVAL '90 days'",
            "Daily Sales Trend": """
                SELECT 
                    DATE(fs.load_timestamp) as time,
                    SUM(fs.revenue) as value
                FROM fact_sales fs
                WHERE fs.load_timestamp >= NOW() - INTERVAL '90 days'
                GROUP BY DATE(fs.load_timestamp)
                ORDER BY time DESC
                LIMIT 10
            """,
            "Top 10 Products": """
                SELECT 
                    dp.product_name,
                    SUM(fs.quantity) as quantity,
                    SUM(fs.revenue) as revenue
                FROM fact_sales fs
                JOIN dim_product dp ON fs.product_key = dp.product_key
                WHERE fs.load_timestamp >= NOW() - INTERVAL '90 days'
                GROUP BY dp.product_name
                ORDER BY revenue DESC
                LIMIT 10
            """,
        }
        
        all_passed = True
        for query_name, query in test_queries.items():
            try:
                cursor.execute(query)
                result = cursor.fetchall()
                rows = len(result)
                
                if rows > 0:
                    print(f"    ✓ {query_name}: {rows} row(s)")
                else:
                    print(f"    ⚠️  {query_name}: Returns 0 rows")
                    if "SUM" in query or "AVG" in query:
                        print(f"       (This is OK if no data exists for the time range)")
                    
            except Exception as e:
                print(f"    ✗ {query_name}: {str(e)[:80]}")
                all_passed = False
        
        cursor.close()
        conn.close()
        
        return all_passed
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("\n  Check:")
        print("  - PostgreSQL is running on localhost:5433")
        print("  - Database 'unilever_warehouse' exists")
        print("  - Credentials are correct (postgres:123456)")
        return False


def test_grafana():
    """Test Grafana connection"""
    print("\n" + "="*80)
    print("[GRAFANA VALIDATION]")
    print("="*80)
    
    GRAFANA_URL = "http://localhost:3000"
    GRAFANA_AUTH = ("admin", "admin")
    
    try:
        session = requests.Session()
        session.auth = GRAFANA_AUTH
        
        # Test 1: Health check
        print("\n[1] Grafana health check:")
        response = session.get(f"{GRAFANA_URL}/api/health", timeout=5)
        if response.status_code == 200:
            version = response.json().get('version', 'unknown')
            print(f"    ✓ Grafana is running (v{version})")
        else:
            print(f"    ✗ Grafana health check failed: {response.status_code}")
            return False
        
        # Test 2: Check datasources
        print("\n[2] PostgreSQL datasource check:")
        response = session.get(f"{GRAFANA_URL}/api/datasources", timeout=5)
        if response.status_code == 200:
            datasources = response.json()
            pg_found = False
            
            for ds in datasources:
                if 'postgres' in ds.get('type', '').lower():
                    pg_found = True
                    ds_id = ds.get('id')
                    ds_name = ds.get('name')
                    print(f"    ✓ Found PostgreSQL datasource: {ds_name} (ID: {ds_id})")
                    
                    # Test datasource connection
                    print("      Testing connection...")
                    test_response = session.post(
                        f"{GRAFANA_URL}/api/datasources/{ds_id}/health",
                        timeout=10
                    )
                    test_result = test_response.json()
                    status = test_result.get('message', test_result.get('status', 'Unknown'))
                    
                    if 'OK' in status or 'Database' in status:
                        print(f"      ✓ Connection: {status}")
                    else:
                        print(f"      ✗ Connection: {status}")
                        return False
                    
                    break
            
            if not pg_found:
                print("    ✗ No PostgreSQL datasource found")
                print("    Add PostgreSQL datasource to Grafana:")
                print("    1. Go to http://localhost:3000/connections/datasources")
                print("    2. Add PostgreSQL datasource with:")
                print("       - Host: localhost:5433")
                print("       - Database: unilever_warehouse")
                print("       - User: postgres")
                print("       - Password: 123456")
                return False
        else:
            print(f"    ✗ Failed to get datasources: {response.status_code}")
            return False
        
        print("\n[3] Dashboard check:")
        response = session.get(f"{GRAFANA_URL}/api/dashboards/uid/sales-analytics", timeout=5)
        if response.status_code == 200:
            dashboard = response.json().get('dashboard', {})
            panels = dashboard.get('panels', [])
            print(f"    ✓ Sales Analytics dashboard found ({len(panels)} panels)")
            
            # Check panels have queries
            queries_found = 0
            for panel in panels:
                targets = panel.get('targets', [])
                if targets and any(t.get('rawSql') for t in targets):
                    queries_found += 1
            
            print(f"    ✓ {queries_found} panels with SQL queries")
            
        else:
            print(f"    ✗ Dashboard not found")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to Grafana")
        print("  Check:")
        print("  - Grafana is running on http://localhost:3000")
        print("  - Try accessing http://localhost:3000 in your browser")
        return False
    except Exception as e:
        print(f"✗ Grafana check failed: {e}")
        return False


def main():
    print("\n" + "="*80)
    print("GRAFANA FIX VALIDATION")
    print("="*80)
    
    db_ok = test_database()
    grafana_ok = test_grafana()
    
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print(f"\nDatabase:  {'✓ OK' if db_ok else '✗ FAILED'}")
    print(f"Grafana:   {'✓ OK' if grafana_ok else '✗ FAILED'}")
    
    if db_ok and grafana_ok:
        print("\n" + "╔" + "="*78 + "╗")
        print("║" + " "*20 + "✓ ALL SYSTEMS READY ✓" + " "*36 + "║")
        print("╚" + "="*78 + "╝")
        
        print("\nNEXT STEPS:")
        print("1. Open Grafana: http://localhost:3000")
        print("2. Navigate to Dashboards → Sales Analytics")
        print("3. Refresh the page with Ctrl+F5 (full browser refresh)")
        print("4. All panels should now show data")
        print("\nIf panels are still blank:")
        print("  1. Click Edit on a panel")
        print("  2. Check the query in the Query editor")
        print("  3. Look for red error messages at the bottom")
        print("  4. Verify the datasource is set to 'PostgreSQL Warehouse'")
        print("  5. Click 'Refresh' button to re-run the query")
        
        return 0
    else:
        print("\nISSUES FOUND - Please fix the errors above before proceeding")
        return 1


if __name__ == "__main__":
    sys.exit(main())
