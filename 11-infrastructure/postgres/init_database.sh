#!/bin/bash
#
# PHASE 11: Infrastructure
# PostgreSQL Initialization Script
# Run this to set up the database with all required objects
#

set -euo pipefail

DB_HOST="${1:-localhost}"
DB_PORT="${2:-5432}"
DB_USER="${3:-postgres}"
DB_PASS="${4:-postgres}"
DB_NAME="unilever_warehouse"

echo "=========================================="
echo "PostgreSQL Database Initialization"
echo "=========================================="
echo "Host: $DB_HOST"
echo "Port: $DB_PORT"
echo "User: $DB_USER"
echo "Database: $DB_NAME"
echo ""

# Create database
echo "Creating database..."
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -tc \
    "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c \
    "CREATE DATABASE $DB_NAME;"

echo "✓ Database created/verified: $DB_NAME"

# Create schema
echo "Creating star schema..."
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'

-- Create extensions
CREATE EXTENSION IF NOT EXISTS uuid-ossp;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create date dimension
CREATE TABLE IF NOT EXISTS dim_date (
    date_id SERIAL PRIMARY KEY,
    full_date DATE UNIQUE,
    year INT,
    quarter INT,
    month INT,
    week INT,
    day INT,
    holiday_flag BOOLEAN DEFAULT FALSE,
    weekend_flag BOOLEAN DEFAULT FALSE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create product dimension
CREATE TABLE IF NOT EXISTS dim_product (
    product_id SERIAL PRIMARY KEY,
    product_code VARCHAR(50) UNIQUE,
    product_name VARCHAR(255),
    category VARCHAR(100),
    brand VARCHAR(100),
    unit_price DECIMAL(10,2),
    unit_cost DECIMAL(10,2),
    supplier_id INT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create customer dimension (SCD Type 2)
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key SERIAL PRIMARY KEY,
    customer_id VARCHAR(50),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    country VARCHAR(50),
    state_province VARCHAR(50),
    city VARCHAR(100),
    customer_segment VARCHAR(50),
    lifetime_value DECIMAL(10,2),
    is_current BOOLEAN DEFAULT TRUE,
    start_date DATE,
    end_date DATE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, start_date)
);

-- Create location/store dimension
CREATE TABLE IF NOT EXISTS dim_location (
    location_id SERIAL PRIMARY KEY,
    store_code VARCHAR(50) UNIQUE,
    store_name VARCHAR(255),
    store_type VARCHAR(50),
    country VARCHAR(50),
    state_province VARCHAR(50),
    city VARCHAR(100),
    address TEXT,
    manager_name VARCHAR(100),
    store_size_sqft INT,
    employees_count INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create fact table
CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id SERIAL PRIMARY KEY,
    date_id INT REFERENCES dim_date(date_id),
    product_id INT REFERENCES dim_product(product_id),
    customer_key INT REFERENCES dim_customer(customer_key),
    location_id INT REFERENCES dim_location(location_id),
    quantity INT,
    unit_price DECIMAL(10,2),
    discount_percent DECIMAL(5,2) DEFAULT 0,
    sale_amount DECIMAL(10,2),
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (date_id);

-- Create metadata tables
CREATE TABLE IF NOT EXISTS etl_log (
    execution_id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100),
    execution_status VARCHAR(50),
    records_processed INT,
    records_failed INT DEFAULT 0,
    duration_seconds DECIMAL(10,2),
    start_timestamp TIMESTAMP,
    end_timestamp TIMESTAMP,
    error_message TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS data_quality_log (
    check_id SERIAL PRIMARY KEY,
    table_name VARCHAR(100),
    metric_name VARCHAR(100),
    metric_value DECIMAL(10,4),
    check_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indices
CREATE INDEX idx_fact_date ON fact_sales(date_id);
CREATE INDEX idx_fact_product ON fact_sales(product_id);
CREATE INDEX idx_fact_customer ON fact_sales(customer_key);
CREATE INDEX idx_fact_location ON fact_sales(location_id);
CREATE UNIQUE INDEX idx_customer_current ON dim_customer(customer_id) WHERE is_current = TRUE;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO public;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO public;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO public;

EOF

echo "✓ Schema created successfully"

# Initialize date dimension (365 days)
echo "Initializing date dimension..."
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'

INSERT INTO dim_date (full_date, year, quarter, month, week, day, holiday_flag, weekend_flag)
SELECT 
    d,
    EXTRACT(YEAR FROM d)::INT,
    EXTRACT(QUARTER FROM d)::INT,
    EXTRACT(MONTH FROM d)::INT,
    EXTRACT(WEEK FROM d)::INT,
    EXTRACT(DAY FROM d)::INT,
    CASE WHEN EXTRACT(MONTH FROM d) IN (12, 1) AND EXTRACT(DAY FROM d) IN (25, 1) THEN TRUE ELSE FALSE END,
    CASE WHEN EXTRACT(DOW FROM d) IN (0, 6) THEN TRUE ELSE FALSE END
FROM generate_series(CURRENT_DATE - INTERVAL '365 days', CURRENT_DATE + INTERVAL '365 days', INTERVAL '1 day') d
ON CONFLICT (full_date) DO NOTHING;

EOF

echo "✓ Date dimension initialized"
echo ""
echo "=========================================="
echo "Database initialization complete!"
echo "Ready for ETL pipeline"
echo "=========================================="
