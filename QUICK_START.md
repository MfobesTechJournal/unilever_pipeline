# 🚀 UNILEVER PIPELINE - QUICK START GUIDE

**Status: ✅ FULLY OPERATIONAL**

---

## 📍 Where Are We?

Your complete enterprise data warehouse is **live and running**:

| Component | Status | Access |
|-----------|--------|--------|
| **PostgreSQL** | ✅ Running | `localhost:5433` |
| **pgAdmin** | ✅ Running | http://localhost:5050 |
| **Grafana** | ✅ Running | http://localhost:3000 |
| **Airflow** | ✅ Running | http://localhost:8080 |
| **Prometheus** | ✅ Running | http://localhost:9090 |

**Data Loaded:** 57,231 records across 4 tables

---

## 🎯 WHAT TO DO NOW (5-10 minutes)

### 1️⃣ View Your Data Dashboards (Grafana)
```
URL:      http://localhost:3000
Login:    admin / admin
```
✨ **What you'll see:**
- 💰 Total sales revenue
- 📊 Daily sales trends
- 🏆 Top 10 products
- 📈 ETL execution logs

**Dashboard:** "Sales Analytics" (auto-created)

### 2️⃣ Access Databases (pgAdmin)
```
URL:      http://localhost:5050
Login:    admin@unilever.com / admin123
```
✨ **Features:**
- Browse 4 warehouse tables
- Run SQL queries
- View row counts
- Monitor performance

### 3️⃣ Run Automated Pipelines (Airflow)
```
URL:      http://localhost:8080
Login:    airflow / airflow
```
✨ **Available:**
- 5 production DAGs
- Daily schedule
- Data quality checks
- Automatic error handling

### 4️⃣ Monitor System Health
```bash
cd c:\Users\Mfobe Ntintelo\Documents\unilever_pipeline
python validate_system.py
```
Shows all services and data status ✓

---

## 🔑 All Credentials Cheat Sheet

```
DATABASE
├─ Host:     localhost:5433
├─ User:     postgres
└─ Password: 123456

pgADMIN
├─ URL:      http://localhost:5050
├─ Email:    admin@unilever.com
└─ Password: admin123

GRAFANA
├─ URL:      http://localhost:3000
├─ User:     admin
└─ Password: admin

AIRFLOW
├─ URL:      http://localhost:8080
├─ User:     airflow
└─ Password: airflow

PROMETHEUS
└─ URL:      http://localhost:9090
```

---

## 📈 Your Data at a Glance

```
✓ 1,500 Products   (loaded to dim_product)
✓ 5,000 Customers  (loaded to dim_customer)
✓ 731 Dates        (date dimension with SCD Type 2)
✓ 50,000 Sales     (fact_sales transactions)

Total: 57,231 records ready for analysis
```

---

## 🔧 Common Operations

### Reload Fresh Sample Data
```bash
python load_sales_simple.py
```
Creates new sample CSV files and reloads warehouse

### Check System Health
```bash
python validate_system.py
```
Validates all services and data

### View Pipeline Logs
In Airflow → Select DAG → View Logs  
Or in PostgreSQL:
```sql
SELECT * FROM etl_log ORDER BY execution_date DESC LIMIT 10;
```

### Run a Query on Your Data
In pgAdmin (http://localhost:5050):
```sql
-- Top selling products
SELECT dp.product_name, COUNT(*) as sales_count, SUM(fs.revenue) as revenue
FROM fact_sales fs
JOIN dim_product dp ON fs.product_key = dp.product_key
GROUP BY dp.product_name
ORDER BY revenue DESC
LIMIT 10;
```

---

## 🎓 Learning Path

1. **Week 1: Explore**
   - Browse data in pgAdmin
   - Create your first Grafana dashboard
   - Understand the data model

2. **Week 2: Automate**
   - Schedule Airflow DAGs
   - Set up alerts in Grafana
   - Create data quality checks

3. **Week 3: Scale**
   - Deploy to AWS
   - Implement real-time streaming
   - Add advanced analytics

---

## 🚨 If Something Goes Wrong

### Service not responding?
```bash
# Restart all services
cd 11-infrastructure/network
docker-compose down
docker-compose up -d
```

### Can't connect to database?
```bash
# Check if PostgreSQL is running
docker ps | findstr postgres
```

### Data not showing in Grafana?
1. Check PostgreSQL datasource in Grafana settings
2. Run test query: `SELECT COUNT(*) FROM fact_sales`
3. Verify credentials

### Airflow DAGs not showing?
1. Copy DAG files to `11-infrastructure/network/dags/`
2. Restart Airflow scheduler
3. Wait 2-3 minutes for parsing

---

## 📚 Documentation

- **Full Technical Guide:** [OPERATIONAL_SUMMARY.md](OPERATIONAL_SUMMARY.md)
- **Architecture Details:** [10-documentation/ARCHITECTURE.md](10-documentation/ARCHITECTURE.md)
- **Operations Guide:** [10-documentation/OPERATIONS.md](10-documentation/OPERATIONS.md)
- **Data Dictionary:** [01-warehouse-design/data-dictionary/warehouse_schema.md](01-warehouse-design/data-dictionary/warehouse_schema.md)

---

## ✅ What's Been Done

- ✅ Restructured entire codebase (9 phases)
- ✅ Created star schema warehouse
- ✅ Generated 57,231 sample records
- ✅ Set up 5 production-ready services
- ✅ Configured automated ETL pipeline
- ✅ Built real-time monitoring dashboard
- ✅ Implemented data quality checks
- ✅ Containerized everything with Docker

---

## 🎯 Next Milestone: AWS Deployment

Ready to go to production?

```bash
# In 09-deployment directory:
# 1. Configure AWS credentials
# 2. Update Terraform variables
# 3. Deploy infrastructure
# 4. Migrate data
# 5. Update DNS
```

See [09-deployment/AWS_DEPLOYMENT.md](09-deployment/AWS_DEPLOYMENT.md) for full guide.

---

## 🎉 You're All Set!

Your data pipeline is **operational, monitored, and ready for production**. 

**Start here:** [Grafana Dashboard](http://localhost:3000)  
**Admin commands:** [Airflow Console](http://localhost:8080)  
**Query data:** [pgAdmin](http://localhost:5050)

---

*Last Updated: 2026-02-28*  
*Status: ✅ Fully Operational*
