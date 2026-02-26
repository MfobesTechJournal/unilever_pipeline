-- Phase 1: Star Schema Design
-- University ETL Project - Data Warehouse Schema

-- Part 1: Drop existing objects (for reset)
DROP TABLE IF EXISTS fact_sales CASCADE;
DROP TABLE IF EXISTS dim_product CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;
DROP TABLE IF EXISTS dim_location CASCADE;
DROP TABLE IF EXISTS etl_log CASCADE;
DROP TABLE IF EXISTS data_quality_log CASCADE;

-- Part 2: Dimension Tables

-- Dimension: Date (Calendar Hierarchy)
CREATE TABLE dim_date (
    date_id SERIAL PRIMARY KEY,
    date_value DATE UNIQUE NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_of_week VARCHAR(10) NOT NULL,
    week_of_year INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    is_holiday BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_date_value ON dim_date(date_value);

-- Dimension: Product
CREATE TABLE dim_product (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    price DECIMAL(10, 2),
    cost DECIMAL(10, 2),
    supplier VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_product_name ON dim_product(product_name);
CREATE INDEX idx_dim_product_category ON dim_product(category);

-- Dimension: Customer (SCD Type 2)
CREATE TABLE dim_customer (
    customer_id SERIAL PRIMARY KEY,
    customer_code VARCHAR(20) UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    city VARCHAR(100),
    state VARCHAR(50),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    customer_segment VARCHAR(50),
    lifetime_value DECIMAL(12, 2),
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_customer_code ON dim_customer(customer_code);
CREATE INDEX idx_dim_customer_city ON dim_customer(city);
CREATE INDEX idx_dim_customer_current ON dim_customer(is_current);

-- Dimension: Location
CREATE TABLE dim_location (
    location_id SERIAL PRIMARY KEY,
    location_name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    state VARCHAR(50),
    country VARCHAR(100),
    region VARCHAR(100),
    postal_code VARCHAR(20),
    latitude DECIMAL(9, 6),
    longitude DECIMAL(9, 6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_location_city ON dim_location(city);
CREATE INDEX idx_dim_location_region ON dim_location(region);

-- Part 3: Fact Table

CREATE TABLE fact_sales (
    sales_id BIGSERIAL PRIMARY KEY,
    date_id INTEGER NOT NULL REFERENCES dim_date(date_id),
    product_id INTEGER NOT NULL REFERENCES dim_product(product_id),
    customer_id INTEGER NOT NULL REFERENCES dim_customer(customer_id),
    location_id INTEGER REFERENCES dim_location(location_id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    extended_amount DECIMAL(12, 2) NOT NULL,
    discount_amount DECIMAL(12, 2) DEFAULT 0,
    net_amount DECIMAL(12, 2) NOT NULL,
    tax_amount DECIMAL(12, 2) DEFAULT 0,
    total_amount DECIMAL(12, 2) NOT NULL,
    cost_amount DECIMAL(12, 2),
    profit_amount DECIMAL(12, 2),
    order_status VARCHAR(50),
    payment_method VARCHAR(50),
    shipping_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (date_id);

-- Create partitions by year (for performance)
CREATE TABLE fact_sales_2024 PARTITION OF fact_sales
    FOR VALUES FROM (1) TO (366);

CREATE TABLE fact_sales_2025 PARTITION OF fact_sales
    FOR VALUES FROM (366) TO (731);

CREATE TABLE fact_sales_2026 PARTITION OF fact_sales
    FOR VALUES FROM (731) TO (1096);

-- Fact table indices
CREATE INDEX idx_fact_sales_date ON fact_sales(date_id);
CREATE INDEX idx_fact_sales_product ON fact_sales(product_id);
CREATE INDEX idx_fact_sales_customer ON fact_sales(customer_id);
CREATE INDEX idx_fact_sales_status ON fact_sales(order_status);

-- Part 4: Metadata & Logging Tables

-- ETL Execution Log
CREATE TABLE etl_log (
    run_id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    run_status VARCHAR(20) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds DECIMAL(10, 2),
    records_extracted BIGINT DEFAULT 0,
    records_transformed BIGINT DEFAULT 0,
    records_loaded BIGINT DEFAULT 0,
    error_message TEXT,
    error_details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_etl_log_status ON etl_log(run_status);
CREATE INDEX idx_etl_log_start ON etl_log(start_time);

-- Data Quality Log
CREATE TABLE data_quality_log (
    quality_id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES etl_log(run_id),
    table_name VARCHAR(100),
    check_type VARCHAR(100),
    check_description VARCHAR(255),
    severity VARCHAR(20),
    record_count BIGINT,
    issue_count BIGINT,
    quality_score DECIMAL(5, 2),
    details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Part 5: Views for Analytics

CREATE VIEW v_sales_summary AS
SELECT
    ds.date_id,
    DATE(dd.date_value) as sale_date,
    COUNT(*) as total_sales,
    SUM(fs.quantity) as total_quantity,
    SUM(fs.total_amount) as total_revenue,
    AVG(fs.total_amount) as avg_order_value,
    SUM(fs.cost_amount) as total_cost,
    SUM(fs.profit_amount) as total_profit
FROM fact_sales fs
JOIN dim_date dd ON fs.date_id = dd.date_id
GROUP BY ds.date_id, DATE(dd.date_value);

-- Part 6: Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO postgres;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres;

COMMIT;
