"""
=============================================================
PHASE 7: DATABASE ADMINISTRATION
Database Optimization and Maintenance Script
=============================================================
"""

import psycopg2
from psycopg2 import sql
import os

# Database connection
DB_HOST = "localhost"
DB_PORT = "5433"
DB_NAME = "unilever_warehouse"
DB_USER = "postgres"
DB_PASSWORD = "123456"

def get_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def analyze_tables(conn):
    """Run ANALYZE on all tables to update statistics"""
    print("Analyzing tables...")
    tables = ['dim_product', 'dim_customer', 'dim_date', 'fact_sales']
    
    with conn.cursor() as cur:
        for table in tables:
            cur.execute(sql.SQL("ANALYZE {}").format(sql.Identifier(table)))
            print(f"  Analyzed: {table}")
    
    conn.commit()
    print("Table analysis completed.")

def vacuum_tables(conn):
    """Run VACUUM to reclaim storage and update statistics"""
    print("Vacuuming tables...")
    tables = ['dim_product', 'dim_customer', 'dim_date', 'fact_sales']
    
    with conn.cursor() as cur:
        for table in tables:
            cur.execute(sql.SQL("VACUUM ANALYZE {}").format(sql.Identifier(table)))
            print(f"  Vacuumed: {table}")
    
    conn.commit()
    print("Vacuum completed.")

def reindex_tables(conn):
    """Rebuild indexes to improve query performance"""
    print("Reindexing tables...")
    tables = ['dim_product', 'dim_customer', 'dim_date', 'fact_sales']
    
    with conn.cursor() as cur:
        for table in tables:
            # Get all indexes for the table
            cur.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = %s
            """, (table,))
            
            indexes = cur.fetchall()
            for idx in indexes:
                index_name = idx[0]
                cur.execute(sql.SQL("REINDEX INDEX {}").format(sql.Identifier(index_name)))
                print(f"  Reindexed: {index_name}")
    
    conn.commit()
    print("Reindexing completed.")

def check_table_sizes(conn):
    """Check sizes of all tables"""
    print("\nTable Sizes:")
    print("-" * 50)
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                n_live_tup as row_count
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """)
        
        results = cur.fetchall()
        for row in results:
            print(f"  {row[1]}: {row[2]} ({row[3]:,} rows)")
    
    print("-" * 50)

def check_index_usage(conn):
    """Check index usage statistics"""
    print("\nIndex Usage:")
    print("-" * 50)
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                indexrelname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            WHERE idx_scan > 0
            ORDER BY idx_scan DESC
        """)
        
        results = cur.fetchall()
        for row in results:
            print(f"  {row[0]}: {row[1]:,} scans")
    
    print("-" * 50)

def check_slow_queries(conn):
    """Check for slow queries in log"""
    print("\nSlow Queries (last 24 hours):")
    print("-" * 50)
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                query,
                calls,
                mean_exec_time,
                total_exec_time
            FROM pg_stat_statements
            WHERE query LIKE '%fact_%' OR query LIKE '%dim_%'
            ORDER BY mean_exec_time DESC
            LIMIT 10
        """)
        
        try:
            results = cur.fetchall()
            for row in results:
                print(f"  Query: {row[0][:50]}...")
                print(f"    Calls: {row[1]}, Mean: {row[2]:.2f}ms, Total: {row[3]:.2f}ms")
        except psycopg2.errors.UndefinedTable:
            print("  pg_stat_statements extension not installed")
    
    print("-" * 50)

def create_partitioned_fact_table(conn):
    """Create partitioned fact table for better performance"""
    print("\nCreating partitioned fact table...")
    
    with conn.cursor() as cur:
        # Create new partitioned fact table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fact_sales_partitioned (
                sales_key SERIAL,
                sale_id VARCHAR(50) NOT NULL,
                product_key INTEGER NOT NULL,
                customer_key INTEGER NOT NULL,
                date_key INTEGER NOT NULL,
                quantity INTEGER,
                revenue DECIMAL(12, 2),
                load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (sales_key, load_timestamp)
            ) PARTITION BY RANGE (load_timestamp);
        """)
        
        # Create partitions by month
        for i in range(1, 13):
            partition_name = f"fact_sales_2026_{i:02d}"
            cur.execute(sql.SQL("""
                CREATE TABLE {} PARTITION OF fact_sales_partitioned
                FOR VALUES FROM ('2026-{:02d}-01') TO ('2026-{:02d}-01')
            """).format(sql.Identifier(partition_name), i, (i % 12) + 1))
        
        conn.commit()
        print("  Partitioned table created.")

def main():
    """Main function to run all optimization tasks"""
    print("=" * 60)
    print("DATABASE OPTIMIZATION AND MAINTENANCE")
    print("=" * 60)
    
    conn = None
    try:
        conn = get_connection()
        
        # Check current state
        check_table_sizes(conn)
        check_index_usage(conn)
        
        # Run optimization tasks
        print("\nRunning optimization tasks...")
        analyze_tables(conn)
        vacuum_tables(conn)
        reindex_tables(conn)
        
        # Check again
        check_table_sizes(conn)
        check_index_usage(conn)
        
        # Check for slow queries
        check_slow_queries(conn)
        
        print("\n" + "=" * 60)
        print("OPTIMIZATION COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
