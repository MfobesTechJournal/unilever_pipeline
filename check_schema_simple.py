#!/usr/bin/env python3
import psycopg2

try:
    conn = psycopg2.connect(host='localhost', port=5433, database='unilever_warehouse', user='postgres', password='123456')
    cursor = conn.cursor()
    
    # Get all columns
    cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'fact_sales' ORDER BY column_name")
    print("Fact_sales columns:")
    for col, dtype in cursor.fetchall():
        print(f"  {col}: {dtype}")
    
    # Get sample data
    cursor.execute("SELECT * FROM fact_sales LIMIT 1")
    print("\nQuery successful - columns exist")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
