#!/usr/bin/env python3
"""
PostgreSQL Bridge - Exposes local PostgreSQL to cloud Grafana via public tunnel
Uses ngrok to create a public URL that forwards to local PostgreSQL
"""

import subprocess
import time
import sys
import requests
import json
import os

GRAFANA_CLOUD_URL = "https://mfobestechjournal.grafana.net"
API_TOKEN = "os.environ.get("GRAFANA_TOKEN", "")_ebe31527"

def check_postgres_connection():
    """Verify local PostgreSQL is accessible"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            user="postgres",
            password="123456",
            database="unilever_warehouse"
        )
        conn.close()
        print("✓ PostgreSQL is accessible at localhost:5433")
        return True
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        return False

def check_ngrok():
    """Check if ngrok is installed"""
    try:
        result = subprocess.run(["ngrok", "version"], capture_output=True, text=True)
        print(f"✓ ngrok is installed: {result.stdout.split()[0]}")
        return True
    except FileNotFoundError:
        print("✗ ngrok not found. Install from: https://ngrok.com/download")
        return False

def install_ngrok():
    """Attempt to install ngrok via chocolatey or manual download"""
    print("\n[*] Attempting to install ngrok...")
    
    try:
        # Try chocolatey
        result = subprocess.run(["choco", "install", "ngrok", "-y"], 
                              capture_output=True, timeout=60)
        if result.returncode == 0:
            print("✓ ngrok installed via Chocolatey")
            return True
    except:
        pass
    
    print("⚠ Could not install ngrok automatically")
    print("  Please download from: https://ngrok.com/download")
    print("  And add to PATH, then run this script again")
    return False

def start_ngrok_tunnel():
    """Start ngrok tunnel to local PostgreSQL"""
    print("\n[*] Starting ngrok tunnel to localhost:5433...")
    
    try:
        # Start ngrok in background
        process = subprocess.Popen(
            ["ngrok", "tcp", "5433"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for tunnel to start and get public URL
        time.sleep(3)
        
        # Check ngrok API
        try:
            ngrok_api = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
            if ngrok_api.status_code == 200:
                tunnels = ngrok_api.json()["tunnels"]
                for tunnel in tunnels:
                    if tunnel["proto"] == "tcp":
                        public_url = tunnel["public_url"]  # e.g., "tcp://1.tcp.ngrok.io:12345"
                        print(f"✓ ngrok tunnel started: {public_url}")
                        return public_url, process
        except:
            pass
        
        print("⚠ Could not retrieve ngrok tunnel info")
        print("  ngrok API may be running on different port")
        return None, process
        
    except FileNotFoundError:
        print("✗ ngrok command not found")
        return None, None

def parse_ngrok_url(public_url):
    """Extract host and port from ngrok TCP URL"""
    # Format: tcp://1.tcp.ngrok.io:12345
    if not public_url:
        return None, None
    
    parts = public_url.replace("tcp://", "").split(":")
    host = parts[0]
    port = int(parts[1]) if len(parts) > 1 else 5432
    return host, port

def update_grafana_datasource(host, port):
    """Update Grafana datasource to use ngrok public URL"""
    print(f"\n[*] Updating Grafana datasource to {host}:{port}...")
    
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Get datasource
    try:
        response = requests.get(f"{GRAFANA_CLOUD_URL}/api/datasources", headers=headers, timeout=10)
        datasources = response.json()
        
        pg_ds = None
        ds_id = None
        for ds in datasources:
            if 'postgres' in ds.get('type', '').lower():
                pg_ds = ds
                ds_id = ds.get('id')
                break
        
        if not pg_ds:
            print("✗ PostgreSQL datasource not found in Grafana Cloud")
            return False
        
        # Update datasource with public ngrok URL
        update_payload = {
            "name": "PostgreSQL Warehouse (via ngrok)",
            "type": "postgres",
            "url": f"{host}:{port}",
            "access": "proxy",
            "isDefault": True,
            "jsonData": {
                "sslmode": "disable",
                "postgresVersion": 1400,
                "maxOpenConns": 0,
                "maxIdleConns": 2,
                "connMaxLifetime": 14400
            },
            "secureJsonData": {
                "password": "123456"
            }
        }
        
        # Add other fields from original datasource
        for key in ['id', 'uid', 'orgId', 'readOnly']:
            if key in pg_ds:
                update_payload[key] = pg_ds[key]
        
        update_payload['database'] = 'unilever_warehouse'
        update_payload['user'] = 'postgres'
        
        response = requests.put(
            f"{GRAFANA_CLOUD_URL}/api/datasources/{ds_id}",
            headers=headers,
            json=update_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✓ Datasource updated successfully")
            return True
        else:
            print(f"✗ Datasource update failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error updating datasource: {e}")
        return False

def main():
    print("\n" + "="*80)
    print("GRAFANA CLOUD - LOCAL POSTGRESQL BRIDGE (via ngrok)")
    print("="*80)
    
    # Step 1: Check PostgreSQL
    if not check_postgres_connection():
        print("\nCannot proceed without local PostgreSQL. Docker containers running?")
        print("Run: cd 11-infrastructure/network ; docker-compose up -d")
        return False
    
    # Step 2: Check/install ngrok
    if not check_ngrok():
        if not install_ngrok():
            print("\nManual Installation Required:")
            print("1. Download ngrok from https://ngrok.com/download")
            print("2. Extract and add to PATH")
            print("3. Run this script again")
            return False
    
    # Step 3: Start ngrok tunnel
    public_url, process = start_ngrok_tunnel()
    if not public_url:
        print("\n✗ Could not establish ngrok tunnel")
        if process:
            process.terminate()
        return False
    
    # Step 4: Parse ngrok URL
    host, port = parse_ngrok_url(public_url)
    if not host:
        print(f"✗ Could not parse ngrok URL: {public_url}")
        if process:
            process.terminate()
        return False
    
    # Step 5: Update Grafana datasource
    if not update_grafana_datasource(host, port):
        print("\n✗ Failed to update Grafana datasource")
        if process:
            process.terminate()
        return False
    
    # Step 6: Test connection
    print(f"\n[*] Testing Grafana connection...")
    time.sleep(2)
    
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # Test datasource health
        response = requests.get(
            f"{GRAFANA_CLOUD_URL}/api/datasources/uid/bfew4d1gmjw8wf/health",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✓ Datasource health check PASSED")
            print(f"✓ Response: {response.json()}")
        else:
            print(f"⚠ Health check returned: {response.status_code}")
            
    except Exception as e:
        print(f"⚠ Health check failed: {e}")
    
    print("\n" + "="*80)
    print("SETUP COMPLETE")
    print("="*80)
    print(f"""
✓ ngrok tunnel is running: {public_url}
✓ Grafana datasource updated to {host}:{port}

Your dashboards should now display data!

Next Steps:
1. Keep this terminal window open (tunnel must stay active)
2. Go to Grafana Cloud: https://mfobestechjournal.grafana.net
3. Refresh your dashboards (F5)
4. You should see data populating

To stop the bridge:
- Press Ctrl+C in this terminal
- Datasource will need to be updated again when restarted

Troubleshooting:
- If data still doesn't appear, wait 30 seconds and refresh again
- Check dashboard query with time filter updated in Grafana UI
- Verify PostgreSQL is running: docker ps

""")
    
    # Keep tunnel alive
    print("Tunnel is active. Press Ctrl+C to stop...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down tunnel...")
        if process:
            process.terminate()
            process.wait()
        print("Bridge stopped.")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
