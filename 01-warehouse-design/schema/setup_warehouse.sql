-- ============================================================
-- PHASE 1: DATA WAREHOUSE DESIGN
-- Star Schema for Unilever Sales Data Warehouse
-- ============================================================

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS fact_sales CASCADE;
DROP TABLE IF EXISTS dim_product CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;
DROP TABLE IF EXISTS load_batch CASCADE;
DROP TABLE IF EXISTS etl_log CASCADE;

-- ============================================================
-- DIMENSION TABLES
-- ============================================================

-- Dim Product: Product dimension with surrogate key and SCD Type 2
CREATE TABLE dim_product (
    product_key SERIAL PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL,
    product_name VARCHAR(255),
    category VARCHAR(100),
    brand VARCHAR(100),
    is_current BOOLEAN DEFAULT TRUE,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dim Customer: Customer dimension with surrogate key and SCD Type 2
CREATE TABLE dim_customer (
    customer_key SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    customer_name VARCHAR(255),
    email VARCHAR(255),
    city VARCHAR(100),
    province VARCHAR(100),
    is_current BOOLEAN DEFAULT TRUE,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dim Date: Date dimension with calendar hierarchy
CREATE TABLE dim_date (
    date_key SERIAL PRIMARY KEY,
    sale_date DATE UNIQUE NOT NULL,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    quarter INTEGER,
    month_name VARCHAR(20),
    day_of_week VARCHAR(20),
    is_weekend BOOLEAN,
    fiscal_year INTEGER,
    fiscal_quarter INTEGER
);

-- ============================================================
-- FACT TABLE
-- ============================================================

-- Fact Sales: Transaction fact table
CREATE TABLE fact_sales (
    sales_key SERIAL PRIMARY KEY,
    sale_id VARCHAR(50) UNIQUE NOT NULL,
    product_key INTEGER NOT NULL,
    customer_key INTEGER NOT NULL,
    date_key INTEGER NOT NULL,
    quantity INTEGER,
    revenue DECIMAL(12, 2),
    load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_key) REFERENCES dim_product(product_key),
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);

-- ============================================================
-- CONTROL TABLES
-- ============================================================

-- Load Batch: Track processed folders
CREATE TABLE load_batch (
    batch_id SERIAL PRIMARY KEY,
    folder_name TEXT UNIQUE NOT NULL,
    load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ETL Log: Track ETL runs
CREATE TABLE etl_log (
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
);

-- Data Quality Log: Track data quality issues
CREATE TABLE data_quality_log (
    log_id SERIAL PRIMARY KEY,
    run_id BIGINT REFERENCES etl_log(run_id),
    table_name VARCHAR(50),
    check_type VARCHAR(50),
    issue_count BIGINT,
    issue_description TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SCD TYPE 2 CONSTRAINTS (Using Partial Unique Indexes)
-- ============================================================

-- Ensure only one current version per product (partial unique index)
CREATE UNIQUE INDEX uq_dim_product_current 
    ON dim_product (product_id) 
    WHERE is_current = TRUE;

-- Ensure only one current version per customer (partial unique index)
CREATE UNIQUE INDEX uq_dim_customer_current 
    ON dim_customer (customer_id) 
    WHERE is_current = TRUE;

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================

-- Fact table indexes
CREATE INDEX idx_fact_sales_product ON fact_sales(product_key);
CREATE INDEX idx_fact_sales_customer ON fact_sales(customer_key);
CREATE INDEX idx_fact_sales_date ON fact_sales(date_key);
CREATE INDEX idx_fact_sales_revenue ON fact_sales(revenue);
CREATE INDEX idx_fact_sales_quantity ON fact_sales(quantity);

-- Dimension table indexes
CREATE INDEX idx_dim_product_id ON dim_product(product_id);
CREATE INDEX idx_dim_product_current ON dim_product(product_id, is_current);
CREATE INDEX idx_dim_product_category ON dim_product(category);
CREATE INDEX idx_dim_product_brand ON dim_product(brand);
CREATE INDEX idx_dim_customer_id ON dim_customer(customer_id);
CREATE INDEX idx_dim_customer_current ON dim_customer(customer_id, is_current);
CREATE INDEX idx_dim_customer_province ON dim_customer(province);
CREATE INDEX idx_dim_date_year_month ON dim_date(year, month);
CREATE INDEX idx_dim_date_quarter ON dim_date(quarter);

-- SCD Type 2 indexes
CREATE INDEX idx_dim_product_valid_dates ON dim_product(valid_from, valid_to);
CREATE INDEX idx_dim_customer_valid_dates ON dim_customer(valid_from, valid_to);

-- Control table indexes
CREATE INDEX idx_load_batch_folder ON load_batch(folder_name);
CREATE INDEX idx_etl_log_status ON etl_log(status);
CREATE INDEX idx_etl_log_start_time ON etl_log(start_time);
CREATE INDEX idx_data_quality_run ON data_quality_log(run_id);
CREATE INDEX idx_data_quality_table ON data_quality_log(table_name);

-- ============================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================

COMMENT ON TABLE dim_product IS 'Product dimension with SCD Type 2 - tracks product changes over time';
COMMENT ON TABLE dim_customer IS 'Customer dimension with SCD Type 2 - tracks customer changes over time';
COMMENT ON COLUMN dim_product.is_current IS 'Flag indicating current version (TRUE = current, FALSE = historical)';
COMMENT ON COLUMN dim_product.valid_from IS 'Start date of this dimension version';
COMMENT ON COLUMN dim_product.valid_to IS 'End date of this dimension version (NULL = current)';
COMMENT ON COLUMN dim_customer.is_current IS 'Flag indicating current version (TRUE = current, FALSE = historical)';
COMMENT ON COLUMN dim_customer.valid_from IS 'Start date of this dimension version';
COMMENT ON COLUMN dim_customer.valid_to IS 'End date of this dimension version (NULL = current)';
COMMENT ON TABLE dim_customer IS 'Customer dimension - contains customer information';
COMMENT ON TABLE dim_date IS 'Date dimension - calendar hierarchy for time analysis';
COMMENT ON TABLE fact_sales IS 'Sales fact table - transactional sales data';
COMMENT ON TABLE load_batch IS 'Control table - tracks processed data folders';
COMMENT ON TABLE etl_log IS 'ETL logging table - tracks pipeline execution';
COMMENT ON TABLE data_quality_log IS 'Data quality metrics - tracks quality issues per run';
