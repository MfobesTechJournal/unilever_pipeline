"""
PHASE 10: Documentation
Architecture and Design Guide
"""

# Unilever ETL Pipeline - Architecture Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Sources                              │
│   (CSV, JSON, Excel, APIs, Databases)                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Ingestion Layer (Phase 3)                       │
│   • File monitoring (monitor_new_files.sh)                   │
│   • Format validation (validate_csv_format.sh)               │
│   • Staging area (raw_data → staging)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│            ETL Pipeline (Phase 4)                            │
│   ┌──────────────────────────────────────────────────────┐   │
│   │ Extract         → CSV/JSON/Excel Extractors          │   │
│   ├──────────────────────────────────────────────────────┤   │
│   │ Transform       → Data Cleaner, Validator, Transformer
│   ├──────────────────────────────────────────────────────┤   │
│   │ Load            → Fact & Dimension Loaders (SCD)     │   │
│   └──────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│          Orchestration (Phase 5 & Apache Airflow)            │
│   • daily_etl_dag.py: Full daily load                        │
│   • incremental_etl_dag.py: Hourly incremental               │
│   • data_quality_dag.py: Quality validation                  │
│   • maintenance_dag.py: Weekly cleanup                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│          Data Warehouse (Phase 1 - PostgreSQL)               │
│   ┌──────────────────────────────────────────────────────┐   │
│   │ Fact Table                                            │   │
│   │ • fact_sales (55K records/day)                       │   │
│   ├──────────────────────────────────────────────────────┤   │
│   │ Dimension Tables (with SCD Type 2)                   │   │
│   │ • dim_date (calendar hierarchy)                      │   │
│   │ • dim_product (500+ products)                        │   │
│   │ • dim_customer (1000+ customers, history tracked)    │   │
│   │ • dim_location (100+ stores)                         │   │
│   ├──────────────────────────────────────────────────────┤   │
│   │ Metadata Tables                                       │   │
│   │ • etl_log (pipeline execution history)               │   │
│   │ • data_quality_log (quality metrics)                 │   │
│   └──────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌────────────────┐
│ Monitoring  │ │  Backups    │ │ Optimization   │
│ (Phase 8)   │ │ (Phase 7)   │ │ (Phase 7)      │
│             │ │             │ │                │
│ Prometheus  │ │ pg_dump     │ │ Indices        │
│ Grafana     │ │ AWS S3      │ │ Partitioning   │
│ Alerts      │ │ PITR        │ │ VACUUM ANALYZE │
└─────────────┘ └─────────────┘ └────────────────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
                      ▼
        ┌─────────────────────────────────┐
        │  Analytics & Reporting Ready     │
        │  (BI Tools, Power BI, Tableau)   │
        └─────────────────────────────────┘
```

## Data Model (Star Schema)

### Fact Table: fact_sales
```
Columns:
- sale_id (INT, PRIMARY KEY)
- date_id (INT, FOREIGN KEY → dim_date)
- product_id (INT, FOREIGN KEY → dim_product)
- customer_id (INT, FOREIGN KEY → dim_customer)
- location_id (INT, FOREIGN KEY → dim_location)
- quantity (INT)
- unit_price (DECIMAL)
- discount_percent (DECIMAL)
- sale_amount (DECIMAL)
- created_timestamp (TIMESTAMP)

Indexes:
- PRIMARY KEY on sale_id
- COMPOSITE on (date_id, product_id)
- COMPOSITE on (customer_id, date_id)
- ON location_id

Partitioning: By date_id (monthly)
```

### Dimension Tables
```
dim_date:
- date_id, full_date, year, quarter, month, week, day
- holiday_flag, weekend_flag

dim_product:
- product_id, product_name, category, brand
- unit_price, unit_cost, supplier_id

dim_customer (SCD Type 2):
- customer_id, first_name, last_name, email
- phone, country, city, customer_segment
- lifetime_value
- is_current, start_date, end_date

dim_location:
- location_id, store_name, store_type
- country, state, city, address
- manager_name, store_size_sqft, employees_count
```

### Metadata Tables
```
etl_log:
- execution_id, pipeline_name, execution_status
- records_processed, duration_seconds, execution_timestamp

data_quality_log:
- check_id, table_name, metric_name
- metric_value, check_timestamp
```

## ETL Pipeline Flow

### Daily Full Load (2:00 AM UTC)
```
1. Check for new files (monitor_new_files.sh)
2. Validate file format (validate_csv_format.sh)
3. Extract data (generate_sales_data.py → fact_sales)
4. Extract dimensions (if present)
5. Transform:
   - Clean nulls/duplicates
   - Standardize types and text
   - Remove outliers
6. Load:
   - Dimension tables (with SCD Type 2)
   - Fact table (upsert on keys)
   - Quality metrics (etl_log)
7. Validate:
   - Check referential integrity
   - Verify data completeness
   - Log quality scores
8. Notify:
   - Success email
   - Teams notification
   - Log execution details
```

### Incremental Load (Every 6 hours)
```
1. Query etl_log for last execution time
2. Extract only changed records since last run
3. Transform incremental data
4. Upsert into fact/dimension tables
5. Log metrics
```

### Weekly Maintenance
```
1. VACUUM ANALYZE (optimize table statistics)
2. Backup database to S3
3. Archive old files (30+ days)
4. Cleanup old logs
5. Update partition scheme
```

## Deployment Architecture

### Local Development
- Docker Compose with 5 services
- PostgreSQL 13, Airflow 2.0, Grafana, Prometheus
- Hot reload for code changes

### Cloud (AWS)
- EC2 t3.medium for Airflow/ETL
- RDS PostgreSQL Multi-AZ
- S3 for backups
- CloudWatch for logs
- Estimated cost: $25-30/month

### Kubernetes (Optional)
- Deployments for ETL pipeline (2 replicas)
- StatefulSet for PostgreSQL
- CronJob for daily ETL
- Persistent volumes for logs/data
- Load balancer for access

## Security & Compliance

- All credentials in environment variables
- No hardcoded secrets
- SSL for database connections
- AWS S3 encryption for backups
- RDS backup retention: 30 days
- Audit logging in etl_log table
- RBAC for Kubernetes (optional)

## Monitoring & Alerting

### Metrics Tracked
- ETL execution time
- Record counts (extracted, transformed, loaded)
- Data quality scores
- Pipeline success/failure rates
- Database size and growth
- Query performance

### Alerts Triggered
- Pipeline failures
- Quality score drops
- Disk space warnings
- Performance degradation
- Database connection failures

### Dashboards
- Pipeline overview (24h view)
- Data quality metrics
- Performance trends
- Error tracking

## Scalability

Current: 55,550 records/day → 45 seconds load time

To scale to 1M+ records:
1. Increase batch sizes in bulk loading
2. Implement parallel extraction
3. Use connection pooling
4. Partition fact table by (date, location)
5. Add read replicas for reporting
6. Consider Kafka for streaming

---

See IMPLEMENTATION_SUMMARY.md for current status
