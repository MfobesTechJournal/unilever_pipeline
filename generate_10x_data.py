#!/usr/bin/env python3
"""
Generate 10x more sales data
"""

import psycopg2
from datetime import datetime, timedelta
import random
import math

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "unilever_warehouse",
    "user": "postgres",
    "password": "123456"
}

print("\n" + "="*80)
print("GENERATING 10X MORE SALES DATA")
print("="*80)

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Get current record count
    cursor.execute("SELECT COUNT(*) FROM fact_sales")
    current_count = cursor.fetchone()[0]
    print(f"\nCurrent sales records: {current_count:,}")
    
    # Get dimension data
    cursor.execute("SELECT product_key FROM dim_product")
    products = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT customer_key FROM dim_customer")
    customers = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT date_key FROM dim_date")
    dates = [row[0] for row in cursor.fetchall()]
    
    print(f"Products: {len(products)}, Customers: {len(customers)}, Dates: {len(dates)}")
    
    # Generate 9x more data (to make 10x total)
    print(f"\nGenerating {current_count * 9:,} new records...")
    
    new_records = []
    for i in range(current_count * 9):
        if (i + 1) % 50000 == 0:
            print(f"  Generated {i + 1:,} records...")
        
        sales_key = current_count + i + 1
        sale_id = f"SALE-{sales_key:07d}"
        product_key = random.choice(products)
        customer_key = random.choice(customers)
        date_key = random.choice(dates)
        quantity = random.randint(1, 20)
        revenue = round(quantity * random.uniform(20, 200), 2)
        
        new_records.append((
            sales_key, sale_id, product_key, customer_key, date_key,
            quantity, revenue, datetime.now()
        ))
        
        # Insert in batches
        if len(new_records) >= 5000:
            cursor.executemany(
                """INSERT INTO fact_sales 
                (sales_key, sale_id, product_key, customer_key, date_key, quantity, revenue, load_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                new_records
            )
            conn.commit()
            new_records = []
    
    # Insert remaining records
    if new_records:
        cursor.executemany(
            """INSERT INTO fact_sales 
            (sales_key, sale_id, product_key, customer_key, date_key, quantity, revenue, load_timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            new_records
        )
        conn.commit()
    
    # Verify new count
    cursor.execute("SELECT COUNT(*) FROM fact_sales")
    new_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(revenue) FROM fact_sales")
    total_revenue = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\n✓ Complete!")
    print(f"  Old count: {current_count:,}")
    print(f"  New count: {new_count:,}")
    print(f"  Increase: {new_count - current_count:,} records ({(new_count/current_count):.1f}x)")
    print(f"  Total revenue: ${total_revenue:,.2f}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
