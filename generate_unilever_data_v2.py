#!/usr/bin/env python3
"""
Unilever Sales Data Generator v2
- 25,000 customers (50x)
- 2,500,000 sales records (50x)
- ETL monitoring logs for Grafana ETL dashboard
"""

import psycopg2
import psycopg2.extras
import random
from datetime import date, datetime, timedelta
from faker import Faker

fake = Faker('en_GB')
random.seed(42)

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "unilever_warehouse",
    "user": "postgres",
    "password": "123456"
}

PRODUCTS = [
    ("sku-001", "Dove Body Wash 500ml",        "Personal Care",  "Dove",        89.99),
    ("sku-002", "Dove Soap Bar 6-Pack",         "Personal Care",  "Dove",        54.99),
    ("sku-003", "Dove Shampoo 400ml",           "Personal Care",  "Dove",        74.99),
    ("sku-004", "Axe Black Body Spray",         "Personal Care",  "Axe",         64.99),
    ("sku-005", "Axe Gold Body Wash",           "Personal Care",  "Axe",         79.99),
    ("sku-006", "Rexona Women Deodorant",       "Personal Care",  "Rexona",      49.99),
    ("sku-007", "Rexona Men Deodorant",         "Personal Care",  "Rexona",      49.99),
    ("sku-008", "Sunsilk Shampoo 400ml",        "Personal Care",  "Sunsilk",     59.99),
    ("sku-009", "TRESemme Conditioner",         "Personal Care",  "TRESemme",    84.99),
    ("sku-010", "Vaseline Body Lotion 400ml",   "Personal Care",  "Vaseline",    69.99),
    ("sku-011", "Domestos Bleach 750ml",        "Household",      "Domestos",    34.99),
    ("sku-012", "Handy Andy Cream Cleaner",     "Household",      "Handy Andy",  29.99),
    ("sku-013", "Surf Washing Powder 2kg",      "Household",      "Surf",        89.99),
    ("sku-014", "Skip Auto Washing Powder 2kg", "Household",      "Skip",       109.99),
    ("sku-015", "Comfort Fabric Softener 1L",   "Household",      "Comfort",     49.99),
    ("sku-016", "Sunlight Dishwashing Liquid",  "Household",      "Sunlight",    24.99),
    ("sku-017", "Jif Cream Cleaner 500ml",      "Household",      "Jif",         39.99),
    ("sku-018", "Knorr Chicken Stock 200g",     "Food & Beverage","Knorr",       29.99),
    ("sku-019", "Knorr Beef Stock 200g",        "Food & Beverage","Knorr",       29.99),
    ("sku-020", "Knorr Pasta Sauce 400g",       "Food & Beverage","Knorr",       44.99),
    ("sku-021", "Robertsons Mixed Herbs 20g",   "Food & Beverage","Robertsons",  19.99),
    ("sku-022", "Hellmanns Mayonnaise 750g",    "Food & Beverage","Hellmanns",   59.99),
    ("sku-023", "Lipton Yellow Label Tea 100s", "Food & Beverage","Lipton",      49.99),
    ("sku-024", "Rama Margarine 500g",          "Food & Beverage","Rama",        39.99),
    ("sku-025", "Flora Margarine 500g",         "Food & Beverage","Flora",       44.99),
]

SA_LOCATIONS = [
    ("Johannesburg", "Gauteng"),
    ("Pretoria", "Gauteng"),
    ("Sandton", "Gauteng"),
    ("Midrand", "Gauteng"),
    ("Soweto", "Gauteng"),
    ("Cape Town", "Western Cape"),
    ("Stellenbosch", "Western Cape"),
    ("Paarl", "Western Cape"),
    ("Durban", "KwaZulu-Natal"),
    ("Pietermaritzburg", "KwaZulu-Natal"),
    ("Richards Bay", "KwaZulu-Natal"),
    ("Port Elizabeth", "Eastern Cape"),
    ("East London", "Eastern Cape"),
    ("Mthatha", "Eastern Cape"),
    ("Bloemfontein", "Free State"),
    ("Welkom", "Free State"),
    ("Polokwane", "Limpopo"),
    ("Tzaneen", "Limpopo"),
    ("Nelspruit", "Mpumalanga"),
    ("Witbank", "Mpumalanga"),
    ("Kimberley", "Northern Cape"),
    ("Upington", "Northern Cape"),
    ("Rustenburg", "North West"),
    ("Mahikeng", "North West"),
]


# ==================== GENERATORS ====================

