import psycopg2
import psycopg2.extras
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('en_GB')
random.seed(42)

NEON_URL = "postgresql://neondb_owner:npg_TyiBWMpxN30z@ep-mute-feather-ae8fkh9o.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require"

PRODUCTS = [
    ("P001","Dove Body Wash 500ml","Personal Care","Dove"),
    ("P002","Dove Soap Bar 150g","Personal Care","Dove"),
    ("P003","Dove Shampoo 400ml","Personal Care","Dove"),
    ("P004","Axe Body Spray 150ml","Personal Care","Axe"),
    ("P005","Axe Body Wash 400ml","Personal Care","Axe"),
    ("P006","Rexona Deodorant Roll-On 50ml","Personal Care","Rexona"),
    ("P007","Rexona Deodorant Spray 150ml","Personal Care","Rexona"),
    ("P008","Sunsilk Shampoo 400ml","Personal Care","Sunsilk"),
    ("P009","TRESemme Shampoo 500ml","Personal Care","TRESemme"),
    ("P010","Vaseline Body Lotion 400ml","Personal Care","Vaseline"),
    ("P011","Domestos Bleach 750ml","Household","Domestos"),
    ("P012","Handy Andy Cream 500ml","Household","Handy Andy"),
    ("P013","Surf Washing Powder 2kg","Household","Surf"),
    ("P014","Skip Auto Washing Powder 2kg","Household","Skip"),
    ("P015","Comfort Fabric Softener 1L","Household","Comfort"),
    ("P016","Sunlight Dishwashing Liquid 750ml","Household","Sunlight"),
    ("P017","Jif Cream Cleaner 500ml","Household","Jif"),
    ("P018","Knorr Chicken Stock 200g","Food & Beverage","Knorr"),
    ("P019","Knorr Tomato Sauce 400ml","Food & Beverage","Knorr"),
    ("P020","Robertsons Spice Mix 50g","Food & Beverage","Robertsons"),
    ("P021","Hellmanns Mayonnaise 750ml","Food & Beverage","Hellmanns"),
    ("P022","Lipton Yellow Label Tea 100s","Food & Beverage","Lipton"),
    ("P023","Rama Margarine 500g","Food & Beverage","Rama"),
    ("P024","Flora Margarine 500g","Food & Beverage","Flora"),
    ("P025","Knorr Soup Mix 50g","Food & Beverage","Knorr"),
]

CITIES = [
    ("Johannesburg","Gauteng"),("Pretoria","Gauteng"),("Sandton","Gauteng"),
    ("Midrand","Gauteng"),("Soweto","Gauteng"),("Cape Town","Western Cape"),
    ("Stellenbosch","Western Cape"),("Paarl","Western Cape"),
    ("Durban","KwaZulu-Natal"),("Pietermaritzburg","KwaZulu-Natal"),
    ("Richards Bay","KwaZulu-Natal"),("Port Elizabeth","Eastern Cape"),
    ("East London","Eastern Cape"),("Mthatha","Eastern Cape"),
    ("Bloemfontein","Free State"),("Welkom","Free State"),
    ("Polokwane","Limpopo"),("Tzaneen","Limpopo"),
    ("Nelspruit","Mpumalanga"),("Witbank","Mpumalanga"),
    ("Kimberley","Northern Cape"),("Upington","Northern Cape"),
    ("Rustenburg","North West"),("Mahikeng","North West"),
]

PRICES = {
    "P001":89.99,"P002":34.99,"P003":79.99,"P004":69.99,"P005":74.99,
    "P006":49.99,"P007":64.99,"P008":79.99,"P009":89.99,"P010":69.99,
    "P011":39.99,"P012":44.99,"P013":119.99,"P014":129.99,"P015":59.99,
    "P016":49.99,"P017":54.99,"P018":29.99,"P019":34.99,"P020":24.99,
    "P021":79.99,"P022":59.99,"P023":44.99,"P024":49.99,"P025":19.99,
}

ERROR_MESSAGES = [
    "Connection timeout to source database",
    "Data validation failed: null values in required fields",
    "Transform error: unexpected schema change",
    "Duplicate key violation on fact_sales",
    "Memory limit exceeded during transformation",
]

QUALITY_CHECKS = [
    ("dim_customer","completeness","Null customer_id values detected"),
    ("dim_product","completeness","Null product_id values detected"),
    ("fact_sales","validity","Negative revenue values found"),
    ("fact_sales","uniqueness","Duplicate sale_id records detected"),
    ("fact_sales","integrity","Orphaned product_key references"),
    ("fact_sales","integrity","Orphaned customer_key references"),
    ("fact_sales","validity","Sale dates outside expected range"),
    ("fact_sales","validity","Quantity values out of valid range"),
]


