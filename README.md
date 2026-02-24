# Unilever Data Warehouse Pipeline

A comprehensive ETL pipeline for the Unilever data warehouse project. This is a production-ready data engineering portfolio project demonstrating end-to-end data warehouse implementation.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        UNILEVER DATA WAREHOUSE PIPELINE                     │
└─────────────────────────────────────────────────────────────────────────────┘

                           DATA FLOW DIAGRAM
                           =================

┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   SOURCE     │     │   STAGING    │     │   ETL        │     │   WAREHOUSE  │
│   SYSTEMS    │────▶│   AREA       │────▶│   PIPELINE   │────▶│   (PostgreSQL)│
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │                    │
       ▼                    ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ CSV Files    │     │ CSV Files    │     │ Python       │     │ Star Schema  │
│ JSON Files   │     │ (Products,   │     │ Scripts      │     │ Fact Table   │
│ Excel Files  │     │  Customers,  │     │ Airflow DAG │     │ Dimension    │
│ Database     │     │  Sales)      │     │ Shell Scripts│     │ Tables       │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                 │
                                                                 ▼
                                              ┌──────────────────────────────┐
                                              │   CONTROL & METADATA         │
                                              │  - load_batch (folders)      │
                                              │  - etl_log (runs)            │
                                              │  - data_quality_log          │
                                              └──────────────────────────────┘


                           STAR SCHEMA DESIGN
                           =================

                           ┌─────────────┐
                           │  dim_date   │
                           │─────────────│
                           │ date_key PK │
                           │ sale_date   │
                           │ year        │
                           │ month       │
                           │ day         │
                           │ quarter     │
                           │ month_name  │
                           │ day_of_week │
                           └──────┬──────┘
                                  │
                                  │ date_key
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│ dim_product   │          │  fact_sales   │          │ dim_customer  │
│───────────────│          │───────────────│          │───────────────│
│ product_key PK◀──────────│ product_key FK │          │ customer_key PK│
│ product_id    │          │ customer_key FK│─────────▶│ customer_id   │
│ product_name  │          │ date_key FK    │          │ customer_name │
│ category      │          │ quantity       │          │ email         │
│ brand         │          │ revenue        │          │ city          │
│               │          │ sale_id (UNIQUE)         │ province      │
└───────────────┘          └───────────────────┘          └───────────────┘


                           ETL PIPELINE FLOW
                           ================

┌─────────────────────────────────────────────────────────────────────────────┐
│                           ETL PROCESS FLOW                                  │
└─────────────────────────────────────────────────────────────────────────────┘

1. EXTRACT
   ├── Detect latest raw data folder (raw_data/YYYY-MM-DD/)
   ├── Copy files to staging area
   ├── Load CSV files into pandas DataFrames
   └── Validate data formats

2. TRANSFORM
   ├── Data Quality Checks
   │   ├── Check for null values
   │   ├── Check for duplicates
   │   ├── Check for outliers
   │   └── Check for negative values
   │
   ├── Dimension Processing
   │   ├── Deduplicate products
   │   ├── Deduplicate customers
   │   ├── Deduplicate dates
   │   └── SCD Type 2 (historical tracking)
   │
   └── Fact Processing
       ├── Create staging_sales table
       ├── Join with dimensions (surrogate keys)
       └── Insert with ON CONFLICT handling

3. LOAD
   ├── Insert new dimension records
   ├── Insert fact records (idempotent)
   ├── Update metadata tables
   │   ├── load_batch (folder tracking)
   │   ├── etl_log (run tracking)
   │   └── data_quality_log (quality issues)
   │
   └── Archive processed raw data


                           TECHNICAL STACK
                           ==============

┌─────────────────────────────────────────────────────────────────────────────┐
│                           TECHNOLOGY STACK                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   DATA          │    │   ORCHESTRATION │    │   MONITORING   │
│   PROCESSING    │    │                 │    │                 │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ Python 3.8+    │    │ Apache Airflow  │    │ Prometheus      │
│ Pandas          │    │ Cron Jobs       │    │ Grafana        │
│ SQLAlchemy      │    │ Shell Scripts   │    │ Custom Scripts  │
│ PostgreSQL      │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘

         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   DATA          │    │   DEPLOYMENT   │    │   DOCUMENTATION│
│   GENERATION    │    │                 │    │                 │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ Faker Library   │    │ Docker          │    │ README          │
│ CSV/JSON/Excel  │    │ Docker Compose │    │ Architecture    │
│ Data Quality    │    │ GitHub          │    │ Diagrams        │
│ Issues          │    │                 │    │ Runbooks        │
└─────────────────┘    └─────────────────┘    └─────────────────┘


                           PROJECT STRUCTURE
                           ================

