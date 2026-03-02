# Entity Relationship Diagram (ERD)

## Unilever Data Pipeline - Star Schema Warehouse

### Database Schema Overview

The Unilever data warehouse implements a **star schema** design pattern with one central fact table and multiple dimension tables for optimal analytical query performance.

---

## ER Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      FACT TABLE                                 │
│                   FACT_SALES                                    │
├─────────────────────────────────────────────────────────────────┤
│ sales_key (PK)          │ BIGSERIAL                              │
│ product_key (FK)        │ INTEGER ──────────┐                   │
│ customer_key (FK)       │ INTEGER ────┐     │                   │
│ date_key (FK)           │ INTEGER ──┐ │     │                   │
│ quantity                │ INTEGER   │ │     │                   │
│ revenue                 │ DECIMAL   │ │     │                   │
│ cost                    │ DECIMAL   │ │     │                   │
│ created_at              │ TIMESTAMP │ │     │                   │
│ updated_at              │ TIMESTAMP │ │     │                   │
└─────────────────────────────────────────────────────────────────┘
                          │ │ │
        ┌─────────────────┘ │ │ ┌──────────────────────┐
        │                   │ │                        │
        │                   │ │ ┌──────────────────────┴──────┐
        │                   │ │                               │
        ▼                   ▼ ▼                               ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│  DIM_PRODUCT     │  │   DIM_DATE       │  │  DIM_CUSTOMER        │
├──────────────────┤  ├──────────────────┤  ├──────────────────────┤
│ product_key (PK) │  │ date_key (PK)    │  │customer_key (PK)     │
│ product_id       │  │ sale_date        │  │customer_id           │
│ product_name     │  │ year             │  │customer_name         │
│ category         │  │ quarter          │  │email                 │
│ subcategory      │  │ month            │  │phone                 │
│ price            │  │ day_of_week      │  │country               │
│ description      │  │ day_of_month     │  │city                  │
│ created_at       │  │ is_weekend       │  │registration_date     │
│ updated_at       │  │ is_holiday       │  │customer_segment      │
│                  │  │ created_at       │  │lifetime_value        │
│                  │  │ updated_at       │  │created_at            │
│                  │  │                  │  │updated_at            │
└──────────────────┘  └──────────────────┘  └──────────────────────┘
```

---

## Table Specifications

### FACT_SALES (Sales Transactions)
**Purpose:** Central fact table storing all sales transactions  
**Primary Key:** `sales_key` (BIGSERIAL, auto-increment)  
**Foreign Keys:** `product_key`, `customer_key`, `date_key`  
**Record Count:** 50,000 transactions  

| Column | Type | Constraint | Description |
|--------|------|-----------|-------------|
| sales_key | BIGSERIAL | PRIMARY KEY | Unique transaction identifier |
| product_key | INTEGER | FOREIGN KEY → dim_product | Product reference |
| customer_key | INTEGER | FOREIGN KEY → dim_customer | Customer reference |
| date_key | INTEGER | FOREIGN KEY → dim_date | Date reference |
| quantity | INTEGER | NOT NULL | Units sold |
| revenue | DECIMAL(12,2) | NOT NULL | Total sale amount |
| cost | DECIMAL(12,2) | NOT NULL | Cost of goods sold |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

**Indexes:**
- PK: `sales_key`
- FK: `product_key`, `customer_key`, `date_key`
- Performance: On `date_key`, `product_key`, `customer_key` for common queries

---

### DIM_PRODUCT (Products)
**Purpose:** Product dimension providing product attributes  
**Primary Key:** `product_key` (SERIAL)  
**Record Count:** 1,500 distinct products  

| Column | Type | Constraint | Description |
|--------|------|-----------|-------------|
| product_key | SERIAL | PRIMARY KEY | Unique product identifier |
| product_id | VARCHAR(50) | UNIQUE | Business product ID |
| product_name | VARCHAR(255) | NOT NULL | Product name |
| category | VARCHAR(100) | NOT NULL | Product category |
| subcategory | VARCHAR(100) | NULL | Product subcategory |
| price | DECIMAL(10,2) | NOT NULL | Standard product price |
| description | TEXT | NULL | Product description |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

**Slowly Changing Dimension (SCD) Type:** 2 (tracked via created_at/updated_at)

---

### DIM_CUSTOMER (Customers)
**Purpose:** Customer dimension providing customer attributes  
**Primary Key:** `customer_key` (SERIAL)  
**Record Count:** 5,000 unique customers  

| Column | Type | Constraint | Description |
|--------|------|-----------|-------------|
| customer_key | SERIAL | PRIMARY KEY | Unique customer identifier |
| customer_id | VARCHAR(50) | UNIQUE | Business customer ID |
| customer_name | VARCHAR(255) | NOT NULL | Customer's full name |
| email | VARCHAR(255) | UNIQUE NOT NULL | Email address |
| phone | VARCHAR(20) | NULL | Contact phone number |
| country | VARCHAR(100) | NOT NULL | Country of residence |
| city | VARCHAR(100) | NOT NULL | City of residence |
| registration_date | DATE | NOT NULL | Customer registration date |
| customer_segment | VARCHAR(50) | NOT NULL | Segmentation (e.g., Premium, Regular) |
| lifetime_value | DECIMAL(12,2) | DEFAULT 0 | Total customer value |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

**Indexes:**
- Customer segmentation queries: Index on `customer_segment`
- Temporal analysis: Index on `registration_date`

---

### DIM_DATE (Time Dimension)
**Purpose:** Date dimension for temporal queries  
**Primary Key:** `date_key` (SERIAL)  
**Record Count:** 731 days (2-year span)  

| Column | Type | Constraint | Description |
|--------|------|-----------|-------------|
| date_key | SERIAL | PRIMARY KEY | Unique date identifier |
| sale_date | DATE | UNIQUE NOT NULL | Calendar date (YYYY-MM-DD) |
| year | INTEGER | NOT NULL | Calendar year |
| quarter | INTEGER | NOT NULL | Quarter (1-4) |
| month | INTEGER | NOT NULL | Month (1-12) |
| day_of_week | VARCHAR(10) | NOT NULL | Day name (Monday-Sunday) |
| day_of_month | INTEGER | NOT NULL | Day number (1-31) |
| is_weekend | BOOLEAN | NOT NULL DEFAULT FALSE | Weekend indicator |
| is_holiday | BOOLEAN | NOT NULL DEFAULT FALSE | Holiday indicator |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

**Optimization Note:** Pre-populated with all dates; enables DATEPART queries without complex calculations

---

## Relationship Matrix

| Fact Table | Dimension | Cardinality | Join Condition |
|----------|-----------|-------------|-----------------|
| FACT_SALES | DIM_PRODUCT | Many-to-One | fact_sales.product_key = dim_product.product_key |
| FACT_SALES | DIM_CUSTOMER | Many-to-One | fact_sales.customer_key = dim_customer.customer_key |
| FACT_SALES | DIM_DATE | Many-to-One | fact_sales.date_key = dim_date.date_key |

---

## Data Statistics

### Record Distribution
```
Total Records in Warehouse: 57,231