def connect():
    return psycopg2.connect(NEON_URL, connect_timeout=30)


def run(conn, fn):
    try:
        cur = conn.cursor()
        fn(cur)
        conn.commit()
        cur.close()
    except Exception as e:
        try:
            conn.rollback()
        except:
            pass
        raise e


def create_schema():
    print("Creating schema...")
    conn = connect()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS data_quality_log CASCADE")
    cur.execute("DROP TABLE IF EXISTS fact_sales CASCADE")
    cur.execute("DROP TABLE IF EXISTS etl_log CASCADE")
    cur.execute("DROP TABLE IF EXISTS dim_customer CASCADE")
    cur.execute("DROP TABLE IF EXISTS dim_product CASCADE")
    cur.execute("DROP TABLE IF EXISTS dim_date CASCADE")
    cur.execute("""
        CREATE TABLE dim_date (
            date_key INTEGER PRIMARY KEY, sale_date DATE,
            year INTEGER, month INTEGER, day INTEGER, quarter INTEGER,
            month_name VARCHAR(20), day_of_week VARCHAR(20), is_weekend BOOLEAN,
            fiscal_year INTEGER, fiscal_quarter INTEGER)""")
    cur.execute("""
        CREATE TABLE dim_product (
            product_key SERIAL PRIMARY KEY, product_id VARCHAR(20) UNIQUE,
            product_name VARCHAR(200), category VARCHAR(100), brand VARCHAR(100),
            is_current BOOLEAN DEFAULT TRUE, valid_from DATE, valid_to DATE)""")
    cur.execute("""
        CREATE TABLE dim_customer (
            customer_key SERIAL PRIMARY KEY, customer_id VARCHAR(20) UNIQUE,
            customer_name VARCHAR(200), email VARCHAR(200),
            city VARCHAR(100), province VARCHAR(100),
            is_current BOOLEAN DEFAULT TRUE, valid_from DATE, valid_to DATE)""")
    cur.execute("""
        CREATE TABLE fact_sales (
            sale_key SERIAL PRIMARY KEY, sale_id VARCHAR(50) UNIQUE,
            product_key INTEGER REFERENCES dim_product(product_key),
            customer_key INTEGER REFERENCES dim_customer(customer_key),
            date_key INTEGER REFERENCES dim_date(date_key),
            quantity INTEGER, revenue DECIMAL(12,2),
            load_timestamp TIMESTAMP DEFAULT NOW())""")
    cur.execute("""
        CREATE TABLE etl_log (
            run_id SERIAL PRIMARY KEY, start_time TIMESTAMP, end_time TIMESTAMP,
            status VARCHAR(20), records_products BIGINT, records_customers BIGINT,
            records_dates BIGINT, records_facts BIGINT, records_quality_issues BIGINT,
            error_message TEXT)""")
    cur.execute("""
        CREATE TABLE data_quality_log (
            log_id SERIAL PRIMARY KEY, run_id BIGINT REFERENCES etl_log(run_id),
            table_name VARCHAR(50), check_type VARCHAR(50), issue_count BIGINT,
            issue_description TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    cur.close()
    conn.close()
    print("  Schema created")


def load_dates():
    print("Loading dim_date...")
    conn = connect()
    cur = conn.cursor()
    rows = []
    start = datetime(2024, 1, 1)
    for i in range(731):
        d = start + timedelta(days=i)
        rows.append((int(d.strftime('%Y%m%d')), d.date(), d.year, d.month, d.day,
            (d.month-1)//3+1, d.strftime('%B'), d.strftime('%A'), d.weekday()>=5,
            d.year if d.month>=3 else d.year-1,
            (d.month-3)//3+1 if d.month>=3 else (d.month+9)//3))
    psycopg2.extras.execute_batch(cur,
        "INSERT INTO dim_date VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
        rows, page_size=200)
    conn.commit()
    cur.close()
    conn.close()
    print(f"  {len(rows)} dates loaded")


def load_products():
    print("Loading dim_product...")
    conn = connect()
    cur = conn.cursor()
    rows = [(pid,name,cat,brand,True,datetime(2024,1,1).date(),None) for pid,name,cat,brand in PRODUCTS]
    psycopg2.extras.execute_batch(cur,
        "INSERT INTO dim_product (product_id,product_name,category,brand,is_current,valid_from,valid_to) VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
        rows)
    conn.commit()
    cur.close()
    conn.close()
    print(f"  {len(rows)} products loaded")


def load_customers():
    print("Loading dim_customer (25,000)...")
    rows = []
    for i in range(25000):
        city, province = random.choice(CITIES)
        rows.append((f"C{i+1:06d}", fake.name(), fake.email(), city, province,
                     True, datetime(2024,1,1).date(), None))
        if (i+1) % 5000 == 0:
            print(f"  {i+1:,}/25,000")

    # Insert in chunks with fresh connection each time
    chunk = 2500
    for i in range(0, len(rows), chunk):
        conn = connect()
        cur = conn.cursor()
        psycopg2.extras.execute_batch(cur,
            "INSERT INTO dim_customer (customer_id,customer_name,email,city,province,is_current,valid_from,valid_to) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            rows[i:i+chunk], page_size=500)
        conn.commit()
        cur.close()
        conn.close()
    print("  25,000 customers loaded")


def load_sales():
    print("Loading fact_sales (2,500,000)...")

    # Fetch lookup data
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT product_key, product_id FROM dim_product")
    products = cur.fetchall()
    cur.execute("SELECT customer_key FROM dim_customer")
    customers = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT date_key FROM dim_date")
    date_keys = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()

    n = 2500000
    batch_size = 25000
    loaded = 0
    batch = []

    for i in range(n):
        pk, pid = random.choice(products)
        ck = random.choice(customers)
        dk = random.choice(date_keys)
        qty = random.randint(1, 10)
        price = PRICES.get(pid, 50.0)
        rev = round(qty * price * random.uniform(0.9, 1.1), 2)
        batch.append((f"S{i+1:09d}", pk, ck, dk, qty, rev))

        if len(batch) >= batch_size:
            conn = connect()
            cur = conn.cursor()
            psycopg2.extras.execute_batch(cur,
                "INSERT INTO fact_sales (sale_id,product_key,customer_key,date_key,quantity,revenue) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                batch, page_size=1000)
            conn.commit()
            cur.close()
            conn.close()
            loaded += len(batch)
            print(f"  {loaded:,}/{n:,}")
            batch = []

    if batch:
        conn = connect()
        cur = conn.cursor()
        psycopg2.extras.execute_batch(cur,
            "INSERT INTO fact_sales (sale_id,product_key,customer_key,date_key,quantity,revenue) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            batch, page_size=1000)
        conn.commit()
        cur.close()
        conn.close()
        loaded += len(batch)
    print(f"  {loaded:,} sales loaded")


def load_etl_logs():
    print("Loading etl_log...")
    rows = []
    current = datetime(2024, 1, 1)
    while current <= datetime(2025, 12, 31):
        start = current.replace(hour=2, minute=0, second=0)
        success = random.random() > 0.05
        duration = random.randint(180, 480) if success else random.randint(20, 120)
        end = start + timedelta(seconds=duration)
        if success:
            rows.append((start, end, 'success', random.randint(20,30),
                random.randint(450,600), 365, random.randint(800,3500),
                random.randint(0,3), None))
        else:
            rows.append((start, end, 'failed', 0, 0, 0, 0, 0, random.choice(ERROR_MESSAGES)))
        current += timedelta(days=1)

    conn = connect()
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur,
        "INSERT INTO etl_log (start_time,end_time,status,records_products,records_customers,records_dates,records_facts,records_quality_issues,error_message) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        rows, page_size=200)
    conn.commit()
    cur.close()
    conn.close()
    print(f"  {len(rows)} ETL logs loaded")


def load_quality_logs():
    print("Loading data_quality_log...")
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT run_id, start_time FROM etl_log ORDER BY run_id")
    runs = cur.fetchall()
    cur.close()
    conn.close()

    rows = []
    for run_id, run_time in runs:
        for table, check_type, desc in QUALITY_CHECKS:
            has_issue = random.random() < 0.04
            issue_count = random.randint(1, 50) if has_issue else 0
            rows.append((run_id, table, check_type, issue_count,
                         desc if has_issue else None, run_time))

    chunk = 1000
    for i in range(0, len(rows), chunk):
        conn = connect()
        cur = conn.cursor()
        psycopg2.extras.execute_batch(cur,
            "INSERT INTO data_quality_log (run_id,table_name,check_type,issue_count,issue_description,timestamp) VALUES (%s,%s,%s,%s,%s,%s)",
            rows[i:i+chunk], page_size=500)
        conn.commit()
        cur.close()
        conn.close()
    print(f"  {len(rows)} quality log entries loaded")


def verify():
    print("\n=== VERIFICATION ===")
    conn = connect()
    cur = conn.cursor()
    for table in ['fact_sales','dim_customer','dim_product','dim_date','etl_log','data_quality_log']:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"  {table}: {cur.fetchone()[0]:,}")
    cur.execute("SELECT ROUND(SUM(revenue)::numeric, 2) FROM fact_sales")
    print(f"  Total revenue: R{cur.fetchone()[0]:,}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    create_schema()
    load_dates()
    load_products()
    load_customers()
    load_sales()
    load_etl_logs()
    load_quality_logs()
    verify()
    print("\nNeon migration complete!")
