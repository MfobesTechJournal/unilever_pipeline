# Grafana PostgreSQL Connection Setup Guide

## Current Status ✓
The connection is **ALREADY CONFIGURED AND WORKING**, but here's how to verify and adjust if needed:

---

## Step-by-Step Verification & Configuration

### Step 1: Access Grafana
1. Open browser and go to: **http://localhost:3000**
2. Login with:
   - **Username**: admin
   - **Password**: admin

### Step 2: Navigate to Data Sources
1. In Grafana, click the **Settings Icon** (gear icon) in the left sidebar
2. Select **Data Sources**
   - Or go directly to: http://localhost:3000/connections/datasources

### Step 3: Check PostgreSQL Datasource
1. You should see **"PostgreSQL Warehouse"** listed
2. Click on it to view/edit configuration

### Step 4: Verify Datasource Settings
The connection should have these **EXACT** values:

```
Name: PostgreSQL Warehouse
Type: postgres
Host: postgres:5432           ← IMPORTANT: Use 'postgres' not 'localhost'
Database: unilever_warehouse
User: postgres
Password: 123456
SSL Mode: disable
PostgreSQL version: 14
```

**IF ANY VALUE IS DIFFERENT:**
- Edit the field to match the value above
- Click **Save & Test** button

### Step 5: Test the Connection
1. At the bottom of the datasource page, click **"Save & Test"**
2. You should see: **"Database Connection OK"** ✓
3. If you see an error:
   - Check the Host: Must be `postgres:5432` (not `localhost`)
   - Check Database: Must be `unilever_warehouse`
   - Check Username: Must be `postgres`
   - Check Password: Must be `123456`

---

## Step 6: View Your Dashboards

### Option A: Via Dashboard Menu
1. Click **Dashboards** in the left sidebar
2. You should see:
   - ✓ Sales Analytics
   - ✓ ETL Monitoring
3. Click either to view

### Option B: Direct Links
- **Sales Analytics**: http://localhost:3000/d/sales-analytics
- **ETL Monitoring**: http://localhost:3000/d/etl-monitoring

---

## Step 7: Verify Data Display

### Sales Analytics Dashboard Should Show:
- **Total Sales Revenue**: $54,380,419.57
- **Total Transactions**: 50,000
- **Average Order Value**: $1,087.61
- **Daily Sales Trend**: Graph with 30 days of data
- **Top 10 Products**: List of best-selling products

### ETL Monitoring Dashboard Should Show:
- **ETL Log Records**: 3 entries
- **Data Quality Issues**: 41 issues logged

---

## Troubleshooting

### Issue: "Database Connection FAILED" Error

**Problem 1: Host is "localhost" instead of "postgres"**
- Solution: Change Host to `postgres:5432`
- Reason: Inside Docker, use service name "postgres", not "localhost"

**Problem 2: Cannot connect to localhost:5432**
- Solution: Change Host to `postgres:5432`
- Make sure you're using the Docker service name

**Problem 3: "User 'postgres' does not exist"**
- Solution: Verify Username is exactly `postgres`
- Check spelling and case sensitivity

**Problem 4: "Invalid password"**
- Solution: Verify Password is exactly `123456`
- Check for spaces or typos

### Issue: Dashboards Show "No Data" or Empty Panels

**Even if connection is OK**, the panels might need:
1. Refresh: Click the refresh icon (circular arrow) in dashboard
2. Wait: Give it 5-10 seconds to load
3. Check datasource: Click on panel → Edit → Verify datasource is "PostgreSQL Warehouse"

### Issue: Can't Access Grafana at all

Check if Grafana is running:
```powershell
# Windows PowerShell
docker ps | Select-String grafana
```

Should show Grafana container running. If not:
```powershell
docker-compose up -d grafana
```

---

## Quick Configuration Checklist

Before moving forward, ensure all of these are TRUE:

- [ ] Grafana is accessible at http://localhost:3000
- [ ] You can login with admin/admin
- [ ] PostgreSQL Warehouse datasource exists in Data Sources list
- [ ] Datasource test returns "Database Connection OK"
- [ ] Both dashboards exist (Sales Analytics & ETL Monitoring)
- [ ] Dashboards show data when you click on them

---

## If You Need to Recreate the Connection

**If something is wrong, delete and recreate:**

1. Go to Data Sources (Settings → Data Sources)
2. Click **PostgreSQL Warehouse**
3. Scroll to bottom, click **Delete**
4. Click **Add Data Source**
5. Choose **PostgreSQL**
6. Fill in settings exactly as shown above:
   ```
   Name: PostgreSQL Warehouse
   Host: postgres:5432
   Database: unilever_warehouse
   User: postgres
   Password: 123456
   SSL Mode: disable
   ```
7. Click **Save & Test**

---

## Network Reference

```
Your Machine (localhost:5433)
         ↓
   Docker Network
         ↓
   PostgreSQL Container (postgres:5432)
         ↓
   Grafana Container (localhost:3000)
         ↓
   Browser (http://localhost:3000)
```

**KEY POINT**: 
- From your computer: Use `localhost:5433`
- From inside Docker: Use `postgres:5432`
- Grafana is INSIDE Docker, so it uses `postgres:5432`

---

## Verify Everything is Working

Run this command to confirm:
```powershell
python verify_dashboard_data.py
```

Should output:
```
✓ Database connection established
✓ All Required Tables
✓ Sales Analytics Dashboard POPULATED
✓ ETL Monitoring Dashboard POPULATED
```

If all checks pass ✓, your connection is correctly configured!
