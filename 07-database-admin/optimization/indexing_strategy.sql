-- Phase 7: Database Indexing Strategy
-- Purpose: Create optimal indices for warehouse performance

-- Part 1: Fact Table Indices (High Priority)
CREATE INDEX IF NOT EXISTS idx_fact_sales_date ON fact_sales(date_id);
CREATE INDEX IF NOT EXISTS idx_fact_sales_product ON fact_sales(product_id);
CREATE INDEX IF NOT EXISTS idx_fact_sales_customer ON fact_sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_fact_sales_location ON fact_sales(location_id);

-- Composite indices for common queries
CREATE INDEX IF NOT EXISTS idx_fact_sales_date_product ON fact_sales(date_id, product_id);
CREATE INDEX IF NOT EXISTS idx_fact_sales_customer_date ON fact_sales(customer_id, date_id);

-- Part 2: Dimension Table Indices
CREATE INDEX IF NOT EXISTS idx_dim_product_active ON dim_product(is_active, is_current);
CREATE INDEX IF NOT EXISTS idx_dim_customer_current ON dim_customer(is_current, customer_code);
CREATE INDEX IF NOT EXISTS idx_dim_location_region ON dim_location(region, city);

-- Part 3: Query Optimization Indices
CREATE INDEX IF NOT EXISTS idx_fact_sales_status ON fact_sales(order_status);
CREATE INDEX IF NOT EXISTS idx_fact_sales_payment ON fact_sales(payment_method);
CREATE INDEX IF NOT EXISTS idx_dim_date_calendar ON dim_date(year, month, day);

-- Part 4: Analyze query performance (EXPLAIN PLAN)
EXPLAIN ANALYZE
SELECT 
    DATE(dd.date_value) as sale_date,
    dp.category,
    COUNT(*) as sales_count,
    SUM(fs.total_amount) as total_revenue
FROM fact_sales fs
JOIN dim_date dd ON fs.date_id = dd.date_id
JOIN dim_product dp ON fs.product_id = dp.product_id
WHERE dd.date_value >= CURRENT_DATE - INTERVAL '90 days'
    AND dp.is_active = TRUE
GROUP BY DATE(dd.date_value), dp.category
ORDER BY sale_date DESC, total_revenue DESC;

-- Part 5: Database statistics
ANALYZE fact_sales;
ANALYZE dim_date;
ANALYZE dim_product;
ANALYZE dim_customer;

-- Part 6: Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
