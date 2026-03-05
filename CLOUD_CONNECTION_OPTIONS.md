# Cloud Grafana + Local PostgreSQL Connection Guide

## Current Situation
- **Cloud Grafana**: https://mfobestechjournal.grafana.net (can see dashboards but no data)
- **Local PostgreSQL**: Running in Docker at localhost:5433
- **Challenge**: Cloud Grafana cannot reach local network/database

## Why Current Setup Doesn't Work
The datasource URL `unilever_postgres:5432` doesn't resolve in Grafana Cloud because:
- `unilever_postgres` is a Docker container name (only resolvable within Docker network)
- Cloud Grafana has no route to your local network
- Network isolation exists between cloud and your machine

## Solution Options (Ranked by Practicality)

### **Option 1: Grafana Agent (Recommended - Requires Installation)**
**Status**: Partially attempted

**What it does**:
- Creates a secure tunnel from cloud Grafana to your local PostgreSQL
- No firewall/port exposure needed
- Most secure for production
- Microsoft Windows native service

**Requirements**:
- Download & install Grafana Agent MSI from: https://grafana.com/grafana/agent/
- Create agent configuration file
- Start service
- Update datasource to use agent bridge

**Pros**:
- ✓ Secure encrypted tunnel
- ✓ No firewall port exposure
- ✓ Grafana-supported solution
- ✓ Can handle variable network conditions

**Cons**:
- ✗ Requires MSI installation + service setup
- ✗ Moderate configuration complexity

**Cost**: Free

**Next Steps if choosing this**:
1. Download: https://grafana.com/grafana/agent/
2. Run MSI installer (may need admin)
3. Configure: `C:\Program Files\Grafana\agent\agent-config.yaml`
4. Restart Grafana Agent service
5. Update datasource via Grafana Cloud UI

---

### **Option 2: Local TCP Bridge + Global Tunnel Service (Easy Setup)**
**Status**: Can implement now

**What it does**:
- Python script listens on local port 5555
- Forwards to PostgreSQL at localhost:5433
- Uses ngrok/Cloudflare Tunnel to expose publicly
- Cloud Grafana connects to public URL

**Requires**:
- ngrok account (free tier available) OR Cloudflare Tunnel (free)
- ngrok CLI with auth token
- Keep Python script running

**Pros**:
- ✓ No installation required (pure Python)
- ✓ Quick setup (5 minutes)
- ✓ Free ngrok account available
- ✓ Cloudflare alternative for better stability

**Cons**:
- ✗ Requires external service account
- ✗ Must keep terminal window open
- ✗ ngrok free tier has limitations
- ✗ Less secure than Grafana Agent

**Cost**: Free (ngrok), or $7-20/month for premium

**Next Steps if choosing this**:
1. Create ngrok account: https://ngrok.com/
2. Get auth token from dashboard
3. Run: `ngrok config add-authtoken <your-token>`
4. Run: `python tcp_bridge.py`
5. Note public URL from ngrok output
6. Update datasource in Grafana Cloud with that URL

---

### **Option 3: Manual Port Forwarding + Public IP (Advanced)**
**Status**: Possible but complex

**What it does**:
- Run TCP bridge on local machine
- Manually configure router port forwarding
- Cloud Grafana connects via your public IP:5555
- Requires network/firewall knowledge

**Requires**:
- Access to router/firewall settings
- Static IP or dynamic DNS
- Understanding of port forwarding

**Pros**:
- ✓ No external service needed
- ✓ Full control
- ✓ Can be very stable

**Cons**:
- ✗ Complex network setup
- ✗ Security exposure (open port on internet)
- ✗ Fragile if public IP changes
- ✗ Requires router access

**Cost**: Free but requires infrastructure knowledge

---

### **Option 4: Migrate to Cloud PostgreSQL (Architectural Change)**
**Status**: Nuclear option

**What it does**:
- Move PostgreSQL to cloud (AWS RDS, Azure Database, Heroku, etc.)
- Point Grafana to cloud database
- No network bridging needed

**Pros**:
- ✓ Simplest for cloud architecture
- ✓ Grafana Cloud native integration
- ✓ Scalable and robust
- ✓ No local services needed

**Cons**:
- ✗ Data migration effort
- ✗ Monthly costs
- ✗ Changes your architecture
- ✗ Overkill for local testing

**Cost**: $5-50/month depending on service

---

## Current Datasource Status

**Datasource UID**: `bfew4d1gmjw8wf`
**Current URL**: `unilever_postgres:5432` (doesn't work)
**Database**: `unilever_warehouse`
**User**: `postgres`
**Password**: `123456`

---

## Recommended Path Forward

### For immediate testing (2-5 minutes):
1. **Use Option 2 (ngrok)**
   - Quick to set up
   - Free trial available
   - No installation complexity
   - Can test dashboards in minutes

### For production/stability (15-30 minutes):
2. **Use Option 1 (Grafana Agent)**
   - Official Grafana solution
   - Secure and supported
   - No external service dependency
   - Better reliability

### IF stuck on Grafana Agent:
3. **Fall back to Option 2** while troubleshooting agent installation

---

## Files Created for You

| File | Purpose | Option |
|------|---------|--------|
| `tcp_bridge.py` | TCP proxy/bridge | All options |
| `postgres_bridge.py` | ngrok wrapper | Option 2 |
| `simple_bridge.py` | Simplified ngrok | Option 2 |
| `setup_grafana_agent.py` | Agent configuration | Option 1 |

---

## Quick Start: Option 2 (ngrok)

```powershell
# 1. Create ngrok account and get token
# 2. Configure ngrok
ngrok config add-authtoken <your-token-here>

# 3. Start TCP bridge
python tcp_bridge.py

# 4. In another terminal, start ngrok tunnel
ngrok tcp --addr localhost:5555

# 5. Note the public URL (look for: tcp://X.tcp.ngrok.io:XXXXX)

# 6. Update Grafana datasource:
#    - Go to: https://mfobestechjournal.grafana.net/connections/datasources/edit/bfew4d1gmjw8wf
#    - Change Host to: X.tcp.ngrok.io
#    - Change Port to: XXXXX (from step 5)
#    - Click "Save & Test"

# 7. Dashboards should populate with data!
```

---

## Questions to Ask Yourself

1. **Is this for testing or production?**
   - Testing → Option 2 (quick)
   - Production → Option 1 (secure)

2. **Can you keep terminal windows open?**
   - Yes → Option 2 or 3
   - No → Option 1 (runs as service)

3. **Do you have firewall/router access?**
   - Yes → Option 3 (complex but free)
   - No → Option 1 or 2

4. **Is network bridging a long-term need?**
   - Yes → Invest in Option 1
   - No (temporary testing) → Option 2

---

## What I Recommend

**Given your situation (Windows, cloud Grafana trial, urgent need for data display):**

→ **Use Option 2 (ngrok)** for **immediate results** (next 10 minutes)

→ **Then plan Option 1 (Grafana Agent)** for **production stability** (next 24 hours)

**My suggested next action**: Create ngrok account and try the Quick Start above.

---

## Need Help?

- **Grafana Agent install issues**: Check registry for previous installations, confirm admin rights
- **ngrok issues**: Verify account, check auth token, try v3 syntax
- **Port access issues**: Check Windows Defender firewall, router settings
- **PostgreSQL connectivity**: Verify with: `docker ps` (should show running postgres container)

Let me know which option you prefer, and I'll guide you through the setup!
