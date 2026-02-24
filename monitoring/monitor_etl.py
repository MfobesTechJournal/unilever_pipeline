"""
=============================================================
PHASE 8: MONITORING & LOGGING
ETL Monitoring and Alerting Script
=============================================================
"""

import psycopg2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Configuration (from environment or defaults)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5433"))
DB_NAME = os.getenv("DB_NAME", "unilever_warehouse")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")

# Email configuration (for alerts) - from environment
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@unilever.com")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "alerts@company.com")

# Alert thresholds
ALERT_QUALITY_ISSUES_MAX = int(os.getenv("ALERT_QUALITY_ISSUES_MAX", "100"))
ALERT_FAILED_RUNS_COUNT = int(os.getenv("ALERT_FAILED_RUNS_COUNT", "3"))

def get_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def check_etl_runs(conn, hours=24):
    """Check ETL runs in the last N hours"""
    print(f"\nETL Runs (last {hours} hours):")
    print("-" * 80)
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                run_id,
                start_time,
                end_time,
                status,
                records_products,
                records_customers,
                records_dates,
                records_facts,
                error_message
            FROM etl_log
            WHERE start_time > NOW() - INTERVAL '%s hours'
            ORDER BY start_time DESC
        """, (hours,))
        
        results = cur.fetchall()
        for row in results:
            print(f"Run ID: {row[0]}")
            print(f"  Start: {row[1]}, End: {row[2]}")
            print(f"  Status: {row[3]}")
            print(f"  Records: Products={row[4]}, Customers={row[5]}, Dates={row[6]}, Facts={row[7]}")
            if row[8]:
                print(f"  Error: {row[8][:100]}...")
            print("-" * 80)
        
        return results

def check_failed_runs(conn):
    """Check for failed ETL runs"""
    print("\nFailed ETL Runs:")
    print("-" * 80)
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                run_id,
                start_time,
                status,
                error_message
            FROM etl_log
            WHERE status = 'FAILURE'
            ORDER BY start_time DESC
            LIMIT 10
        """)
        
        results = cur.fetchall()
        for row in results:
            print(f"Run ID: {row[0]}, Time: {row[1]}")
            print(f"  Error: {row[3][:200] if row[3] else 'No error message'}")
            print("-" * 80)
        
        return results

def check_data_growth(conn):
    """Check data growth over time"""
    print("\nData Growth (last 30 days):")
    print("-" * 80)
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                DATE(start_time) as run_date,
                MAX(records_products) as max_products,
                MAX(records_customers) as max_customers,
                MAX(records_dates) as max_dates,
                MAX(records_facts) as max_facts
            FROM etl_log
            WHERE status = 'SUCCESS'
                AND start_time > NOW() - INTERVAL '30 days'
            GROUP BY DATE(start_time)
            ORDER BY run_date DESC
        """)
        
        results = cur.fetchall()
        for row in results:
            print(f"Date: {row[0]}")
            print(f"  Products: {row[1]:,}, Customers: {row[2]:,}, Dates: {row[3]:,}, Facts: {row[4]:,}")
            print("-" * 80)
        
        return results

def check_data_quality(conn):
    """Check data quality metrics"""
    print("\nData Quality Checks:")
    print("-" * 80)
    
    with conn.cursor() as cur:
        # Check for nulls in fact table
        cur.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE product_key IS NULL) as null_products,
                COUNT(*) FILTER (WHERE customer_key IS NULL) as null_customers,
                COUNT(*) FILTER (WHERE date_key IS NULL) as null_dates,
                COUNT(*) FILTER (WHERE quantity IS NULL) as null_quantity,
                COUNT(*) FILTER (WHERE revenue IS NULL) as null_revenue
            FROM fact_sales
        """)
        
        nulls = cur.fetchone()
        print(f"Fact Sales Null Counts:")
        print(f"  Null Product Keys: {nulls[0]:,}")
        print(f"  Null Customer Keys: {nulls[1]:,}")
        print(f"  Null Date Keys: {nulls[2]:,}")
        print(f"  Null Quantity: {nulls[3]:,}")
        print(f"  Null Revenue: {nulls[4]:,}")
        
        # Check for duplicates
        cur.execute("""
            SELECT COUNT(*) - COUNT(DISTINCT sale_id) as duplicate_sales
            FROM fact_sales
        """)
        
        duplicates = cur.fetchone()
        print(f"\nDuplicate Sales: {duplicates[0]:,}")
        
        # Check for negative quantities
        cur.execute("""
            SELECT COUNT(*) as negative_quantities
            FROM fact_sales
            WHERE quantity < 0
        """)
        
        negative = cur.fetchone()
        print(f"Negative Quantities: {negative[0]:,}")
        
        # Check for negative revenue
        cur.execute("""
            SELECT COUNT(*) as negative_revenue
            FROM fact_sales
            WHERE revenue < 0
        """)
        
        negative_rev = cur.fetchone()
        print(f"Negative Revenue: {negative_rev[0]:,}")
        
        print("-" * 80)
        
        return {
            'null_products': nulls[0],
            'null_customers': nulls[1],
            'null_dates': nulls[2],
            'null_quantity': nulls[3],
            'null_revenue': nulls[4],
            'duplicates': duplicates[0],
            'negative_quantities': negative[0],
            'negative_revenue': negative_rev[0]
        }

