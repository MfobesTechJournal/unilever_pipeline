#!/usr/bin/env python3
"""
Check if data exists in PostgreSQL warehouse database.
"""

import psycopg2
import sys

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "unilever_warehouse",
    "user": "postgres",
    "password": "123456"
}

try:
    print("\n" + "="*70)
    print("DATABASE DATA VERIFICATION")
    print("="*70)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Check each table
    print("\nWarehouse Tables:")
    tables = ['fact_sales', 'dim_customer', 'dim_product', 'dim_date']
    total_records = 0
    
    for table in tables:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            total_records += count
            status = '✓' if count > 0 else '✗ EMPTY'
            print(f'{status} {table}: {count:,} records')
        except Exception as e:
            print(f'✗ {table}: ERROR - {e}')
    
    print(f"\nTotal Records: {total_records:,}")
    
    # Show sample data
    if total_records > 0:
        print("\nSample fact_sales data:")
        cursor.execute('SELECT sales_key, sale_id, quantity, revenue FROM fact_sales LIMIT 2')
        for i, row in enumerate(cursor.fetchall(), 1):
            print(f'  Row {i}: {row}')
    
    # Check if Grafana can access
    print("\nDatabase Status: ✓ ACCESSIBLE")
    print("="*70)
    
    if total_records == 0:
        print("\n✗ WARNING: Database is empty - NO DATA TO DISPLAY")
        print("  Need to run data load script")
        sys.exit(1)
    else:
        print(f"\n✓ Database has {total_records:,} records ready to display")
        sys.exit(0)
    
    cursor.close()
    conn.close()

except Exception as e:
    print(f"\n✗ Database Connection Error: {e}")
    print("\nCheck:")
    print("  • PostgreSQL is running: docker ps | grep postgres")
    print("  • Port 5433 is accessible")
    print("  • Credentials: postgres / 123456")
    sys.exit(1)
