"""
=============================================================
PHASE 4: PYTHON ETL PIPELINE DEVELOPMENT
Advanced ETL Pipeline with Data Quality and SCD Type 2
=============================================================
"""

import pandas as pd
from sqlalchemy import create_engine, text
import os
import shutil
from datetime import datetime
import traceback
import logging

print("Starting ETL run...")

# ============================================================
# CONFIGURATION
# ============================================================

RAW_PATH = "raw_data"
STAGING_PATH = "staging"
ARCHIVE_PATH = os.path.join(RAW_PATH, "archive")
DB_URL = "postgresql://postgres:123456@localhost:5433/unilever_warehouse"

# Create necessary folders
os.makedirs(STAGING_PATH, exist_ok=True)
os.makedirs(ARCHIVE_PATH, exist_ok=True)

# ============================================================
# LOGGING SETUP
# ============================================================

# Create logger
logger = logging.getLogger('etl_pipeline')
logger.setLevel(logging.INFO)

# File handler
fh = logging.FileHandler('etl_pipeline.log')
fh.setLevel(logging.INFO)

# Console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

# ============================================================
# DATABASE CONNECTION
# ============================================================

engine = create_engine(DB_URL)

# ============================================================
# ETL LOGGING & CONTROL TABLE SETUP
# ============================================================

with engine.begin() as conn:
    # Create etl_log table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS etl_log (
            run_id SERIAL PRIMARY KEY,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            status VARCHAR(20),
            records_products BIGINT,
            records_customers BIGINT,
            records_dates BIGINT,
            records_facts BIGINT,
            records_quality_issues BIGINT,
            error_message TEXT
        )
    """))
    
    # Create load_batch control table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS load_batch (
            batch_id SERIAL PRIMARY KEY,
            folder_name TEXT UNIQUE,
            load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20)
        )
    """))
    
    # Create data_quality_log table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS data_quality_log (
            log_id SERIAL PRIMARY KEY,
            run_id BIGINT,
            table_name VARCHAR(50),
            check_type VARCHAR(50),
            issue_count BIGINT,
            issue_description TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))

# ============================================================
# DATA QUALITY FUNCTIONS
# ============================================================

def log_quality_issue(conn, run_id, table_name, check_type, count, description):
    """Log data quality issues to database"""
    # Convert numpy types to Python native types
    count = int(count) if hasattr(count, 'item') else int(count)
    conn.execute(text("""
        INSERT INTO data_quality_log 
        (run_id, table_name, check_type, issue_count, issue_description)
        VALUES (:run_id, :table, :check, :count, :description)
    """), {
        "run_id": int(run_id),
        "table": table_name,
        "check": check_type,
        "count": count,
        "description": description
    })

def check_data_quality(df, table_name, conn, run_id):
    """Check data quality and log issues"""
    quality_issues = 0
    
    # Check for nulls
    null_counts = df.isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            quality_issues += count
            logger.warning(f"{table_name}: {count} null values in {col}")
            log_quality_issue(conn, run_id, table_name, "NULL_CHECK", count, 
                            f"Column {col} has {count} null values")
    
    # Check for duplicates
    if table_name == "products":
        dup_count = df.duplicated(subset=['product_id']).sum()
    elif table_name == "customers":
        dup_count = df.duplicated(subset=['customer_id']).sum()
    elif table_name == "sales":
        dup_count = df.duplicated(subset=['sale_id']).sum()
    else:
        dup_count = 0
    
    if dup_count > 0:
        quality_issues += dup_count
        logger.warning(f"{table_name}: {dup_count} duplicate records")
        log_quality_issue(conn, run_id, table_name, "DUPLICATE_CHECK", dup_count,
                         f"Found {dup_count} duplicate records")
    
    # Check for negative values in sales
    if table_name == "sales":
        neg_qty = (df['quantity'] < 0).sum()
        if neg_qty > 0:
            quality_issues += neg_qty
            logger.warning(f"{table_name}: {neg_qty} negative quantities")
            log_quality_issue(conn, run_id, table_name, "NEGATIVE_VALUE", neg_qty,
                            f"Found {neg_qty} negative quantities")
        
        # Check for outliers (unusually high values)
        high_qty = (df['quantity'] > 100).sum()
        high_rev = (df['revenue'] > 10000).sum()
        if high_qty > 0:
            quality_issues += high_qty
            logger.warning(f"{table_name}: {high_qty} unusually high quantities")
            log_quality_issue(conn, run_id, table_name, "OUTLIER", high_qty,
                            f"Found {high_qty} unusually high quantities")
        if high_rev > 0:
            quality_issues += high_rev
            logger.warning(f"{table_name}: {high_rev} unusually high revenues")
            log_quality_issue(conn, run_id, table_name, "OUTLIER", high_rev,
                            f"Found {high_rev} unusually high revenues")
    
    return quality_issues

# ============================================================
# SCD TYPE 2 FUNCTIONS (for dimension tracking)
# ============================================================

