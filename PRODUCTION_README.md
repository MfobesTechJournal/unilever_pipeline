# 🏭 Unilever ETL Data Warehouse - Production Deployment Guide

## 📊 Project Overview

Enterprise-grade ETL pipeline for loading Unilever sales data into a production data warehouse with:
- ✅ Automated daily data processing
- ✅ Real-time monitoring and alerting
- ✅ Data quality validation
- ✅ Disaster recovery capabilities
- ✅ Complete audit trails

---

## 🚀 Quick Start (5 minutes)

### Prerequisites
- Docker Desktop (running)
- Python 3.8+
- PostgreSQL client tools
- 10+ GB free disk space

### Step 1: Start Docker Stack
```bash
docker-compose up -d --wait
```

### Step 2: Generate Test Data
```bash
python generate_data.py
```

### Step 3: Run Production ETL
```bash
python etl_production.py
```

### Step 4: View Dashboards
- **Grafana:** http://localhost:3000 (admin/admin)
- **Airflow:** http://localhost:8080 (airflow/airflow)
- **pgAdmin:** http://localhost:5050 (admin@unilever.com/admin123)
- **Prometheus:** http://localhost:9090

---

## 📋 Complete Setup Guide

### 1. Environment Configuration

Create `.env` file in project root:

```bash
# Database
DATABASE_URL=postgresql://postgres:123456@localhost:5433/unilever_warehouse
DB_HOST=localhost
DB_PORT=5433
DB_NAME=unilever_warehouse
DB_USER=postgres
DB_PASSWORD=123456

# Execution
ENVIRONMENT=production
MAX_RETRIES=3
RETRY_DELAY=5
BATCH_SIZE=10000

# Paths
RAW_DATA_PATH=raw_data
STAGING_PATH=staging
LOG_PATH=logs

# Monitoring
ENABLE_NOTIFICATIONS=true
ALERT_EMAIL=alerts@unilever.com
ALERT_THRESHOLD=100

# Backup
BACKUP_PATH=backups
RETENTION_DAYS=30
```

### 2. Start Docker Stack

```bash
# Bring up all services
docker-compose up -d --wait

# Verify services
docker-compose ps

# Expected output:
# NAME                   STATUS
# unilever_postgres      Up (healthy)
# unilever_pgadmin       Up (healthy)
# unilever_airflow       Up (healthy)
# unilever_airflow_scheduler  Up (healthy)
# unilever_prometheus    Up (healthy)
# unilever_grafana       Up (healthy)
```

### 3. Initialize Database

```bash
# The database automatically initializes on first run
# To manually initialize:
docker-compose exec postgres psql -U postgres -d unilever_warehouse -f setup_warehouse.sql
```

### 4. Configure Airflow

```bash
# Access Airflow UI
# http://localhost:8080

# Login with: airflow / airflow

# Enable the DAG:
# 1. Navigate to DAGs
# 2. Find 'unilever_etl_production'
# 3. Toggle the DAG on (blue toggle)
```

### 5. Setup Monitoring

```bash
# Access Grafana
# http://localhost:3000

# Login with: admin / admin

# Import dashboards:
# 1. Settings → Data Sources
# 2. Add PostgreSQL datasource
# 3. Host: postgres (Docker networking)
# 4. Database: unilever_warehouse
# 5. User: postgres / Password: 123456
```

---

## 🔄 Running the ETL Pipeline

### Manual Execution

```bash
# Full pipeline
python etl_production.py

# Expected output:
# ======================================================================
# 🚀 Production ETL Pipeline Started (Env: production)
# ======================================================================
# 2026-02-19 14:30:00,123 - etl_pipeline_prod - INFO - Database connected
# 2026-02-19 14:30:05,456 - etl_pipeline_prod - INFO - ✅ Loaded 1000 products
# 2026-02-19 14:30:10,789 - etl_pipeline_prod - INFO - ✅ Loaded 4000 customers
# 2026-02-19 14:30:45,012 - etl_pipeline_prod - INFO - ✅ Loaded 150000 sales
# ======================================================================
# ✅ ETL Pipeline Result:
# {
#   "run_id": 1,
#   "status": "SUCCESS",
#   "metrics": {...}
# }
# ======================================================================
```

### Scheduled Execution (Airflow)

The DAG runs automatically every day at 2 AM UTC.

```bash
# Manually trigger DAG
docker-compose exec airflow airflow trigger_dag unilever_etl_production -e 2026-02-19

# View DAG status
docker-compose exec airflow airflow list_dag_runs -d unilever_etl_production

# View task status
docker-compose exec airflow airflow list_tasks -d unilever_etl_production
```

---

## 🔍 Monitoring & Alerting

### Cloud Dashboards

**ETL Monitoring Dashboard:** http://localhost:3000/d/etl-monitoring
- Processing time trends
- Run status distribution  
- Records loaded by type
- Data quality issues timeline
- Recent run details

**Data Quality Dashboard:** http://localhost:3000/d/data-quality
- Null values (24h)
- Duplicates (24h)
- Outliers (24h)
- Negative values (24h)
- Quality issues over time

### Email Alerts

Alerts triggered on:
- ❌ ETL pipeline failure
- ⚠️ Data quality issues > threshold
- 🔴 SLA breach (>6 hours processing time)
- 📊 Quality score < 95%

Configure email in `.env`:
```bash
ALERT_EMAIL=your-email@unilever.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Query Live Metrics

```bash
# Connect to database
docker-compose exec postgres psql -U postgres -d unilever_warehouse

