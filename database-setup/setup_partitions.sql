-- ============================================================
-- PHASE 7: DATABASE ADMINISTRATION
-- Table Partitioning for Performance
-- ============================================================

-- ============================================================
-- PARTITIONED FACT TABLE
-- ============================================================

-- Drop existing tables if they exist
DROP TABLE IF EXISTS fact_sales_partitioned CASCADE;
DROP TABLE IF EXISTS fact_sales CASCADE;

-- Create partitioned fact table
CREATE TABLE fact_sales (
    sales_key BIGSERIAL,
    sale_id VARCHAR(50) NOT NULL,
    product_key INTEGER NOT NULL,
    customer_key INTEGER NOT NULL,
    date_key INTEGER NOT NULL,
    quantity INTEGER,
    revenue DECIMAL(12, 2),
    load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (sales_key, load_timestamp)
) PARTITION BY RANGE (load_timestamp);

-- ============================================================
-- CREATE PARTITIONS BY MONTH
-- ============================================================

-- 2024 partitions
CREATE TABLE fact_sales_2024_01 PARTITION OF fact_sales
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE fact_sales_2024_02 PARTITION OF fact_sales
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

CREATE TABLE fact_sales_2024_03 PARTITION OF fact_sales
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

CREATE TABLE fact_sales_2024_04 PARTITION OF fact_sales
    FOR VALUES FROM ('2024-04-01') TO ('2024-05-01');

CREATE TABLE fact_sales_2024_05 PARTITION OF fact_sales
    FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');

CREATE TABLE fact_sales_2024_06 PARTITION OF fact_sales
    FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');

CREATE TABLE fact_sales_2024_07 PARTITION OF fact_sales
    FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');

CREATE TABLE fact_sales_2024_08 PARTITION OF fact_sales
    FOR VALUES FROM ('2024-08-01') TO ('2024-09-01');

CREATE TABLE fact_sales_2024_09 PARTITION OF fact_sales
    FOR VALUES FROM ('2024-09-01') TO ('2024-10-01');

CREATE TABLE fact_sales_2024_10 PARTITION OF fact_sales
    FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');

CREATE TABLE fact_sales_2024_11 PARTITION OF fact_sales
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

CREATE TABLE fact_sales_2024_12 PARTITION OF fact_sales
    FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');

-- 2025 partitions
CREATE TABLE fact_sales_2025_01 PARTITION OF fact_sales
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE fact_sales_2025_02 PARTITION OF fact_sales
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

CREATE TABLE fact_sales_2025_03 PARTITION OF fact_sales
    FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');

CREATE TABLE fact_sales_2025_04 PARTITION OF fact_sales
    FOR VALUES FROM ('2025-04-01') TO ('2025-05-01');

CREATE TABLE fact_sales_2025_05 PARTITION OF fact_sales
    FOR VALUES FROM ('2025-05-01') TO ('2025-06-01');

CREATE TABLE fact_sales_2025_06 PARTITION OF fact_sales
    FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');

CREATE TABLE fact_sales_2025_07 PARTITION OF fact_sales
    FOR VALUES FROM ('2025-07-01') TO ('2025-08-01');

CREATE TABLE fact_sales_2025_08 PARTITION OF fact_sales
    FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');

CREATE TABLE fact_sales_2025_09 PARTITION OF fact_sales
    FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');

CREATE TABLE fact_sales_2025_10 PARTITION OF fact_sales
    FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');

CREATE TABLE fact_sales_2025_11 PARTITION OF fact_sales
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

CREATE TABLE fact_sales_2025_12 PARTITION OF fact_sales
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

-- 2026 partitions
CREATE TABLE fact_sales_2026_01 PARTITION OF fact_sales
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE fact_sales_2026_02 PARTITION OF fact_sales
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- Default partition for out-of-range data
CREATE TABLE fact_sales_default PARTITION OF fact_sales DEFAULT;

-- ============================================================
-- ADD CONSTRAINTS TO PARTITIONED TABLE
-- ============================================================

-- Add unique constraint on sale_id
ALTER TABLE fact_sales ADD CONSTRAINT uq_fact_sale UNIQUE (sale_id);

-- Add foreign keys
ALTER TABLE fact_sales ADD CONSTRAINT fk_product 
    FOREIGN KEY (product_key) REFERENCES dim_product(product_key);

ALTER TABLE fact_sales ADD CONSTRAINT fk_customer 
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key);

ALTER TABLE fact_sales ADD CONSTRAINT fk_date 
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key);

-- ============================================================
-- INDEXES FOR PARTITIONED TABLE
-- ============================================================

CREATE INDEX idx_fact_sales_product ON fact_sales(product_key);
CREATE INDEX idx_fact_sales_customer ON fact_sales(customer_key);
CREATE INDEX idx_fact_sales_date ON fact_sales(date_key);
CREATE INDEX idx_fact_sales_sale_id ON fact_sales(sale_id);

PRINT 'Partitioned fact table created successfully!';
