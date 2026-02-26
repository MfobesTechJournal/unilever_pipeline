# Data Warehouse Schema Documentation

## Overview

Star schema design for Unilever ETL Pipeline with 4 dimensions and 1 fact table. Implements SCD Type 2 for slowly changing dimensions (customer tracking).

## Fact Table

### fact_sales
**Purpose:** Central fact table containing all sales transactions

**Grain:** One row per sales transaction

| Column | Type | Description |
|--------|------|-------------|
| sales_id | BIGSERIAL | Primary key, unique transaction ID |
| date_id | INTEGER | FK to dim_date |
| product_id | INTEGER | FK to dim_product |
| customer_id | INTEGER | FK to dim_customer |
| location_id | INTEGER | FK to dim_location |
| quantity | INTEGER | Number of items sold |
| unit_price | DECIMAL(10,2) | Price per unit |
| extended_amount | DECIMAL(12,2) | quantity × unit_price |
| discount_amount | DECIMAL(12,2) | Applied discount |
| net_amount | DECIMAL(12,2) | extended_amount - discount |
| tax_amount | DECIMAL(12,2) | Sales tax |
| total_amount | DECIMAL(12,2) | Final amount paid |
| cost_amount | DECIMAL(12,2) | Cost of goods sold |
| profit_amount | DECIMAL(12,2) | Revenue - Cost |
| order_status | VARCHAR(50) | completed, pending, cancelled |
| payment_method | VARCHAR(50) | cash, credit, debit, online |
| shipping_method | VARCHAR(50) | standard, express, overnight |
| created_at | TIMESTAMP | When record was loaded |

**Partitioning:** By date_id (yearly partitions for performance)

---

## Dimension Tables

### dim_date
**Purpose:** Time dimension with calendar hierarchy

| Column | Type | Description |
|--------|------|-------------|
| date_id | SERIAL | Primary key |
| date_value | DATE | Actual calendar date |
| year | INTEGER | 2024, 2025, 2026... |
| quarter | INTEGER | 1-4 |
| month | INTEGER | 1-12 |
| day | INTEGER | 1-31 |
| day_of_week | VARCHAR(10) | Monday, Tuesday... |
| week_of_year | INTEGER | 1-52 |
| is_weekend | BOOLEAN | TRUE for Sat/Sun |
| is_holiday | BOOLEAN | TRUE for holidays |

**Type:** Conformed dimension

---

### dim_product
**Purpose:** Product catalog (SCD Type 1 - Latest values only)

| Column | Type | Description |
|--------|------|-------------|
| product_id | SERIAL | Primary key (surrogate) |
| product_name | VARCHAR(255) | Product name |
| category | VARCHAR(100) | Main category |
| subcategory | VARCHAR(100) | Sub-category |
| price | DECIMAL(10,2) | Current selling price |
| cost | DECIMAL(10,2) | Cost to company |
| supplier | VARCHAR(100) | Supplier name |
| is_active | BOOLEAN | Currently sold? |
| effective_from | DATE | When valid from |
| effective_to | DATE | When valid to |
| is_current | BOOLEAN | Current version? |
| created_at | TIMESTAMP | When created |
| updated_at | TIMESTAMP | Last updated |

**Type:** Slowly Changing Dimension Type 1

---

### dim_customer
**Purpose:** Customer master (SCD Type 2 - Track history)

| Column | Type | Description |
|--------|------|-------------|
| customer_id | SERIAL | Primary key (surrogate) |
| customer_code | VARCHAR(20) | Natural key |
| first_name | VARCHAR(100) | First name |
| last_name | VARCHAR(100) | Last name |
| email | VARCHAR(100) | Email address |
| phone | VARCHAR(20) | Phone number |
| city | VARCHAR(100) | City |
| state | VARCHAR(50) | State/Province |
| country | VARCHAR(100) | Country |
| postal_code | VARCHAR(20) | Postal code |
| customer_segment | VARCHAR(50) | VIP, regular, inactive |
| lifetime_value | DECIMAL(12,2) | Total customer value |
| effective_from | DATE | When record became valid |
| effective_to | DATE | When record expired |
| is_current | BOOLEAN | Current record? |
| created_at | TIMESTAMP | When created |
| updated_at | TIMESTAMP | Last updated |

