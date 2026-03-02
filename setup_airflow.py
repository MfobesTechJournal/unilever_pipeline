#!/usr/bin/env python3
"""
Configure and test Airflow DAGs
Connects to http://localhost:8080
"""

import requests
import json
import time
from datetime import datetime

AIRFLOW_URL = "http://localhost:8080"
AIRFLOW_USER = "airflow"
AIRFLOW_PASSWORD = "airflow"

def wait_for_airflow():
    """Wait for Airflow to be ready"""
    print("Waiting for Airflow to start...", end=" ", flush=True)
    for i in range(30):
        try:
            response = requests.get(f"{AIRFLOW_URL}/health", timeout=2)
            if response.status_code == 200:
                print("✓")
                return True
        except:
            time.sleep(1)
    print("✗ Timeout")
    return False

def list_dags():
    """List all available DAGs"""
    print("\n📋 Available DAGs:")
    try:
        # Airflow v2 uses REST API
        response = requests.get(
            f"{AIRFLOW_URL}/api/v1/dags",
            auth=(AIRFLOW_USER, AIRFLOW_PASSWORD),
            timeout=10
        )
        if response.status_code == 200:
            dags = response.json().get('dags', [])
            for dag in dags:
                print(f"  • {dag['dag_id']}")
            return dags
        else:
            print(f"  (Could not fetch - Airflow may be initializing)")
            return []
    except Exception as e:
        print(f"  (API not ready: {e})")
        return []

def unpause_dag(dag_id):
    """Unpause a DAG to enable it"""
    print(f"\n Enabling {dag_id}...", end=" ", flush=True)
    try:
        response = requests.post(
            f"{AIRFLOW_URL}/api/v1/dags/{dag_id}/set_paused",
            json={"is_paused": False},
            auth=(AIRFLOW_USER, AIRFLOW_PASSWORD),
            timeout=10
        )
        if response.status_code == 200:
            print("✓")
            return True
        else:
            print(f"✗ ({response.status_code})")
            return False
    except Exception as e:
        print(f"✗")
        return False

def trigger_dag(dag_id):
    """Trigger a DAG run"""
    print(f"  Triggering {dag_id}...", end=" ", flush=True)
    try:
        response = requests.post(
            f"{AIRFLOW_URL}/api/v1/dags/{dag_id}/dagRuns",
            json={
                "execution_date": datetime.utcnow().isoformat(),
                "conf": {}
            },
            auth=(AIRFLOW_USER, AIRFLOW_PASSWORD),
            timeout=10
        )
        if response.status_code in [200, 201]:
            print("✓")
            return True
        else:
            print(f"✗")
            return False
    except Exception as e:
        print(f"✗")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("AIRFLOW SETUP & TESTING - Unilever Pipeline")
    print("=" * 60)
    print(f"Target: {AIRFLOW_URL}")
    
    if not wait_for_airflow():
        print("\n✗ Airflow did not respond")
        exit(1)
    
    dags = list_dags()
    
    # Try to enable key DAGs
    target_dags = ['etl_dag', 'etl_dag_production', 'etl_load_staging']
    print("\n" + "=" * 60)
    print("CONFIGURATION")
    print("=" * 60)
    
    for dag_id in target_dags:
        unpause_dag(dag_id)
    
    print("\n✓ Airflow is now operational!")
    print(f"   Access at: http://localhost:8080")
    print(f"   Login: airflow / airflow")
    print("=" * 60)