# Recent runs
SELECT run_id, start_time, status, records_products, records_facts FROM etl_log ORDER BY run_id DESC LIMIT 10;

# Quality issues
SELECT * FROM data_quality_log WHERE timestamp > NOW() - INTERVAL '24 hours' ORDER BY timestamp DESC;

# Data volumes
SELECT 'Products' as table_name, COUNT(*) as record_count FROM dim_product
UNION ALL
SELECT 'Customers', COUNT(*) FROM dim_customer
UNION ALL
SELECT 'Sales', COUNT(*) FROM fact_sales;
```

---

## 🔐 Security & Access Control

### Database Users

```sql
-- Read-only role (data analysts)
CREATE ROLE analyst LOGIN PASSWORD 'password123';
GRANT CONNECT ON DATABASE unilever_warehouse TO analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analyst;

-- ETL role (pipeline)
CREATE ROLE etl_user LOGIN PASSWORD 'etl_password123';
GRANT CONNECT, CREATE ON DATABASE unilever_warehouse TO etl_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO etl_user;

-- Audit role
CREATE ROLE auditor LOGIN PASSWORD 'audit_password123';
GRANT SELECT ON etl_log, data_quality_log TO auditor;
```

### Secrets Management

For production, use AWS Secrets Manager or HashiCorp Vault:

```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name unilever/database/password \
  --secret-string '{"password":"secure-password-here"}'
```

### Data Encryption

```bash
# Enable SSL for database connections
export DATABASE_URL="postgresql://user:pass@localhost:5433/db?sslmode=require"

# Backup encryption (GPG)
gpg --symmetric backups/unilever_warehouse_*.sql
```

---

## 📦 Backup & Disaster Recovery

### Create Backup

```bash
bash backup_restore.sh backup

# Output:
# ✅ Backup created: backups/unilever_warehouse_20260219_143000.sql
# ✅ Backup size: 256 MB
# ✅ Verified successfully
```

### Scheduled Backups (Cron)

```bash
# Add to crontab
crontab -e

# Daily backup at 1 AM
0 1 * * * cd /path/to/unilever_pipeline && bash backup_restore.sh backup

# Weekly full backup + cleanup
0 2 * * 0 cd /path/to/unilever_pipeline && bash backup_restore.sh backup && bash backup_restore.sh cleanup
```

### Restore from Backup

```bash
bash backup_restore.sh restore backups/unilever_warehouse_20260219_143000.sql

# Prompts: Type 'YES' to confirm
# Creates pre-restore backup automatically
```

### Disaster Recovery Plan

**RTO (Recovery Time Objective):** 30 minutes  
**RPO (Recovery Point Objective):** 24 hours

1. **Detection:** Monitoring alerts on pipeline failure
2. **Investigation:** Check logs in `logs/` directory
3. **Mitigation:** Run `etl_production.py` with `--retry` flag
4. **Recovery:** Restore from backup if data is corrupted
5. **Verification:** Run data quality checks post-recovery

---

## 🧪 Testing & Quality Assurance

### Run Test Suite

```bash
# Unit tests
python -m pytest tests/test_etl.py -v

# Integration tests
python -m pytest tests/test_integration.py -v

# Performance tests
python -m pytest tests/test_performance.py -v

# Data quality tests
python -m pytest tests/test_quality.py -v
```

### Sample Tests

```python
# tests/test_quality.py
import pytest
from etl_production import DataQualityChecker
import pandas as pd

def test_null_detection():
    data = pd.DataFrame({
        'id': [1, 2, None],
        'value': [10, None, 30]
    })
    issues = DataQualityChecker.check_nulls(data, 'test_table')
    assert len(issues) > 0

def test_duplicate_detection():
    data = pd.DataFrame({
        'id': [1, 1, 2],
        'value': [10, 10, 20]
    })
    duplicates = DataQualityChecker.check_duplicates(data, ['id'], 'test_table')
    assert duplicates == 1
```

---

## 🐛 Troubleshooting

### Issue: "Database connection failed"

```bash
# Check database status
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U postgres -c "SELECT 1"
```

### Issue: "Airflow DAG not showing"

```bash
# Check DAG parsing
docker-compose exec airflow airflow list_dags

# Force DAG refresh
docker-compose restart airflow airflow-scheduler

# Check for syntax errors
python -m py_compile etl_dag_production.py
```

### Issue: "No data in dashboards"

```bash
# Verify data loaded to database
docker-compose exec postgres psql -U postgres -d unilever_warehouse -c "SELECT COUNT(*) FROM fact_sales"

# Check datasource in Grafana
# Settings → Data Sources → PostgreSQL → Test

# Check dashboard queries in browser console
```

### Issue: "Out of memory"

```bash
# Increase batch size
export BATCH_SIZE=5000

# Reduce parallel processes
export AIRFLOW__CORE__PARALLELISM=2
```

---

## 📞 Support & Contacts

- **Data Engineering Team:** data-eng@unilever.com
- **On-Call:** #data-engineering Slack
- **Documentation:** https://wiki.unilever.com/etl
- **Status Page:** https://status.unilever.com

---

## 📄 Additional Resources

- [API Documentation](docs/API.md)
- [Architecture Diagram](docs/ARCHITECTURE.md)
- [Schema Documentation](docs/SCHEMA.md)
- [Performance Tuning](docs/PERFORMANCE.md)
- [SLA Requirements](docs/SLA.md)

---

**Last Updated:** 2026-02-19  
**Version:** 1.0.0  
**Status:** ✅ Production Ready
