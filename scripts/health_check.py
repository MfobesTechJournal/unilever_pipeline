#!/usr/bin/env python3
"""
Production Health Check Script
Verifies all critical systems are operational
"""

import psycopg2
import requests
import socket
import sys
from datetime import datetime

def check_postgres():
    """Check PostgreSQL database connectivity"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="unilever_warehouse",
            user="postgres",
            password="123456"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM fact_sales")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return True, f"PostgreSQL ✓ ({count:,} records in warehouse)"
    except Exception as e:
        return False, f"PostgreSQL ✗ Error: {str(e)[:50]}"

def check_grafana():
    """Check Grafana service"""
    try:
        response = requests.get('http://localhost:3000/api/health', timeout=5)
        if response.status_code == 200:
            return True, "Grafana ✓ (http://localhost:3000)"
        return False, f"Grafana ✗ Status: {response.status_code}"
    except Exception as e:
        return False, f"Grafana ✗ Error: {str(e)[:50]}"

def check_airflow():
    """Check Airflow service"""
    try:
        # Try main page first (more reliable)
        response = requests.get('http://localhost:8080', timeout=5)
        if response.status_code == 200:
            return True, "Airflow ✓ (http://localhost:8080)"
        return False, f"Airflow ✗ Status: {response.status_code}"
    except Exception as e:
        return False, f"Airflow ✗ Error: {str(e)[:50]}"

def check_prometheus():
    """Check Prometheus service"""
    try:
        response = requests.get('http://localhost:9090/-/healthy', timeout=5)
        if response.status_code == 200:
            return True, "Prometheus ✓ (http://localhost:9090)"
        return False, f"Prometheus ✗ Status: {response.status_code}"
    except Exception as e:
        return False, f"Prometheus ✗ Error: {str(e)[:50]}"

def check_streamlit():
    """Check Streamlit service"""
    try:
        response = requests.get('http://localhost:8501', timeout=5)
        if response.status_code == 200:
            return True, "Streamlit ✓ (http://localhost:8501)"
        return False, f"Streamlit ✗ Status: {response.status_code}"
    except Exception as e:
        return False, f"Streamlit ✗ Error: {str(e)[:50]}"

def check_port(host, port, service_name):
    """Check if a port is accessible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def main():
    """Run all health checks"""
    print("\n" + "="*70)
    print("UNILEVER DATA PIPELINE - PRODUCTION HEALTH CHECK")
    print("="*70 + "\n")
    
    checks = [
        ("PostgreSQL", check_postgres),
        ("Grafana", check_grafana),
        ("Streamlit", check_streamlit),
        ("Airflow", check_airflow),
        ("Prometheus", check_prometheus)
    ]
    
    all_pass = True
    for name, check_func in checks:
        success, message = check_func()
        status = "✓" if success else "✗"
        print(f"[{status}] {message}")
        if not success:
            all_pass = False
    
    print("\n" + "="*70)
    if all_pass:
        print("✓ ALL SYSTEMS OPERATIONAL - READY FOR PRODUCTION")
        print("="*70)
        return 0
    else:
        print("✗ SOME SYSTEMS FAILED - CHECK LOGS")
        print("="*70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