def check_processing_time(conn):
    """Check ETL processing time trends"""
    print("\nProcessing Time Trends:")
    print("-" * 80)
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                DATE(start_time) as run_date,
                AVG(EXTRACT(EPOCH FROM (end_time - start_time))) as avg_duration
            FROM etl_log
            WHERE status = 'SUCCESS'
                AND start_time > NOW() - INTERVAL '30 days'
            GROUP BY DATE(start_time)
            ORDER BY run_date DESC
            LIMIT 10
        """)
        
        results = cur.fetchall()
        for row in results:
            duration = row[1] if row[1] else 0
            print(f"Date: {row[0]}, Avg Duration: {duration:.2f} seconds")
        
        print("-" * 80)
        
        return results

def send_alert(subject, message):
    """Send email alert"""
    print(f"\nSending alert: {subject}")
    print(f"Message: {message}")
    
    # Check if SMTP is configured
    if not SMTP_USER or not SMTP_PASSWORD:
        print("WARNING: SMTP credentials not configured. Set SMTP_USER and SMTP_PASSWORD in .env")
        print("Alert details:")
        print(f"  Subject: {subject}")
        print(f"  Message: {message[:200]}...")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = ALERT_EMAIL
        msg['Subject'] = f"[UNILEVER ETL ALERT] {subject}"
        msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
        
        # Create HTML body
        html_message = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #d9534f;">{subject}</h2>
                <p>{message.replace(chr(10), '<br>')}</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    Alert generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                    Unilever ETL Pipeline Monitoring System
                </p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(message, 'plain'))
        msg.attach(MIMEText(html_message, 'html'))
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print("✓ Alert sent successfully")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print(f"✗ Failed: SMTP Authentication failed. Check SMTP_USER and SMTP_PASSWORD")
        return False
    except smtplib.SMTPException as e:
        print(f"✗ Failed: SMTP error: {e}")
        return False
    except Exception as e:
        print(f"✗ Failed to send alert: {e}")
        return False

def main():
    """Main function to run all monitoring tasks"""
    print("=" * 80)
    print("ETL MONITORING AND LOGGING")
    print("=" * 80)
    
    conn = None
    try:
        conn = get_connection()
        
        # Run all checks
        check_etl_runs(conn)
        check_failed_runs(conn)
        check_data_growth(conn)
        quality = check_data_quality(conn)
        check_processing_time(conn)
        
        # Check for issues and send alerts
        failed_runs = check_failed_runs(conn)
        if failed_runs:
            send_alert(
                "ETL Pipeline Failure",
                f"There are {len(failed_runs)} failed ETL runs in the last 24 hours"
            )
        
        if quality['null_products'] > 0 or quality['null_customers'] > 0:
            send_alert(
                "Data Quality Issue",
                f"Found null keys in fact_sales table"
            )
        
        print("\n" + "=" * 80)
        print("MONITORING COMPLETED")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error: {e}")
        send_alert("Monitoring Script Error", str(e))
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
