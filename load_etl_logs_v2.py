#!/usr/bin/env python3
"""
ETL Log Loader - matches exact unilever_warehouse schema
etl_log columns: run_id, start_time, end_time, status, records_products,
                 records_customers, records_dates, records_facts,
                 records_quality_issues, error_message
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


def generate_etl_logs(start_dt, end_dt):
    logs = []
    current = start_dt
    while current <= end_dt:
        run_start = current.replace(hour=2, minute=0, second=0, microsecond=0)
        success = random.random() > 0.05
        duration = random.randint(180, 480) if success else random.randint(20, 120)
        run_end = run_start + timedelta(seconds=duration)
        if success:
            logs.append((
                run_start, run_end, "success",
                random.randint(20, 30),
                random.randint(450, 600),
                365,
                random.randint(800, 3500),
                random.randint(0, 3),
                None
            ))
        else:
            logs.append((
                run_start, run_end, "failed",
                0, 0, 0, 0, 0,
                random.choice(ERROR_MESSAGES)
            ))
        current += timedelta(days=1)
    return logs


def load():
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        print("Clearing existing logs...")
        cur.execute("TRUNCATE data_quality_log RESTART IDENTITY CASCADE")
        cur.execute("TRUNCATE etl_log RESTART IDENTITY CASCADE")
        conn.commit()

        start_dt = datetime(2024, 1, 1)
        end_dt = datetime(2025, 12, 31)
        print(f"Generating ETL logs from {start_dt.date()} to {end_dt.date()}...")

        logs = generate_etl_logs(start_dt, end_dt)
        psycopg2.extras.execute_batch(cur, """
            INSERT INTO etl_log
                (start_time, end_time, status, records_products, records_customers,
                 records_dates, records_facts, records_quality_issues, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, logs, page_size=200)
        conn.commit()
        print(f"  Loaded {len(logs)} ETL run logs")

        # Fetch run_ids
        cur.execute("SELECT run_id, start_time FROM etl_log ORDER BY run_id")
        runs = cur.fetchall()

        # Check data_quality_log schema
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='data_quality_log' ORDER BY ordinal_position")
        dq_cols = [r[0] for r in cur.fetchall()]
        print(f"  data_quality_log columns: {dq_cols}")

        checks = [
            ("null_check_customer_id",        "dim_customer", "completeness"),
            ("null_check_product_id",         "dim_product",  "completeness"),
            ("revenue_positive_check",        "fact_sales",   "validity"),
            ("duplicate_sale_id_check",       "fact_sales",   "uniqueness"),
            ("referential_integrity_product", "fact_sales",   "integrity"),
            ("referential_integrity_customer","fact_sales",   "integrity"),
            ("date_range_check",              "fact_sales",   "validity"),
            ("quantity_range_check",          "fact_sales",   "validity"),
        ]

        print("Generating data quality logs...")
        quality_rows = []
        for run_id, run_time in runs:
            for check_name, table_name, check_type in checks:
                passed = random.random() > 0.04
                records_checked = random.randint(5000, 50000)
                records_failed = 0 if passed else random.randint(1, 50)
                score = round(((records_checked - records_failed) / records_checked) * 100, 2)
                quality_rows.append((
                    run_id, check_name, table_name, check_type,
                    "passed" if passed else "failed",
                    records_checked, records_failed, score, run_time
                ))

        # Try insert with run_id first
        try:
            psycopg2.extras.execute_batch(cur, """
                INSERT INTO data_quality_log
                    (run_id, check_name, table_name, check_type, status,
                     records_checked, records_failed, quality_score, run_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, quality_rows, page_size=500)
            conn.commit()
        except Exception:
            conn.rollback()
            # Fallback without run_id
            quality_rows_no_fk = [r[1:] for r in quality_rows]
            psycopg2.extras.execute_batch(cur, """
                INSERT INTO data_quality_log
                    (check_name, table_name, check_type, status,
                     records_checked, records_failed, quality_score, run_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, quality_rows_no_fk, page_size=500)
            conn.commit()

        print(f"  Loaded {len(quality_rows)} data quality log entries")

        print("\n=== VERIFICATION ===")
        cur.execute("SELECT COUNT(*) FROM etl_log")
        print(f"  etl_log:          {cur.fetchone()[0]:,} rows")
        cur.execute("SELECT COUNT(*) FROM data_quality_log")
        print(f"  data_quality_log: {cur.fetchone()[0]:,} rows")
        cur.execute("SELECT status, COUNT(*) FROM etl_log GROUP BY status")
        for row in cur.fetchall():
            print(f"  ETL status '{row[0]}': {row[1]} runs")
        cur.execute("SELECT ROUND(AVG(records_facts)) FROM etl_log WHERE status='success'")
        print(f"  Avg records/run:  {cur.fetchone()[0]:,}")
        print("\nLogs loaded successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    load()
