import os
#!/usr/bin/env python3
"""
Simple PostgreSQL to Grafana Cloud connector via ngrok
"""

import subprocess
import json
import time
import requests
import sys

def run_command(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "Command timeout"
    except Exception as e:
        return 1, "", str(e)

def check_postgres():
    """Test PostgreSQL connection"""
    code, out, err = run_command('python -c "import psycopg2; conn = psycopg2.connect(host=\'127.0.0.1\', port=5433, user=\'postgres\', password=\'123456\', database=\'unilever_warehouse\'); print(\'OK\'); conn.close()"')
    if code == 0 and 'OK' in out:
        print("✓ PostgreSQL OK at localhost:5433")
        return True
    print("✗ PostgreSQL check failed")
    return False

def get_ngrok_tunnel():
    """Get ngrok tunnel URL from API"""
    for attempt in range(10):
        try:
            resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                for tunnel in data.get("tunnels", []):
                    if tunnel.get("proto") == "tcp":
                        return tunnel.get("public_url")
        except:
            pass
        time.sleep(0.5)
    return None

def start_tunnel():
    """Start ngrok tunnel"""
    print("[*] Starting ngrok tunnel...")
    
    # Kill any existing ngrok processes
    run_command("taskkill /F /IM ngrok.exe")
    time.sleep(1)
    
    # Start new tunnel
    proc = subprocess.Popen(
        "ngrok tcp 5433",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(3)
    
    # Get tunnel URL
    tunnel_url = get_ngrok_tunnel()
    if tunnel_url:
        print(f"✓ Tunnel started: {tunnel_url}")
        return tunnel_url, proc
    
    print("✗ Could not start tunnel")
    proc.terminate()
    return None, None

def update_datasource(tunnel_url):
    """Update Grafana datasource"""
    if not tunnel_url:
        print("✗ No tunnel URL provided")
        return False
    
    # Parse URL: tcp://1.tcp.ngrok.io:12345 -> host:port
    parts = tunnel_url.replace("tcp://", "").split(":")
    host = parts[0]
    port = int(parts[1]) if len(parts) > 1 else 5432
    
    print(f"[*] Updating Grafana datasource to {host}:{port}...")
    
    token = "os.environ.get("GRAFANA_TOKEN", "")_ebe31527"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    try:
        # Get datasource list
        resp = requests.get("https://mfobestechjournal.grafana.net/api/datasources", headers=headers, timeout=10)
        datasources = resp.json()
        
        for ds in datasources:
            if ds.get("type") == "postgres":
                ds_id = ds.get("id")
                
                # Prepare update
                payload = {
                    "id": ds_id,
                    "uid": ds.get("uid"),
                    "orgId": ds.get("orgId"),
                    "name": "PostgreSQL Warehouse",
                    "type": "postgres",
                    "access": "proxy",
                    "url": f"{host}:{port}",
                    "user": "postgres",
                    "database": "unilever_warehouse",
                    "secureJsonData": {"password": "123456"},
                    "jsonData": {
                        "sslmode": "disable",
                        "postgresVersion": 1400
                    },
                    "readOnly": False
                }
                
                # Update
                resp = requests.put(
                    f"https://mfobestechjournal.grafana.net/api/datasources/{ds_id}",
                    headers=headers,
                    json=payload,
                    timeout=10
                )
                
                if resp.status_code in [200, 201]:
                    print(f"✓ Datasource updated")
                    return True
                else:
                    print(f"✗ Update failed: {resp.status_code}")
                    return False
        
        print("✗ PostgreSQL datasource not found")
        return False
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    print("\n" + "="*80)
    print("POSTGRESQL BRIDGE TO GRAFANA CLOUD")
    print("="*80 + "\n")
    
    if not check_postgres():
        return False
    
    tunnel_url, proc = start_tunnel()
    if not tunnel_url:
        return False
    
    if not update_datasource(tunnel_url):
        if proc:
            proc.terminate()
        return False
    
    print("\n" + "="*80)
    print("✓ CONNECTION READY")
    print("="*80)
    print(f"""
Tunnel: {tunnel_url}
Grafana: https://mfobestechjournal.grafana.net

Your dashboards should now display data!

Keep this terminal open to maintain the connection.
Press Ctrl+C to stop the tunnel.

""")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        if proc:
            proc.terminate()
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
