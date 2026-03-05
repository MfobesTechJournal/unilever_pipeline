#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(
    host='localhost', 
    port=5433, 
    database='unilever_warehouse', 
    user='postgres', 
    password='123456'
)
cur = conn.cursor()

# Get all tables
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
tables = cur.fetchall()

print("Tables in warehouse:")
for t in tables:
    # Get record count for each table
    try:
        cur.execute(f"SELECT COUNT(*) FROM {t[0]}")
        count = cur.fetchone()[0]
        print(f"  - {t[0]}: {count:,} records")
    except:
        print(f"  - {t[0]}: (unable to count)")

conn.close()