def generate_dates(start_date, end_date):
    dates = []
    current = start_date
    while current <= end_date:
        quarter = (current.month - 1) // 3 + 1
        fiscal_year = current.year if current.month >= 3 else current.year - 1
        fiscal_quarter = ((current.month - 3) % 12) // 3 + 1
        dates.append((
            current,
            current.year,
            current.month,
            current.day,
            quarter,
            current.strftime("%B"),
            current.strftime("%A"),
            current.weekday() >= 5,
            fiscal_year,
            fiscal_quarter
        ))
        current += timedelta(days=1)
    return dates


def generate_customers(n=25000):
    print(f"  Generating {n} customers...")
    customers = []
    for i in range(1, n + 1):
        city, province = random.choice(SA_LOCATIONS)
        customers.append((
            f"CUST-{i:06d}",
            fake.name(),
            fake.email(),
            city,
            province,
            True,
        ))
        if i % 5000 == 0:
            print(f"    {i}/{n} customers generated...")
    return customers


def generate_sales_batch(batch_start, batch_size, date_keys, customer_keys, product_keys, product_weights):
    sales = []
    for i in range(batch_start, batch_start + batch_size):
        sale_id = f"SALE-{i+1:08d}"
        product_key, unit_price = random.choices(product_keys, weights=product_weights)[0]
        customer_key = random.choice(customer_keys)
        date_key = random.choice(date_keys)
        quantity = random.choices([1, 2, 3, 4, 5, 6, 8, 10], weights=[35, 25, 15, 10, 6, 4, 3, 2])[0]
        revenue = round(unit_price * quantity * random.uniform(0.92, 1.08), 2)
        sales.append((sale_id, product_key, customer_key, date_key, quantity, revenue))
    return sales


def generate_etl_logs(start_date, end_date):
    """Generate realistic ETL run logs for monitoring dashboard"""
    logs = []
    log_id = 1
    current = start_date

    dag_tasks = [
        "check_new_files",
        "extract_data",
        "transform_data",
        "load_data",
        "validate_quality",
        "send_notification"
    ]

    while current <= end_date:
        # Daily ETL runs at 2am
        run_start = datetime(current.year, current.month, current.day, 2, 0, 0)

        # 95% success rate, occasional failures
        run_success = random.random() > 0.05
        records_processed = random.randint(800, 3500) if run_success else random.randint(0, 500)
        total_duration = random.randint(180, 480) if run_success else random.randint(20, 120)

        for task in dag_tasks:
            task_start = run_start + timedelta(seconds=random.randint(0, 30))
            task_duration = random.randint(10, 90)

            # If run failed, last few tasks may fail
            if not run_success and task in ["load_data", "validate_quality", "send_notification"]:
                status = random.choice(["failed", "skipped"])
                error_msg = random.choice([
                    "Connection timeout to source database",
                    "Data validation failed: null values in required fields",
                    "Insufficient disk space",
                    "Source file not found",
                    "Transform error: unexpected schema change",
                ]) if status == "failed" else None
            else:
                status = "success"
                error_msg = None

            logs.append((
                log_id,
                "daily_etl_pipeline",
                task,
                status,
                task_start,
                task_start + timedelta(seconds=task_duration),
                task_duration,
                records_processed if task == "load_data" else None,
                error_msg,
                current
            ))
            log_id += 1

        current += timedelta(days=1)

    return logs


def generate_data_quality_logs(start_date, end_date):
    """Generate data quality check results"""
    checks = []
    check_id = 1
    current = start_date

    quality_checks = [
        ("null_check_customer_id", "dim_customer", "completeness"),
        ("null_check_product_id", "dim_product", "completeness"),
        ("revenue_positive_check", "fact_sales", "validity"),
        ("duplicate_sale_id_check", "fact_sales", "uniqueness"),
        ("referential_integrity_product", "fact_sales", "integrity"),
        ("referential_integrity_customer", "fact_sales", "integrity"),
        ("date_range_check", "fact_sales", "validity"),
        ("quantity_range_check", "fact_sales", "validity"),
    ]

    while current <= end_date:
        run_time = datetime(current.year, current.month, current.day, 2, 30, 0)

        for check_name, table_name, check_type in quality_checks:
            passed = random.random() > 0.03
            records_checked = random.randint(5000, 50000)
            records_failed = 0 if passed else random.randint(1, 50)
            score = round(((records_checked - records_failed) / records_checked) * 100, 2)

            checks.append((
                check_id,
                check_name,
                table_name,
                check_type,
                "passed" if passed else "failed",
                records_checked,
                records_failed,
                score,
                run_time,
            ))
            check_id += 1

        current += timedelta(days=1)

    return checks


# ==================== LOADER ====================