def load_dim_product_scd2(conn, products_df):
    """Load product dimension with SCD Type 2"""
    logger.info("Loading product dimension with SCD Type 2...")
    
    # Get existing products
    existing = pd.read_sql("SELECT product_id, product_key, is_current FROM dim_product WHERE is_current = TRUE", conn)
    
    # Find new products
    new_products = products_df[~products_df['product_id'].isin(existing['product_id'])]
    
    # Find changed products
    if not existing.empty:
        merged = products_df.merge(existing, on='product_id', how='left', indicator=True)
        changed = merged[merged['_merge'] == 'both']
        
        # Close out old versions
        for _, row in changed.iterrows():
            conn.execute(text("""
                UPDATE dim_product 
                SET is_current = FALSE, valid_to = CURRENT_TIMESTAMP
                WHERE product_id = :pid AND is_current = TRUE
            """), {"pid": row['product_id']})
        
        # Insert new versions
        for _, row in changed.iterrows():
            new_prod = products_df[products_df['product_id'] == row['product_id']].iloc[0]
            new_prod_dict = {
                'product_id': new_prod['product_id'],
                'product_name': new_prod['product_name'],
                'category': new_prod['category'],
                'brand': new_prod['brand'],
                'is_current': True
            }
            new_df = pd.DataFrame([new_prod_dict])
            new_df.to_sql("dim_product", conn, if_exists="append", index=False)
    
    # Insert truly new products
    if not new_products.empty:
        new_products['is_current'] = True
        new_products.to_sql("dim_product", conn, if_exists="append", index=False)
    
    logger.info(f"Product dimension loaded. New: {len(new_products)}")

# ============================================================
# MAIN ETL PROCESS
# ============================================================

start_time = datetime.now()
run_id = None

