#!/usr/bin/env python3
"""
Unilever Sales Data Generator
Generates realistic data and loads it into unilever_warehouse
Tables: dim_date, dim_customer, dim_product, fact_sales
"""

import psycopg2
import random
from datetime import date, timedelta
from faker import Faker

fake = Faker('en_GB')
random.seed(42)

# ==================== DB CONFIG ====================
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "unilever_warehouse",
    "user": "postgres",
    "password": "123456"
}

# ==================== UNILEVER PRODUCT DATA ====================
PRODUCTS = [
    # (sku, name, category, brand, unit_price) — price used for revenue calc only
    # Personal Care
    ("sku-001", "Dove Body Wash 500ml", "Personal Care", "Dove", 89.99),
    ("sku-002", "Dove Soap Bar 6-Pack", "Personal Care", "Dove", 54.99),
    ("sku-003", "Dove Shampoo 400ml", "Personal Care", "Dove", 74.99),
    ("sku-004", "Axe Black Body Spray", "Personal Care", "Axe", 64.99),
    ("sku-005", "Axe Gold Body Wash", "Personal Care", "Axe", 79.99),
    ("sku-006", "Rexona Women Deodorant", "Personal Care", "Rexona", 49.99),
    ("sku-007", "Rexona Men Deodorant", "Personal Care", "Rexona", 49.99),
    ("sku-008", "Sunsilk Shampoo 400ml", "Personal Care", "Sunsilk", 59.99),
    ("sku-009", "TRESemme Conditioner", "Personal Care", "TRESemme", 84.99),
    ("sku-010", "Vaseline Body Lotion 400ml", "Personal Care", "Vaseline", 69.99),
    # Household Cleaning
    ("sku-011", "Domestos Bleach 750ml", "Household", "Domestos", 34.99),
    ("sku-012", "Handy Andy Cream Cleaner", "Household", "Handy Andy", 29.99),
    ("sku-013", "Surf Washing Powder 2kg", "Household", "Surf", 89.99),
    ("sku-014", "Skip Auto Washing Powder 2kg", "Household", "Skip", 109.99),
    ("sku-015", "Comfort Fabric Softener 1L", "Household", "Comfort", 49.99),
    ("sku-016", "Sunlight Dishwashing Liquid", "Household", "Sunlight", 24.99),
    ("sku-017", "Jif Cream Cleaner 500ml", "Household", "Jif", 39.99),
    # Food & Beverage
    ("sku-018", "Knorr Chicken Stock 200g", "Food & Beverage", "Knorr", 29.99),
    ("sku-019", "Knorr Beef Stock 200g", "Food & Beverage", "Knorr", 29.99),
    ("sku-020", "Knorr Pasta Sauce 400g", "Food & Beverage", "Knorr", 44.99),
    ("sku-021", "Robertsons Mixed Herbs 20g", "Food & Beverage", "Robertsons", 19.99),
    ("sku-022", "Hellmanns Mayonnaise 750g", "Food & Beverage", "Hellmanns", 59.99),
    ("sku-023", "Lipton Yellow Label Tea 100s", "Food & Beverage", "Lipton", 49.99),
    ("sku-024", "Rama Margarine 500g", "Food & Beverage", "Rama", 39.99),
    ("sku-025", "Flora Margarine 500g", "Food & Beverage", "Flora", 44.99),
]

