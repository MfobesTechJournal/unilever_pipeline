#!/usr/bin/env python3
"""
ETL Log Loader - matches exact schema
etl_log: run_id, start_time, end_time, status, records_products,
         records_customers, records_dates, records_facts,
         records_quality_issues, error_message

data_quality_log: log_id, run_id, table_name, check_type,
                  issue_count, issue_description, timestamp
"""

import psycopg2
import psycopg2.extras
import random
from datetime import datetime, timedelta

random.seed(99)

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "unilever_warehouse",
    "user": "postgres",
    "password": "123456"
}

ERROR_MESSAGES = [
    "Connection timeout to source database",
    "Data validation failed: null values in required fields",
    "Transform error: unexpected schema change in source",
    "Duplicate key violation on fact_sales",
    "Source file not found for extraction",
    "Memory limit exceeded during transformation",
]

QUALITY_CHECKS = [
    ("dim_customer",  "completeness",  "Null customer_id values detected"),
    ("dim_product",   "completeness",  "Null product_id values detected"),
    ("fact_sales",    "validity",      "Negative revenue values found"),
    ("fact_sales",    "uniqueness",    "Duplicate sale_id records detected"),
    ("fact_sales",    "integrity",     "Orphaned product_key references"),
    ("fact_sales",    "integrity",     "Orphaned customer_key references"),
    ("fact_sales",    "validity",      "Sale dates outside expected range"),
    ("fact_sales",    "validity",      "Quantity values out of valid range"),
]


def load():
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        # Clear both tables separately to avoid rollback issues
        print("Clearing data_quality_log...")
        cur.execute("DELETE FROM data_quality_log")
        conn.commit()

        print("Clearing etl_log...")
        cur.execute("DELETE FROM etl_log")
        conn.commit()

        # Reset sequences
        cur.execute("ALTER SEQUENCE etl_log_run_id_seq RESTART WITH 1")
        conn.commit()

        # ── 1. Load etl_log ──
        start_dt = datetime(2024, 1, 1)
        end_dt   = datetime(2025, 12, 31)
        print(f"Generating ETL logs {start_dt.date()} to {end_dt.date()}...")

        etl_rows = []
        current = start_dt
        while current <= end_dt:
            run_start = current.replace(hour=2, minute=0, second=0, microsecond=0)
            success   = random.random() > 0.05
            duration  = random.randint(180, 480) if success else random.randint(20, 120)
            run_end   = run_start + timedelta(seconds=duration)

            if success:
                etl_rows.append((
                    run_start, run_end, "success",
                    random.randint(20, 30),     # records_products
                    random.randint(450, 600),   # records_customers
                    365,                        # records_dates
                    random.randint(800, 3500),  # records_facts
                    random.randint(0, 3),       # records_quality_issues
                    None
                ))
            else:
                etl_rows.append((
                    run_start, run_end, "failed",
                    0, 0, 0, 0, 0,
                    random.choice(ERROR_MESSAGES)
                ))
            current += timedelta(days=1)

        psycopg2.extras.execute_batch(cur, """
            INSERT INTO etl_log
                (start_time, end_time, status,
                 records_products, records_customers, records_dates,
                 records_facts, records_quality_issues, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, etl_rows, page_size=200)
        conn.commit()
        print(f"  Loaded {len(etl_rows)} ETL run logs")

        # ── 2. Fetch run_ids ──
        cur.execute("SELECT run_id, start_time FROM etl_log ORDER BY run_id")
        runs = cur.fetchall()

        # ── 3. Load data_quality_log ──
        print("Generating data quality logs...")
        dq_rows = []
        for run_id, run_time in runs:
            for table_name, check_type, issue_desc in QUALITY_CHECKS:
                has_issue = random.random() < 0.04  # 4% chance of issue
                issue_count = random.randint(1, 50) if has_issue else 0
                dq_rows.append((
                    run_id,
                    table_name,
                    check_type,
                    issue_count,
                    issue_desc if has_issue else None,
                    run_time
                ))

        psycopg2.extras.execute_batch(cur, """
            INSERT INTO data_quality_log
                (run_id, table_name, check_type,
                 issue_count, issue_description, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, dq_rows, page_size=500)
        conn.commit()
        print(f"  Loaded {len(dq_rows)} data quality log entries")

        # ── Verification ──
        print("\n=== VERIFICATION ===")
        cur.execute("SELECT COUNT(*) FROM etl_log")
        print(f"  etl_log:          {cur.fetchone()[0]:,} rows")
        cur.execute("SELECT COUNT(*) FROM data_quality_log")
        print(f"  data_quality_log: {cur.fetchone()[0]:,} rows")
        cur.execute("SELECT status, COUNT(*) FROM etl_log GROUP BY status ORDER BY status")
        for row in cur.fetchall():
            print(f"  ETL '{row[0]}': {row[1]} runs")
        cur.execute("SELECT ROUND(AVG(records_facts)) FROM etl_log WHERE status='success'")
        print(f"  Avg records/run:  {cur.fetchone()[0]:,}")
        cur.execute("SELECT COUNT(*) FROM data_quality_log WHERE issue_count > 0")
        print(f"  Quality issues found: {cur.fetchone()[0]:,}")

        print("\nAll logs loaded successfully!")

    except Exception as e:
        conn.rollback()
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    load()
