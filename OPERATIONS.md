# Unilever Data Warehouse - Operations Runbook

## Table of Contents
1. [Getting Started](#getting-started)
2. [Daily Operations](#daily-operations)
3. [Monitoring](#monitoring)
4. [Troubleshooting](#troubleshooting)
5. [Maintenance](#maintenance)
6. [Disaster Recovery](#disaster-recovery)
7. [Performance Tuning](#performance-tuning)

---

## Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL 14+
- Docker & Docker Compose (optional)
- Git

### Initial Setup

1. **Clone and configure the repository:**
```bash
git clone https://github.com/yourusername/unilever_pipeline.git
cd unilever_pipeline
cp .env.example .env
# Edit .env with your environment-specific settings
```

2. **Create Python virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

3. **Set up the database:**
```bash
# Using Docker Compose (recommended)
docker-compose up -d postgres pgadmin

# Or manually connect to PostgreSQL
psql -U postgres -h localhost -p 5433 -d unilever_warehouse -f setup_warehouse.sql
psql -U postgres -h localhost -p 5433 -d unilever_warehouse -f setup_partitions.sql
```

4. **Generate sample data:**
```bash
python generate_data.py
```

5. **Run initial ETL:**
```bash
python etl_load_staging.py
```

---

## Daily Operations

### Starting the Pipeline

#### Option 1: Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f airflow-webserver

# Stop all services
docker-compose down
```

#### Option 2: Manual Shell Script
```bash
# Run data ingestion
./ingest_data.sh --run

# View logs
tail -f logs/ingestion_*.log
```

#### Option 3: Airflow DAG
```bash
# Access Airflow UI
# http://localhost:8080

# Trigger DAG manually
airflow dags trigger unilever_etl_pipeline
```

### Monitoring Pipeline Status

#### Check Recent Runs
```python
python monitor_etl.py
```

#### View ETL Logs in Database
```sql
-- Last 10 ETL runs
SELECT run_id, start_time, end_time, status, error_message
FROM etl_log
ORDER BY start_time DESC
LIMIT 10;

-- Shows run_id, timing, status, and error messages
```

#### Check Data Quality Issues
```sql
-- Latest data quality checks
SELECT * FROM data_quality_log
WHERE run_id = (SELECT MAX(run_id) FROM etl_log WHERE status = 'SUCCESS')
ORDER BY timestamp DESC;
```

### Processing New Data

1. **Place CSV files in raw_data folder:**
```bash
# Create daily folder
mkdir -p raw_data/2026-02-18

# Copy your CSV files
cp *.csv raw_data/2026-02-18/
```

2. **Trigger ingestion:**
```bash
# Automatic (if cron is configured)
# Or manual trigger
python etl_load_staging.py
```

3. **Verify results:**
```sql
-- Check fact table row count
SELECT COUNT(*) FROM fact_sales;

-- View latest loads
SELECT * FROM load_batch ORDER BY load_timestamp DESC LIMIT 1;
```

---

## Monitoring

### Dashboard Access

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **PgAdmin**: http://localhost:5050 (admin@unilever.com/admin123)
- **Airflow**: http://localhost:8080

### Key Metrics to Monitor

#### ETL Pipeline Health
```sql
-- Success rate (last 30 days)
SELECT 
    COUNT(*) FILTER (WHERE status = 'SUCCESS') as successful,
    COUNT(*) FILTER (WHERE status = 'FAILURE') as failed,
    ROUND(100 * COUNT(*) FILTER (WHERE status = 'SUCCESS') / COUNT(*), 2) as success_rate
FROM etl_log
WHERE start_time > NOW() - INTERVAL '30 days';
```

#### Data Volume
```sql
-- Data growth over time
SELECT 
    DATE(load_timestamp) as load_date,
    COUNT(*) as new_records
FROM fact_sales
WHERE load_timestamp > NOW() - INTERVAL '30 days'
GROUP BY DATE(load_timestamp)
ORDER BY load_date DESC;
```

#### Data Quality
```sql
-- Quality issues summary
SELECT 
    check_type,
    SUM(issue_count) as total_issues,
    COUNT(*) as occurrences
FROM data_quality_log
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY check_type
ORDER BY total_issues DESC;
```

### Alert Thresholds

Set up alerts in Grafana for:

| Metric | Threshold | Action |
|--------|-----------|--------|
| ETL Failure Rate | > 10% in 24h | Investigate ETL logs |
| Data Quality Issues | > 100 per run | Review data sources |
| Processing Time | > 5 minutes | Check database performance |
| Failed Runs | > 3 consecutive | Page on-call engineer |

---

## Troubleshooting

### Common Issues and Solutions

#### 1. **Database Connection Failures**

**Error:** `FATAL: password authentication failed`

**Solution:**
```bash
# Verify credentials in .env
echo "DB_HOST=${DB_HOST}"
echo "DB_PORT=${DB_PORT}"
echo "DB_USER=${DB_USER}"

# Test connection
psql -h localhost -p 5433 -U postgres -d unilever_warehouse -c "SELECT 1"

# Reset password in Docker
docker-compose exec postgres psql -U postgres -c "ALTER USER postgres PASSWORD '123456';"
```

#### 2. **ETL Run Failures**

**Error:** `Folder already processed`

**Solution:**
```sql
-- Check processed folders
SELECT * FROM load_batch WHERE status = 'FAILED';

-- If needed, reset a failed batch
UPDATE load_batch 
SET status = 'RETRY' 
WHERE folder_name = 'raw_data/2026-02-18' 
AND status = 'FAILED';

-- Delete and retry
DELETE FROM load_batch WHERE folder_name = 'raw_data/2026-02-18';
```

#### 3. **Duplicate Key Violations**

**Error:** `duplicate key value violates unique constraint`

**Solution:**
```sql
-- Check for duplicate sale_ids
SELECT sale_id, COUNT(*)
FROM fact_sales
GROUP BY sale_id
HAVING COUNT(*) > 1;

-- If production issue occurred, inspect ETL logs
SELECT error_message FROM etl_log 
WHERE status = 'FAILURE' 
ORDER BY start_time DESC LIMIT 1;
```

#### 4. **Missing Dimension Records**

**Error:** `Foreign key constraint fails`

**Solution:**
```sql
-- Check for orphaned facts
SELECT COUNT(*) FROM fact_sales 
WHERE product_key NOT IN (SELECT product_key FROM dim_product);

-- Reload dimensions
python etl_load_staging.py --reload-dimensions

-- Or manually reload from staging
INSERT INTO dim_product (product_id, product_name, category, brand)
SELECT DISTINCT product_id, product_name, category, brand
FROM staging_sales
WHERE product_id NOT IN (SELECT product_id FROM dim_product)
ON CONFLICT (product_id) DO NOTHING;
```

#### 5. **Disk Space Issues**

**Solution:**
```sql
-- Check table sizes
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Archive old data
DELETE FROM fact_sales 
WHERE load_timestamp < NOW() - INTERVAL '2 years';

-- Vacuum and analyze
VACUUM ANALYZE fact_sales;
```

#### 6. **Slow Query Performance**

**Solution:**
```sql
-- Analyze query plan
EXPLAIN ANALYZE
SELECT * FROM fact_sales 
WHERE date_key = 100 AND customer_key = 50;

-- Create missing indexes
CREATE INDEX idx_fact_sales_date_customer 
ON fact_sales(date_key, customer_key);

-- Reindex
REINDEX TABLE fact_sales;
```

---

## Maintenance

### Regular Maintenance Tasks

#### Daily (Automated)
- ETL pipeline run
- Data quality checks
- Error log review

#### Weekly
```bash
# Analyze and vacuum tables
python db_optimize.py

# Check index usage
python -c "
import psycopg2
conn = psycopg2.connect('postgresql://postgres:123456@localhost:5433/unilever_warehouse')
cur = conn.cursor()
cur.execute('''SELECT indexrelname, idx_scan FROM pg_stat_user_indexes ORDER BY idx_scan DESC LIMIT 10''')
for row in cur:
    print(f'{row[0]}: {row[1]} scans')
"
```

#### Monthly
```sql
-- Full maintenance
VACUUM ANALYZE;
REINDEX DATABASE unilever_warehouse;

-- Partition management
-- Create new partitions for upcoming months
CREATE TABLE fact_sales_2026_03 PARTITION OF fact_sales
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
```

#### Quarterly
- Review and archive old data
- Update statistics
- Capacity planning review

### Backup Strategy

#### Automated Backups
```bash
# Daily backup (via Docker)
docker-compose exec postgres pg_dump -U postgres unilever_warehouse > backup_$(date +%Y%m%d).sql

# Or use shell script
pg_dump -h localhost -U postgres -p 5433 unilever_warehouse > backup_daily.sql
```

#### Restore from Backup
```bash
# Restore full database
psql -U postgres -h localhost -p 5433 unilever_warehouse < backup_20260218.sql

# Or restore via Docker
docker-compose exec postgres psql -U postgres unilever_warehouse < backup_20260218.sql
```

---

## Disaster Recovery

### Data Loss Scenario

**Scenario:** Accidental deletion of fact_sales records

**Recovery Steps:**

1. **Identify the issue:**
```sql
SELECT COUNT(*) FROM fact_sales;  -- Should be > 0
```

2. **Check backup integrity:**
```bash
ls -lh backup_*.sql
```

3. **Restore from backup:**
```bash
# Create test table first
psql -h localhost -p 5433 -U postgres unilever_warehouse -c "CREATE TABLE fact_sales_restored AS TABLE fact_sales WITH NO DATA;"

# Restore backup to separate database
createdb -h localhost -U postgres unilever_warehouse_restore
psql -h localhost -U postgres unilever_warehouse_restore < backup_20260218.sql

# Compare and fix
SELECT COUNT(*) FROM unilever_warehouse_restore.fact_sales;
```

4. **Rebuild from raw data:**
```bash
# If backup unavailable, rebuild from archived raw data
mkdir -p raw_data/recovery
cp raw_data/archive/*/*.csv raw_data/recovery/
python etl_load_staging.py --raw-folder raw_data/recovery
```

### Service Outage Recovery

**Scenario:** Services down for > 1 hour

```bash
# 1. Check service status
docker-compose ps

# 2. Restart services
docker-compose restart

# 3. Verify connections
python -c "import psycopg2; psycopg2.connect('postgresql://postgres:123456@localhost:5433/unilever_warehouse')"

# 4. Resubmit missed runs
python etl_load_staging.py --retry-failed

# 5. Verify data integrity
python monitor_etl.py
```

---

## Performance Tuning

### Query Optimization

```sql
-- Identify slow queries
SELECT query, mean_exec_time 
FROM pg_stat_statements 
WHERE query LIKE '%fact_%'
ORDER BY mean_exec_time DESC LIMIT 10;

-- Add indexes for common queries
CREATE INDEX idx_fact_sales_period ON fact_sales(date_key, product_key, customer_key);

-- Use EXPLAIN to analyze
EXPLAIN (ANALYZE, BUFFERS) 
SELECT COUNT(*) FROM fact_sales 
WHERE date_key BETWEEN 100 AND 200;
```

### Bulk Load Optimization

```python
# For large data loads, disable indexes temporarily
ALTER TABLE fact_sales DISABLE TRIGGER ALL;
-- Load data here
ALTER TABLE fact_sales ENABLE TRIGGER ALL;
REINDEX TABLE fact_sales;
```

### Connection Pool Tuning

```bash
# Edit docker-compose.yml or .env
# Set optimal pool sizes based on workload
SQLALCHEMY_POOL_SIZE=20
SQLALCHEMY_MAX_OVERFLOW=10
SQLALCHEMY_POOL_TIMEOUT=30
```

---

## Contact & Support

For issues or questions:

1. Check logs: `logs/` directory
2. Review database: Query `etl_log` and `data_quality_log` tables
3. Contact: operations@unilever-pipeline.com
4. Escalate: engineering-team@unilever-pipeline.com

---

**Last Updated:** February 2026
**Version:** 1.0
