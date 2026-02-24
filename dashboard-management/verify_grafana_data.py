import psycopg2
import json
from datetime import datetime

try:
    conn = psycopg2.connect(
        host='localhost', port='5433', 
        database='unilever_warehouse', 
        user='postgres', password='123456'
    )
    cursor = conn.cursor()
    
    print("=" * 60)
    print("GRAFANA DATA VERIFICATION")
    print("=" * 60)
    
    # Check data_quality_log table
    cursor.execute('SELECT COUNT(*) FROM data_quality_log')
    count = cursor.fetchone()[0]
    print(f"\n✓ data_quality_log Records: {count}")
    
    if count > 0:
        # Check breakdown by check_type
        cursor.execute('''
            SELECT check_type, COUNT(*) as count 
            FROM data_quality_log 
            GROUP BY check_type 
            ORDER BY check_type
        ''')
        print("\n  Breakdown by check type:")
        for check_type, cnt in cursor.fetchall():
            print(f"    - {check_type}: {cnt}")
        
        # Check timestamp range
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                MIN(timestamp) as oldest,
                MAX(timestamp) as newest,
                COUNT(CASE WHEN timestamp > NOW() - INTERVAL '30 days' THEN 1 END) as last_30_days
            FROM data_quality_log
        ''')
        total, oldest, newest, last_30 = cursor.fetchone()
        print(f"\n  Timestamps:")
        print(f"    - Oldest: {oldest}")
        print(f"    - Newest: {newest}")
        print(f"    - In last 30 days: {last_30}")
        
        # Sample records
        cursor.execute('''
            SELECT run_id, table_name, check_type, issue_count, timestamp
            FROM data_quality_log 
            ORDER BY timestamp DESC 
            LIMIT 3
        ''')
        print(f"\n  Recent records:")
        for run_id, table_name, check_type, issue_count, ts in cursor.fetchall():
            print(f"    Run {run_id}: {table_name} - {check_type} ({issue_count} issues) @ {ts}")
    
    #  Test Grafana chart query
    print("\n" + "=" * 60)
    print("TESTING GRAFANA TIME-SERIES QUERY")
    print("=" * 60)
    
    query = '''
    SELECT 
        timestamp as time,
        check_type,
        SUM(issue_count) as value
    FROM data_quality_log
    WHERE timestamp > NOW() - INTERVAL '30 days'
    GROUP BY timestamp, check_type
    ORDER BY timestamp DESC
    LIMIT 5
    '''
    
    cursor.execute(query)
    results = cursor.fetchall()
    print(f"\nQuery returned {len(results)} rows")
    if results:
        print("Sample results:")
        for row in results[:3]:
            print(f"  {row}")
    
    print("\n✓ Database connectivity: OK")
    print("✓ Data exists: OK" if count > 0 else "✗ Data exists: MISSING")
    
    # Check if Grafana can see the data
    print("\n" + "=" * 60)
    print("GRAFANA DATASOURCE TEST")
    print("=" * 60)
    print("If above shows data, issue is in dashboard QUERIES, not data.")
    print("Check Grafana dashboard panels for correct table/column names.")
    
except Exception as e:
    print(f"✗ ERROR: {e}")
finally:
    cursor.close()
    conn.close()