try:
    # ============================================================
    # DETECT LATEST RAW FOLDER
    # ============================================================
    
    raw_folders = [f for f in os.listdir(RAW_PATH) if os.path.isdir(os.path.join(RAW_PATH, f)) and f != "archive"]
    if not raw_folders:
        raise ValueError("No raw data folders found!")
    
    latest_raw = sorted(raw_folders)[-1]
    latest_raw_path = os.path.join(RAW_PATH, latest_raw)
    print(f"Latest raw folder detected: {latest_raw}")
    logger.info(f"Processing folder: {latest_raw}")
    
    # ============================================================
    # CHECK IF FOLDER ALREADY PROCESSED
    # ============================================================
    
    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT batch_id FROM load_batch WHERE folder_name = :folder_name"),
            {"folder_name": latest_raw}
        )
        existing = result.fetchone()
        print(f"DEBUG: Checking load_batch for '{latest_raw}'")
        print(f"DEBUG: Query result: {existing}")
        if existing:
            logger.info(f"Folder {latest_raw} already processed. Skipping.")
            print("ETL run skipped - folder already loaded.")
            exit(0)
    
    # ============================================================
    # START RUN LOG
    # ============================================================
    
    with engine.begin() as conn:
        result = conn.execute(
            text("INSERT INTO etl_log (start_time, status) VALUES (:start_time, :status) RETURNING run_id"),
            {"start_time": start_time, "status": "RUNNING"}
        )
        run_id = result.scalar()
    
    # ============================================================
    # MOVE FILES TO STAGING
    # ============================================================
    
    for file in os.listdir(latest_raw_path):
        shutil.copy(os.path.join(latest_raw_path, file), os.path.join(STAGING_PATH, file))
    print("Files moved to staging.")
    logger.info("Files moved to staging")
    
    # ============================================================
    # LOAD CSV FILES
    # ============================================================
    
    products_df = pd.read_csv(os.path.join(STAGING_PATH, "products.csv"))
    customers_df = pd.read_csv(os.path.join(STAGING_PATH, "customers.csv"))
    sales_df = pd.read_csv(os.path.join(STAGING_PATH, "sales.csv"))
    sales_df["sale_date"] = pd.to_datetime(sales_df["sale_date"])
    
    print(f"Products rows: {len(products_df)}")
    print(f"Customers rows: {len(customers_df)}")
    print(f"Sales rows: {len(sales_df)}")
    
    # ============================================================
    # DATA QUALITY CHECKS
    # ============================================================
    
    logger.info("Running data quality checks...")
    quality_issues = 0
    
    with engine.begin() as conn:
        quality_issues += check_data_quality(products_df, "products", conn, run_id)
        quality_issues += check_data_quality(customers_df, "customers", conn, run_id)
        quality_issues += check_data_quality(sales_df, "sales", conn, run_id)
    
    logger.info(f"Data quality issues found: {quality_issues}")
    
    # ============================================================
    # DEDUP DIMENSIONS
    # ============================================================
    
    with engine.begin() as conn:
        # Dim Product
        existing_products = pd.read_sql("SELECT product_id FROM dim_product", conn)
        new_products = products_df[~products_df["product_id"].isin(existing_products["product_id"])]
        if not new_products.empty:
            new_products.to_sql("dim_product", conn, if_exists="append", index=False)
            logger.info(f"Inserted {len(new_products)} new products")
        
        # Dim Customer
        existing_customers = pd.read_sql("SELECT customer_id FROM dim_customer", conn)
        new_customers = customers_df[~customers_df["customer_id"].isin(existing_customers["customer_id"])]
        if not new_customers.empty:
            new_customers.to_sql("dim_customer", conn, if_exists="append", index=False)
            logger.info(f"Inserted {len(new_customers)} new customers")
        
        # Dim Date
        date_df = sales_df[["sale_date"]].drop_duplicates()
        date_df["year"] = date_df["sale_date"].dt.year
        date_df["month"] = date_df["sale_date"].dt.month
        date_df["day"] = date_df["sale_date"].dt.day
        date_df["quarter"] = date_df["sale_date"].dt.quarter
        date_df["month_name"] = date_df["sale_date"].dt.strftime("%B")
        date_df["day_of_week"] = date_df["sale_date"].dt.day_name()
        
        existing_dates = pd.read_sql("SELECT sale_date FROM dim_date", conn)
        existing_dates["sale_date"] = pd.to_datetime(existing_dates["sale_date"])
        new_dates = date_df[~date_df["sale_date"].isin(existing_dates["sale_date"])]
        if not new_dates.empty:
            new_dates.to_sql("dim_date", conn, if_exists="append", index=False)
            logger.info(f"Inserted {len(new_dates)} new dates")
    
    # ============================================================
    # BUILD FACT TABLE
    # ============================================================
    
    with engine.begin() as conn:
        dim_product = pd.read_sql("SELECT product_key, product_id FROM dim_product", conn)
        dim_customer = pd.read_sql("SELECT customer_key, customer_id FROM dim_customer", conn)
        dim_date = pd.read_sql("SELECT date_key, sale_date FROM dim_date", conn)
        dim_date["sale_date"] = pd.to_datetime(dim_date["sale_date"])
        
        # Create staging_sales table
        sales_df.to_sql("staging_sales", conn, if_exists="replace", index=False)
        
        # Insert into fact_sales with ON CONFLICT
        fact_sql = """
            INSERT INTO fact_sales (sale_id, product_key, customer_key, date_key, quantity, revenue)
            SELECT s.sale_id, dp.product_key, dc.customer_key, dd.date_key, s.quantity, s.revenue
            FROM staging_sales s
            JOIN dim_product dp ON s.product_id = dp.product_id
            JOIN dim_customer dc ON s.customer_id = dc.customer_id
            JOIN dim_date dd ON s.sale_date = dd.sale_date
            ON CONFLICT (sale_id) DO NOTHING
        """
        conn.execute(text(fact_sql))
        logger.info("Fact sales loaded")
    
    # ============================================================
    # VALIDATION
    # ============================================================
    
    # Convert numpy types to Python native types
    quality_issues = int(quality_issues) if hasattr(quality_issues, 'item') else int(quality_issues)
    
    with engine.connect() as conn:
        counts = {
            "records_products": int(conn.execute(text("SELECT COUNT(*) FROM dim_product")).scalar()),
            "records_customers": int(conn.execute(text("SELECT COUNT(*) FROM dim_customer")).scalar()),
            "records_dates": int(conn.execute(text("SELECT COUNT(*) FROM dim_date")).scalar()),
            "records_facts": int(conn.execute(text("SELECT COUNT(*) FROM fact_sales")).scalar()),
            "records_quality_issues": quality_issues
        }
    
    logger.info(f"Validation: {counts}")
    
    # ============================================================
    # ARCHIVE RAW FOLDER
    # ============================================================
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_folder = os.path.join(ARCHIVE_PATH, f"{latest_raw}_{timestamp}")
    shutil.move(latest_raw_path, archive_folder)
    print(f"Raw data folder archived to: {archive_folder}")
    logger.info(f"Archived to: {archive_folder}")
    
    # ============================================================
    # RECORD BATCH IN CONTROL TABLE
    # ============================================================
    
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO load_batch (folder_name) VALUES (:folder_name)"),
            {"folder_name": latest_raw}
        )
    
    # ============================================================
    # UPDATE ETL LOG SUCCESS
    # ============================================================
    
    end_time = datetime.now()
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE etl_log
                SET end_time=:end_time,
                    status='SUCCESS',
                    records_products=:records_products,
                    records_customers=:records_customers,
                    records_dates=:records_dates,
                    records_facts=:records_facts,
                    records_quality_issues=:records_quality_issues
                WHERE run_id=:run_id
            """),
            {**counts, "end_time": end_time, "run_id": run_id}
        )
    
    print("ETL run completed successfully.")
    logger.info("ETL completed successfully")

except Exception as e:
    # ============================================================
    # LOG FAILURE
    # ============================================================
    
    end_time = datetime.now()
    error_message = traceback.format_exc()
    logger.error(f"ETL failed: {error_message}")
    
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE etl_log
                SET end_time=:end_time,
                    status='FAILURE',
                    error_message=:error_message
                WHERE run_id=:run_id
            """),
            {"end_time": end_time, "error_message": error_message, "run_id": run_id}
        )
    
    print("ETL failed. Check etl_log table for details.")
    print(error_message)
