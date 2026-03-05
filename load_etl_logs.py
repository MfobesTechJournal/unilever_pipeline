#!/usr/bin/env python3
"""
ETL & Data Quality Log Generator
Loads realistic monitoring data into etl_log and data_quality_log
using the exact schema from unilever_warehouse
"""

import psycopg2
import psycopg2.extras
import random
from datetime import datetime, timedelta, date

random.seed(99)

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "unilever_warehouse",
    "user": "postgres",
    "password": "123456"
}

def generate_etl_and_quality_logs(start_date, end_date):
    etl_logs = []
    quality_logs = []

    current = start_date
    while current <= end_date:
        run_start = datetime(current.year, current.month, current.day, 2, 0, 0)
        duration_seconds = random.randint(180, 480)
        run_end = run_start + timedelta(seconds=duration_seconds)

        # 95% success rate
        success = random.random() > 0.05
        status = "success" if success else "failed"

        records_products  = random.randint(20, 25) if success else 0
        records_customers = random.randint(400, 600) if success else random.randint(0, 100)
        records_dates     = 365
        records_facts     = random.randint(800, 3500) if success else 0
        records_quality   = random.randint(0, 5) if success else random.randint(5, 50)
        error_message     = None if success else random.choice([
            "Connection timeout to source database",
            "Data validation failed: null values in required fields",
            "Insufficient disk space",
            "Source file not found",
            "Transform error: unexpected schema change",
        ])

        etl_logs.append((
            run_start,
            run_end,
            status,
            records_products,
            records_customers,
            records_dates,
            records_facts,
            records_quality,
            error_message,
        ))

        current += timedelta(days=1)

    return etl_logs


def generate_quality_logs(run_ids):
    quality_logs = []

    tables = ["dim_customer", "dim_product", "fact_sales", "dim_date"]
    check_types = [
        ("null_check", "Null values found in key columns"),
        ("duplicate_check", "Duplicate records detected"),
        ("referential_integrity", "Orphaned foreign key references"),
        ("range_check", "Values outside expected range"),
        ("completeness_check", "Missing required fields"),
    ]

    for run_id in run_ids:
        num_checks = random.randint(2, 5)
        for _ in range(num_checks):
            table = random.choice(tables)
            check_type, description = random.choice(check_types)
            issue_count = random.choices(
                [0, random.randint(1, 10), random.randint(10, 100)],
                weights=[85, 10, 5]
            )[0]
            quality_logs.append((
                run_id,
                table,
                check_type,
                issue_count,
                description if issue_count > 0 else "No issues found",
            ))

    return quality_logs


def load_logs():
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        print("Clearing existing logs...")
        cur.execute("TRUNCATE data_quality_log RESTART IDENTITY CASCADE")
        cur.execute("TRUNCATE etl_log RESTART IDENTITY CASCADE")
        conn.commit()

        # Generate 2 years of daily ETL runs
        start_date = date(2024, 1, 1)
        end_date   = date(2025, 12, 31)

        print(f"Generating ETL logs from {start_date} to {end_date}...")
        etl_logs = generate_etl_and_quality_logs(start_date, end_date)

        psycopg2.extras.execute_batch(cur, """
            INSERT INTO etl_log
                (start_time, end_time, status,
                 records_products, records_customers, records_dates,
                 records_facts, records_quality_issues, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, etl_logs, page_size=200)
        conn.commit()
        print(f"  Loaded {len(etl_logs)} ETL run logs")

        # Fetch inserted run_ids
        cur.execute("SELECT run_id FROM etl_log ORDER BY run_id")
        run_ids = [r[0] for r in cur.fetchall()]

        print("Generating data quality logs...")
        quality_logs = generate_quality_logs(run_ids)

        psycopg2.extras.execute_batch(cur, """
            INSERT INTO data_quality_log
                (run_id, table_name, check_type, issue_count, issue_description)
            VALUES (%s, %s, %s, %s, %s)
        """, quality_logs, page_size=500)
        conn.commit()
        print(f"  Loaded {len(quality_logs)} data quality log entries")

        # Verify
        print("\n=== VERIFICATION ===")
        cur.execute("SELECT COUNT(*) FROM etl_log")
        print(f"  etl_log:          {cur.fetchone()[0]:,} rows")
        cur.execute("SELECT COUNT(*) FROM data_quality_log")
        print(f"  data_quality_log: {cur.fetchone()[0]:,} rows")
        cur.execute("SELECT status, COUNT(*) FROM etl_log GROUP BY status")
        for row in cur.fetchall():
            print(f"  ETL status '{row[0]}': {row[1]} runs")
        cur.execute("SELECT ROUND(AVG(records_facts)) FROM etl_log WHERE status = 'success'")
        print(f"  Avg records/run:  {cur.fetchone()[0]:,}")

        print("\nLogs loaded successfully!")

    except Exception as e:
        conn.rollback()
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    load_logs()