def load_data():
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        print("Clearing existing data...")
        cur.execute("TRUNCATE fact_sales, dim_customer, dim_product, dim_date RESTART IDENTITY CASCADE")
        cur.execute("TRUNCATE etl_log, data_quality_log RESTART IDENTITY CASCADE")
        conn.commit()

        # 1. dim_date — extend to 2 years for richer trends
        print("Loading dim_date (2 years)...")
        start_date = date(2024, 1, 1)
        end_date = date(2025, 12, 31)
        dates = generate_dates(start_date, end_date)
        psycopg2.extras.execute_batch(cur, """
            INSERT INTO dim_date (sale_date, year, month, day, quarter, month_name, day_of_week, is_weekend, fiscal_year, fiscal_quarter)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, dates, page_size=500)
        conn.commit()
        print(f"  Loaded {len(dates)} dates")

        # 2. dim_customer — 25,000
        print("Loading dim_customers (25,000)...")
        customers = generate_customers(25000)
        psycopg2.extras.execute_batch(cur, """
            INSERT INTO dim_customer (customer_id, customer_name, email, city, province, is_current)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, customers, page_size=1000)
        conn.commit()
        print(f"  Loaded {len(customers)} customers")

        # 3. dim_product
        print("Loading dim_products (25)...")
        for sku, name, category, brand, _ in PRODUCTS:
            cur.execute("""
                INSERT INTO dim_product (product_id, product_name, category, brand)
                VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING
            """, (sku, name, category, brand))
        conn.commit()
        print(f"  Loaded {len(PRODUCTS)} products")

        # 4. Fetch keys
        cur.execute("SELECT date_key FROM dim_date")
        date_keys = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT customer_key FROM dim_customer")
        customer_keys = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT product_key, product_id FROM dim_product")
        sku_to_price = {p[0]: p[4] for p in PRODUCTS}
        product_keys = [(pk, sku_to_price.get(pid, 49.99)) for pk, pid in cur.fetchall()]
        product_weights = [random.uniform(0.5, 3.0) for _ in product_keys]

        # 5. fact_sales — 2,500,000 in batches of 50,000
        total_records = 2_500_000
        batch_size = 50_000
        print(f"Loading fact_sales ({total_records:,} records in batches)...")

        loaded = 0
        for batch_num in range(total_records // batch_size):
            batch = generate_sales_batch(
                batch_num * batch_size,
                batch_size,
                date_keys,
                customer_keys,
                product_keys,
                product_weights
            )
            psycopg2.extras.execute_batch(cur, """
                INSERT INTO fact_sales (sale_id, product_key, customer_key, date_key, quantity, revenue)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, batch, page_size=1000)
            conn.commit()
            loaded += len(batch)
            print(f"  {loaded:,} / {total_records:,} records loaded...")

        print(f"  Done loading sales.")

        # 6. ETL logs
        print("Loading ETL monitoring logs (2 years of daily runs)...")
        etl_logs = generate_etl_logs(
            datetime(2024, 1, 1),
            datetime(2025, 12, 31)
        )

        # Check etl_log columns
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='etl_log' ORDER BY ordinal_position")
        etl_cols = [r[0] for r in cur.fetchall()]
        print(f"  etl_log columns: {etl_cols}")

        # Insert what we can based on available columns
        for log in etl_logs:
            try:
                cur.execute("""
                    INSERT INTO etl_log (dag_id, task_id, status, start_time, end_time, duration_seconds, records_processed, error_message, run_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (log[1], log[2], log[3], log[4], log[5], log[6], log[7], log[8], log[9]))
            except Exception:
                conn.rollback()
                break
        conn.commit()
        print(f"  Loaded {len(etl_logs)} ETL log entries")

        # 7. Data quality logs
        print("Loading data quality logs...")
        quality_logs = generate_data_quality_logs(
            date(2024, 1, 1),
            date(2025, 12, 31)
        )

        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='data_quality_log' ORDER BY ordinal_position")
        dq_cols = [r[0] for r in cur.fetchall()]
        print(f"  data_quality_log columns: {dq_cols}")

        for log in quality_logs:
            try:
                cur.execute("""
                    INSERT INTO data_quality_log (check_name, table_name, check_type, status, records_checked, records_failed, quality_score, run_timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (log[1], log[2], log[3], log[4], log[5], log[6], log[7], log[8]))
            except Exception:
                conn.rollback()
                break
        conn.commit()
        print(f"  Loaded {len(quality_logs)} data quality log entries")

        # Final verification
        print("\n=== VERIFICATION ===")
        for table in ["fact_sales", "dim_customer", "dim_product", "dim_date", "etl_log", "data_quality_log"]:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            print(f"  {table}: {cur.fetchone()[0]:,} rows")

        cur.execute("SELECT SUM(revenue) FROM fact_sales")
        print(f"  Total revenue: R{cur.fetchone()[0]:,.2f}")
        print("\nAll data loaded successfully!")

    except Exception as e:
        conn.rollback()
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    load_data()
