"""
=============================================================
PHASE 2: DATA SOURCE SETUP
Advanced Data Generator with Data Quality Issues
=============================================================
"""

from faker import Faker
import pandas as pd
import random
import os
from datetime import date, timedelta
import uuid

fake = Faker()

# Dynamic date folder
today_str = date.today().isoformat()
folder_path = os.path.join("raw_data", today_str)

os.makedirs(folder_path, exist_ok=True)

# Configuration
NUM_PRODUCTS = 1000
NUM_CUSTOMERS = 4000
NUM_SALES = 50000

# Data quality issue configurations (intentional)
PRODUCT_NULL_RATE = 0.02  # 2% missing values
CUSTOMER_NULL_RATE = 0.03  # 3% missing values
DUPLICATE_RATE = 0.01  # 1% duplicates
OUTLIER_RATE = 0.005  # 0.5% outliers

# ============================================================
# GENERATE PRODUCTS
# ============================================================

def generate_products(n=NUM_PRODUCTS):
    """Generate product data with intentional data quality issues"""
    products = []
    
    for i in range(n):
        product = {
            "product_id": f"P{1000+i}",
            "product_name": fake.word().capitalize(),
            "category": random.choice(["Beauty", "Food", "Personal Care", "Home Care"]),
            "brand": random.choice(["Dove", "Axe", "Omo", "Lux", "Knorr"])
        }
        
        # Introduce missing values
        if random.random() < PRODUCT_NULL_RATE:
            if random.random() < 0.5:
                product["product_name"] = None
            else:
                product["brand"] = None
        
        products.append(product)
    
    # Add some duplicates (data quality issue)
    num_duplicates = int(n * DUPLICATE_RATE)
    for _ in range(num_duplicates):
        duplicate = random.choice(products).copy()
        products.append(duplicate)
    
    products_df = pd.DataFrame(products)
    
    # Shuffle to mix duplicates
    products_df = products_df.sample(frac=1).reset_index(drop=True)
    
    return products_df

# ============================================================
# GENERATE CUSTOMERS
# ============================================================

def generate_customers(n=NUM_CUSTOMERS):
    """Generate customer data with intentional data quality issues"""
    customers = []
    
    for i in range(n):
        customer = {
            "customer_id": f"C{1000+i}",
            "customer_name": fake.name(),
            "email": fake.email(),
            "city": fake.city(),
            "province": random.choice([
                "Gauteng", "Western Cape", "KZN",
                "Eastern Cape", "Limpopo", "Mpumalanga",
                "Free State", "North West", "Northern Cape"
            ])
        }
        
        # Introduce missing values
        if random.random() < CUSTOMER_NULL_RATE:
            if random.random() < 0.33:
                customer["customer_name"] = None
            elif random.random() < 0.5:
                customer["email"] = None
            else:
                customer["city"] = None
        
        customers.append(customer)
    
    # Add some duplicates (data quality issue)
    num_duplicates = int(n * DUPLICATE_RATE)
    for _ in range(num_duplicates):
        duplicate = random.choice(customers).copy()
        customers.append(duplicate)
    
    customers_df = pd.DataFrame(customers)
    customers_df = customers_df.sample(frac=1).reset_index(drop=True)
    
    return customers_df

# ============================================================
# GENERATE SALES
# ============================================================

def generate_sales(products_df, customers_df, n=NUM_SALES):
    """Generate sales data with intentional data quality issues"""
    sales = []
    
    # Date range for sales
    end_date = date.today()
    start_date = end_date - timedelta(days=730)  # 2 years
    
    for i in range(n):
        sale = {
            "sale_id": str(uuid.uuid4()),  # Unique sale ID
            "product_id": random.choice(products_df["product_id"]),
            "customer_id": random.choice(customers_df["customer_id"]),
            "sale_date": fake.date_between(start_date=start_date, end_date=end_date),
            "quantity": random.randint(1, 10),
            "revenue": round(random.uniform(50, 2000), 2)
        }
        
        # Introduce outliers (data quality issue)
        if random.random() < OUTLIER_RATE:
            if random.random() < 0.5:
                sale["quantity"] = random.randint(100, 500)  # Unusually high quantity
            else:
                sale["revenue"] = round(random.uniform(10000, 50000), 2)  # Unusually high revenue
        
        # Introduce negative values (data quality issue)
        if random.random() < 0.001:
            sale["quantity"] = -random.randint(1, 10)
        
        sales.append(sale)
    
    # Add some duplicates (data quality issue)
    num_duplicates = int(n * DUPLICATE_RATE)
    for _ in range(num_duplicates):
        duplicate = random.choice(sales).copy()
        sales.append(duplicate)
    
    sales_df = pd.DataFrame(sales)
    sales_df = sales_df.sample(frac=1).reset_index(drop=True)
    
    return sales_df

# ============================================================
# GENERATE JSON (ALTERNATE FORMAT)
# ============================================================

def generate_products_json(products_df, filepath):
    """Export products as JSON"""
    products_df.to_json(filepath, orient="records", date_format="iso")

def generate_customers_json(customers_df, filepath):
    """Export customers as JSON"""
    customers_df.to_json(filepath, orient="records", date_format="iso")

# ============================================================
# MAIN EXECUTION
# ============================================================



def generate_data(num_customers=4000, num_products=1000, num_sales=50000):
    """Helper function for tests - generates all data types and returns DataFrames"""
    products_df = generate_products(num_products)
    customers_df = generate_customers(num_customers)
    sales_df = generate_sales(products_df, customers_df, num_sales)
    return customers_df, products_df, sales_df


def main():
    print("=" * 60)
    print("GENERATING SAMPLE DATA WITH DATA QUALITY ISSUES")
    print("=" * 60)
    
    print("\nGenerating products...")
    products_df = generate_products()
    products_df.to_csv(os.path.join(folder_path, "products.csv"), index=False)
    print(f"  Products generated: {len(products_df)}")
    print(f"  Missing values: {products_df.isnull().sum().sum()}")
    
    print("\nGenerating customers...")
    customers_df = generate_customers()
    customers_df.to_csv(os.path.join(folder_path, "customers.csv"), index=False)
    print(f"  Customers generated: {len(customers_df)}")
    print(f"  Missing values: {customers_df.isnull().sum().sum()}")
    
    print("\nGenerating sales...")
    sales_df = generate_sales(products_df, customers_df)
    sales_df.to_csv(os.path.join(folder_path, "sales.csv"), index=False)
    print(f"  Sales generated: {len(sales_df)}")
    print(f"  Negative quantities: {(sales_df['quantity'] < 0).sum()}")
    print(f"  High revenue outliers: {(sales_df['revenue'] > 10000).sum()}")
    
    # Also generate JSON files (Phase 2 - multiple formats)
    print("\nGenerating JSON files...")
    generate_products_json(products_df, os.path.join(folder_path, "products.json"))
    generate_customers_json(customers_df, os.path.join(folder_path, "customers.json"))
    print("  JSON files generated")
    
    print("\n" + "=" * 60)
    print(f"Data generated successfully in {folder_path}")
    print("=" * 60)
    print("\nData Quality Issues Introduced:")
    print(f"  - Product missing values: {PRODUCT_NULL_RATE*100}%")
    print(f"  - Customer missing values: {CUSTOMER_NULL_RATE*100}%")
    print(f"  - Duplicates: {DUPLICATE_RATE*100}%")
    print(f"  - Outliers: {OUTLIER_RATE*100}%")
    print(f"  - Negative values: 0.1%")

if __name__ == "__main__":
    main()