unilever_pipeline/
│
├── 📁 DATABASE SCHEMA
│   ├── setup_warehouse.sql       # Star schema definition
│   └── setup_partitions.sql     # Table partitioning
│
├── 📁 DATA GENERATION
│   └── generate_data.py          # Sample data with quality issues
│
├── 📁 ETL PIPELINE
│   ├── etl_load_staging.py       # Main ETL script (SCD Type 2)
│   └── run_pipeline.py           # Legacy pipeline runner
│
├── 📁 ORCHESTRATION
│   ├── ingest_data.sh            # Shell ingestion script
│   ├── etl_dag.py               # Airflow DAG
│   └── cron_setup.sh            # Cron job configuration
│
├── 📁 MONITORING
│   ├── monitor_etl.py            # Pipeline monitoring
│   ├── db_optimize.py           # Database optimization
│   └── alerts/                   # Alert configurations
│
├── 📁 INFRASTRUCTURE
│   ├── docker-compose.yml        # Docker Compose stack
│   ├── .env.example             # Environment variables
│   └── requirements.txt          # Python dependencies
│
├── 📁 DOCUMENTATION
│   ├── README.md                 # This file
│   ├── ARCHITECTURE.md          # Architecture details
│   └── OPERATIONS.md            # Operations runbook
│
└── 📁 DATA
    ├── raw_data/                 # Raw data (daily folders)
    ├── staging/                  # Staging area
    └── archive/                  # Archived data


                           QUICK START
                           ==========

Prerequisites:
- Python 3.8+
- PostgreSQL 14+
- Docker & Docker Compose (optional)

1. Clone the repository:
   git clone https://github.com/yourusername/unilever_pipeline.git
   cd unilever_pipeline

2. Set up environment:
   cp .env.example .env
   # Edit .env with your settings

3. Create virtual environment:
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows

4. Install dependencies:
   pip install -r requirements.txt

5. Set up database:
   psql -U postgres -p 5433 -d unilever_warehouse -f setup_warehouse.sql

6. Generate sample data:
   python generate_data.py

7. Run ETL pipeline:
   python etl_load_staging.py

8. Or use Docker:
   docker-compose up -d


                           USAGE EXAMPLES
                           =============

# Generate data with data quality issues
python generate_data.py

# Run ETL pipeline
python etl_load_staging.py

# Monitor pipeline
python monitor_etl.py

# Optimize database
python db_optimize.py

# Run shell ingestion with monitoring
./ingest_data.sh --run

# Setup daily cron job
./ingest_data.sh --setup-cron


                           FEATURES
                           ========

✅ Star Schema Design
  - Fact table: fact_sales
  - Dimensions: dim_product, dim_customer, dim_date
  - Surrogate keys and foreign keys

✅ Data Quality
  - Intentional data quality issues for testing
  - Null value detection
  - Duplicate detection
  - Outlier detection
  - Data quality logging

✅ ETL Pipeline
  - SCD Type 2 support for dimensions
  - Idempotent operations
  - Comprehensive logging
  - Error handling
  - Batch tracking

✅ Orchestration
  - Apache Airflow DAG
  - Shell scripting with cron
  - Automated file monitoring
  - Email/Slack notifications

✅ Monitoring & Logging
  - ETL run tracking
  - Data quality metrics
  - Performance monitoring
  - Alerting

✅ Database Administration
  - Table partitioning by date
  - Index optimization
  - Vacuum and analyze
  - Backup procedures

✅ Deployment
  - Docker Compose
  - Environment configuration
  - GitHub ready


                           MONITORING DASHBOARDS
                           =====================

┌─────────────────────────────────────────────────────────────────────────────┐
│                         ETL MONITORING DASHBOARD                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┬──────────────────┬──────────────────┬──────────────────┐
│  PIPELINE STATUS │  RECORDS LOADED  │  DATA QUALITY    │  PERFORMANCE     │
├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ ✅ Success: 45   │ Products: 12,500 │ Issues: 234      │ Avg: 45s         │
│ ❌ Failed: 3    │ Customers: 45,000 │ Nulls: 120       │ Min: 23s         │
│ ⏳ Running: 1    │ Dates: 730        │ Duplicates: 114  │ Max: 120s        │
│                  │ Sales: 650,000   │ Outliers: 50     │                  │
└──────────────────┴──────────────────┴──────────────────┴──────────────────┘


                           DATABASE SCHEMA
                           ==============

Dimension Tables:
- dim_product: Product information (surrogate key, natural key, attributes)
- dim_customer: Customer details (surrogate key, natural key, attributes)
- dim_date: Calendar hierarchy (date key, date, year, month, quarter, etc.)

Fact Tables:
- fact_sales: Sales transactions (sale_id, product_key, customer_key, date_key, quantity, revenue)

Control Tables:
- load_batch: Tracks processed folders (folder_name, status)
- etl_log: Pipeline execution logs (start_time, end_time, status, counts)
- data_quality_log: Quality issues (table_name, check_type, issue_count)


                           TROUBLESHOOTING
                           ==============

Common Issues:

1. Duplicate Key Error
   # Check existing runs
   SELECT * FROM etl_log ORDER BY start_time DESC LIMIT 5;
   
   # Check fact table
   SELECT COUNT(*) FROM fact_sales;

2. Missing Tables
   # Recreate schema
   psql -f setup_warehouse.sql

3. Data Quality Issues
   # Run monitoring
   python monitor_etl.py

4. Database Connection
   # Test connection
   psql -U postgres -p 5433 -d unilever_warehouse


                           CONTACT & LICENSE
                           =================

Author: [Your Name]
Email: contact@unilever-pipeline.com
License: MIT

For questions or contributions, please open an issue on GitHub.