**Type:** Slowly Changing Dimension Type 2 (tracks address/segment changes)

**Example History:**
- Customer John Doe, City=NY, effective_from=2024-01-01, effective_to=2024-06-30, is_current=FALSE
- Customer John Doe, City=CA, effective_from=2024-07-01, effective_to=NULL, is_current=TRUE

---

### dim_location
**Purpose:** Geographic location dimension

| Column | Type | Description |
|--------|------|-------------|
| location_id | SERIAL | Primary key |
| location_name | VARCHAR(255) | Store/warehouse name |
| city | VARCHAR(100) | City |
| state | VARCHAR(50) | State/Province |
| country | VARCHAR(100) | Country |
| region | VARCHAR(100) | World region |
| postal_code | VARCHAR(20) | Postal code |
| latitude | DECIMAL(9,6) | Geographic latitude |
| longitude | DECIMAL(9,6) | Geographic longitude |

**Type:** Conformed dimension

---

## Metadata Tables

### etl_log
**Purpose:** Track all ETL pipeline executions

| Column | Type | Description |
|--------|------|-------------|
| run_id | SERIAL | Primary key |
| pipeline_name | VARCHAR(100) | Name of pipeline ("daily_etl", "incremental_load") |
| run_status | VARCHAR(20) | success, failed, running |
| start_time | TIMESTAMP | When pipeline started |
| end_time | TIMESTAMP | When pipeline ended |
| duration_seconds | DECIMAL(10,2) | Total runtime |
| records_extracted | BIGINT | Rows read from source |
| records_transformed | BIGINT | Rows after transformation |
| records_loaded | BIGINT | Rows inserted to warehouse |
| error_message | TEXT | Error summary |
| error_details | TEXT | Full stack trace |
| created_at | TIMESTAMP | When logged |

### data_quality_log
**Purpose:** Track data quality check results

| Column | Type | Description |
|--------|------|-------------|
| quality_id | SERIAL | Primary key |
| run_id | INTEGER | FK to etl_log |
| table_name | VARCHAR(100) | Table checked |
| check_type | VARCHAR(100) | duplicate_check, null_check, outlier_check |
| check_description | VARCHAR(255) | Details of check |
| severity | VARCHAR(20) | info, warning, error |
| record_count | BIGINT | Total records checked |
| issue_count | BIGINT | Records with issues |
| quality_score | DECIMAL(5,2) | 0-100 score |
| details | JSON | Additional metadata |
| created_at | TIMESTAMP | When checked |

---

## Data Model Diagram

```
                    dim_date
                      |
                      |
dim_product -------- fact_sales -------- dim_customer
                      |
                      |
                  dim_location
```

---

## Slowly Changing Dimensions (SCD) Strategy

### SCD Type 1 (dim_product)
- **When:** Product prices change, status changes
- **How:** Update existing row (no history kept)
- **Use Case:** Current state matters, history not needed

### SCD Type 2 (dim_customer)
- **When:** Customer address, segment changes
- **How:** Create new row, mark old as inactive
- **Use Case:** Analyze sales by customer's address at time of sale

---

## Loading Strategy

1. **Extract:** Read from raw CSV/JSON files
2. **Transform:** Data cleaning, deduplication
3. **Load:**
   - Update dimensions (insert new, update if SCD)
   - Bulk insert facts (using date_id FK)
   - Update metadata tables (etl_log, data_quality_log)

---

## Performance Considerations

- **Fact table partitioned** by date_id (yearly)
- **Indices on FKs** (date_id, product_id, customer_id)
- **Indices on common queries** (status, date, city)
- **Surrogate keys** for dimension tables
- **SERIAL sequences** for auto-increment IDs

---

**Last Updated:** February 26, 2026  
**Owner:** Data Engineering Team