# South African provinces and cities
SA_LOCATIONS = [
    ("Johannesburg", "Gauteng"),
    ("Pretoria", "Gauteng"),
    ("Sandton", "Gauteng"),
    ("Cape Town", "Western Cape"),
    ("Stellenbosch", "Western Cape"),
    ("Durban", "KwaZulu-Natal"),
    ("Pietermaritzburg", "KwaZulu-Natal"),
    ("Port Elizabeth", "Eastern Cape"),
    ("East London", "Eastern Cape"),
    ("Bloemfontein", "Free State"),
    ("Polokwane", "Limpopo"),
    ("Nelspruit", "Mpumalanga"),
    ("Kimberley", "Northern Cape"),
    ("Rustenburg", "North West"),
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


def generate_customers(n=500):
    customers = []
    for i in range(1, n + 1):
        city, province = random.choice(SA_LOCATIONS)
        name = fake.name()
        email = fake.email()
        customers.append((
            f"CUST-{i:05d}",
            name,
            email,
            city,
            province,
            True,
        ))
    return customers


def generate_products():
    return PRODUCTS


def generate_sales(num_records, date_keys, customer_keys, product_keys):
    sales = []
    sale_ids = set()
    
    # Weight products so some sell more than others
    product_weights = [random.uniform(0.5, 3.0) for _ in product_keys]
    
    for i in range(num_records):
        sale_id = f"SALE-{i+1:07d}"
        if sale_id in sale_ids:
            continue
        sale_ids.add(sale_id)

        product_key, unit_price = random.choices(
            [(pk, pp) for pk, pp in product_keys],
            weights=product_weights
        )[0]
        customer_key = random.choice(customer_keys)
        date_key = random.choice(date_keys)

        # Weekend and seasonal boosts
        quantity = random.choices([1, 2, 3, 4, 5, 6], weights=[40, 25, 15, 10, 6, 4])[0]
        revenue = round(unit_price * quantity * random.uniform(0.95, 1.05), 2)

        sales.append((
            sale_id,
            product_key,
            customer_key,
            date_key,
            quantity,
            revenue
        ))
    return sales


# ==================== LOADER ====================

def load_data():
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        # Clear existing data in correct order
        print("Clearing existing data...")
        cur.execute("TRUNCATE fact_sales, dim_customer, dim_product, dim_date RESTART IDENTITY CASCADE")
        conn.commit()

        # 1. Load dim_date (12 months of data)
        print("Loading dim_date...")
        start_date = date(2025, 1, 1)
        end_date = date(2025, 12, 31)
        dates = generate_dates(start_date, end_date)
        cur.executemany("""
            INSERT INTO dim_date (sale_date, year, month, day, quarter, month_name, day_of_week, is_weekend, fiscal_year, fiscal_quarter)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, dates)
        conn.commit()
        print(f"  Loaded {len(dates)} dates")

        # 2. Load dim_customer
        print("Loading dim_customers...")
        customers = generate_customers(500)
        cur.executemany("""
            INSERT INTO dim_customer (customer_id, customer_name, email, city, province, is_current)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, customers)
        conn.commit()
        print(f"  Loaded {len(customers)} customers")

        # 3. Load dim_product
        print("Loading dim_products...")
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='dim_product' ORDER BY ordinal_position")
        cols = [r[0] for r in cur.fetchall()]
        print(f"  dim_product columns: {cols}")

        # Insert products — no unit_price column in dim_product
        products = generate_products()
        for p in products:
            sku, name, category, brand, _ = p
            cur.execute("""
                INSERT INTO dim_product (product_id, product_name, category, brand)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (sku, name, category, brand))
        conn.commit()
        print(f"  Loaded {len(products)} products")

        # 4. Fetch keys for fact table
        cur.execute("SELECT date_key FROM dim_date")
        date_keys = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT customer_key FROM dim_customer")
        customer_keys = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT product_key FROM dim_product")
        product_keys_raw = [r[0] for r in cur.fetchall()]
        # Pair product_key with its price from PRODUCTS list for revenue calc
        product_price_map = {p[0]: p[4] for p in products}
        product_sku_map = {}
        cur.execute("SELECT product_key, product_id FROM dim_product")
        for pk, pid in cur.fetchall():
            product_sku_map[pk] = pid
        product_keys = [(pk, product_price_map.get(product_sku_map.get(pk), 49.99)) for pk in product_keys_raw]

        # 5. Load fact_sales
        print("Loading fact_sales (50,000 records)...")
        sales = generate_sales(50000, date_keys, customer_keys, product_keys)
        cur.executemany("""
            INSERT INTO fact_sales (sale_id, product_key, customer_key, date_key, quantity, revenue)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, sales)
        conn.commit()
        print(f"  Loaded {len(sales)} sales records")

        # Verify
        cur.execute("SELECT COUNT(*) FROM fact_sales")
        print(f"\nVerification - fact_sales rows: {cur.fetchone()[0]}")
        cur.execute("SELECT COUNT(*) FROM dim_customer")
        print(f"Verification - dim_customer rows: {cur.fetchone()[0]}")
        cur.execute("SELECT COUNT(*) FROM dim_product")
        print(f"Verification - dim_product rows: {cur.fetchone()[0]}")
        cur.execute("SELECT COUNT(*) FROM dim_date")
        print(f"Verification - dim_date rows: {cur.fetchone()[0]}")
        cur.execute("SELECT SUM(revenue) FROM fact_sales")
        print(f"Verification - Total revenue: R{cur.fetchone()[0]:,.2f}")

        print("\nData loaded successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    load_data()