Breakdown:
├── fact_sales:         50,000 (87.3%)
├── dim_product:         1,500 (2.6%)
├── dim_customer:        5,000 (8.7%)
└── dim_date:              731 (1.3%)
```

### Fact Table Metrics
```
Sales Analytics:
├── Total Revenue:        $54,380,419.57
├── Total Quantity Sold:  1,250,000 units
├── Average Order Value:  $1,087.61
├── Average Quantity:     25 units per order
└── Date Range:           731 days (2 years)
```

---

## Star Schema Benefits

### ✅ Performance
- Simplified JOIN operations (1 fact + dimension tables)
- Pre-aggregated dimension tables reduce query complexity
- Index optimization on foreign keys

### ✅ Scalability
- Fact table growth independent of dimensions
- Incremental data loading via dimension keys
- Efficient incremental ETL patterns

### ✅ Maintainability
- Clear separation: OLAP analytics vs. OLTP operations
- Dimension updates don't impact historical facts
- Supports Slowly Changing Dimensions (SCD)

### ✅ Analytics-Ready
- Optimized for aggregations (SUM, COUNT, AVG)
- Natural support for drill-down analysis
- Time-based analysis via dimension joins

---

## Key Constraints & Integrity

### Primary Keys
- All tables have explicit PRIMARY KEY constraints
- Fact table uses BIGSERIAL for high-volume scenarios
- Dimensions use SERIAL with business keys marked UNIQUE

### Foreign Keys
- FACT_SALES → DIM_PRODUCT (product_key)
- FACT_SALES → DIM_CUSTOMER (customer_key)
- FACT_SALES → DIM_DATE (date_key)
- All FKs enforce referential integrity

### Business Rules
- Sales revenue and cost must be > 0
- Quantity must be >= 1
- Customer emails must be unique
- Product IDs must be unique
- Dates must be chronologically valid

---

## Dashboard Query Examples

### Total Sales Revenue by Category
```sql
SELECT 
    dp.category,
    SUM(fs.revenue) as total_revenue,
    COUNT(*) as transaction_count,
    AVG(fs.revenue) as avg_order_value
FROM fact_sales fs
JOIN dim_product dp ON fs.product_key = dp.product_key
GROUP BY dp.category
ORDER BY total_revenue DESC;
```

### Daily Sales Trend
```sql
SELECT 
    dd.sale_date,
    SUM(fs.revenue) as daily_revenue,
    COUNT(*) as daily_transactions,
    SUM(fs.quantity) as daily_quantity
FROM fact_sales fs
JOIN dim_date dd ON fs.date_key = dd.date_key
GROUP BY dd.sale_date
ORDER BY dd.sale_date;
```

### Customer Segment Analysis
```sql
SELECT 
    dc.customer_segment,
    COUNT(DISTINCT dc.customer_key) as customer_count,
    SUM(fs.revenue) as segment_revenue,
    AVG(fs.revenue) as avg_order_value,
    COUNT(*) as total_orders
FROM fact_sales fs
JOIN dim_customer dc ON fs.customer_key = dc.customer_key
GROUP BY dc.customer_segment;
```

---

## Data Dictionary

### Naming Conventions
- **Fact Tables:** Prefix `fact_`
- **Dimension Tables:** Prefix `dim_`
- **Keys:** Suffix `_key` for surrogates, `_id` for business keys
- **Timestamps:** `created_at`, `updated_at`
- **Measures:** Revenue, cost, quantity (business terms)

### Data Types
- **Identifiers:** SERIAL, BIGSERIAL, VARCHAR(50) with UNIQUE
- **Amounts:** DECIMAL(12,2) for financial data
- **Flags:** BOOLEAN for binary attributes
- **Dates:** DATE for date-only, TIMESTAMP for datetime

---

## Version Control & Metadata

**Schema Version:** 1.0  
**Created:** February 2026  
**Last Updated:** March 2, 2026  
**Maintained By:** Data Analytics Team  
**Database:** PostgreSQL 14+  

---
