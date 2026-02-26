def get_connection():
    """Get database connection"""
    import psycopg2
    return psycopg2.connect(
        host="localhost",
        port="5433",
        database="unilever_warehouse",
        user="postgres",
        password="123456"
    )


def load_dim_date(cursor):
    """Load date dimension"""
    from datetime import date, timedelta
    
    end_date = date.today()
    start_date = end_date - timedelta(days=730)
    
    dates_to_load = []
    current = start_date
    while current <= end_date:
        dates_to_load.append(current)
        current += timedelta(days=1)
    
    count = 0
    for d in dates_to_load:
        cursor.execute("""
            INSERT INTO dim_date (sale_date, year, month, day, quarter, month_name, day_of_week, is_weekend, fiscal_year, fiscal_quarter)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (sale_date) DO NOTHING
        """, (
            d,
            d.year,
            d.month,
            d.day,
            (d.month - 1) // 3 + 1,
            d.strftime('%B'),
            d.strftime('%A'),
            d.weekday() >= 5,
            d.year,
            (d.month - 1) // 3 + 1
        ))
        count += 1
    
    return count


def load_dim_product(cursor):
    """Load product dimension from CSV"""
    import pandas as pd
    
    df = pd.read_csv('staging/products.csv')
    count = 0
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO dim_product (product_id, product_name, category, brand, is_current, valid_from)
            VALUES (%s, %s, %s, %s, TRUE, NOW())
            ON CONFLICT DO NOTHING
        """, (str(row['product_id']), str(row['product_name']), str(row['category']), str(row['brand'])))
        count += 1
    return count


def load_dim_customer(cursor):
    """Load customer dimension from CSV"""
    import pandas as pd
    
    df = pd.read_csv('staging/customers.csv')
    count = 0
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO dim_customer (customer_id, customer_name, email, city, province, is_current, valid_from)
            VALUES (%s, %s, %s, %s, %s, TRUE, NOW())
            ON CONFLICT DO NOTHING
        """, (str(row['customer_id']), str(row['customer_name']), str(row['email']), str(row['city']), str(row['province'])))
        count += 1
    return count


def load_fact_sales(cursor):
    """Load sales fact table from CSV"""
    import pandas as pd
    
    df = pd.read_csv('staging/sales.csv')
    count = 0
    for _, row in df.iterrows():
        # Get keys from dimension tables
        cursor.execute("SELECT product_key FROM dim_product WHERE product_id = %s LIMIT 1", (str(row['product_id']),))
        product_result = cursor.fetchone()
        product_key = product_result[0] if product_result else None
        
        cursor.execute("SELECT customer_key FROM dim_customer WHERE customer_id = %s LIMIT 1", (str(row['customer_id']),))
        customer_result = cursor.fetchone()
        customer_key = customer_result[0] if customer_result else None
        
        from datetime import datetime
        sale_date = datetime.strptime(str(row['sale_date']), '%Y-%m-%d').date()
        cursor.execute("SELECT date_key FROM dim_date WHERE sale_date = %s LIMIT 1", (sale_date,))
        date_result = cursor.fetchone()
        date_key = date_result[0] if date_result else None
        
        if product_key and customer_key and date_key:
            cursor.execute("""
                INSERT INTO fact_sales (sale_id, product_key, customer_key, date_key, quantity, revenue)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (str(row['sale_id']), product_key, customer_key, date_key, int(row['quantity']), float(row['revenue'])))
            count += 1
    
    return count


# Main pipeline execution
conn = None
cursor = None

try:
    conn = get_connection()
    cursor = conn.cursor()
    
    print("[1/4] Loading date dimension...")
    rows = load_dim_date(cursor)
    print(f"  Loaded {rows} date records")
    
    print("[2/4] Loading product dimension...")
    rows = load_dim_product(cursor)
    print(f"  Loaded {rows} product records")
    
    print("[3/4] Loading customer dimension...")
    rows = load_dim_customer(cursor)
    print(f"  Loaded {rows} customer records")
    
    print("[4/4] Loading sales fact table...")
    rows = load_fact_sales(cursor)
    print(f"  Loaded {rows} sales records")
    
    conn.commit()
    print("\nPipeline completed successfully!")

except Exception as e:
    print(f"\nError during pipeline execution: {e}")
    if conn:
        conn.rollback()
    raise

finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()

