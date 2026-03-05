# Streamlit App Guide

This guide walks you through running and using the Streamlit analytics app for the Unilever SA Data Pipeline.

---

## Prerequisites

Before running Streamlit, make sure:

1. Docker containers are running (`docker ps` should show 6 containers)
2. Data is loaded (`fact_sales` has 2.5M rows)
3. You are in the pipeline folder with your virtual environment active

---

## Step 1: Install Streamlit dependencies

```bash
pip install -r streamlit_requirements.txt
```

If `streamlit_requirements.txt` doesn't exist, install manually:

```bash
pip install streamlit psycopg2-binary pandas plotly sqlalchemy
```

---

## Step 2: Verify database connection

Before launching, confirm the app can reach the database:

```bash
python -c "import psycopg2; conn = psycopg2.connect(host='localhost', port=5433, database='unilever_warehouse', user='postgres', password='123456'); print('Connected OK')"
```

You should see `Connected OK`. If not, make sure Docker is running and your local PostgreSQL service is stopped.

---

## Step 3: Launch the app

```bash
streamlit run streamlit_app.py
```

Streamlit will print something like:

```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

Open **http://localhost:8501** in your browser.

---

## Step 4: Using the app

The app has multiple pages accessible from the left sidebar:

### Home
- Overview of key metrics
- Total revenue, transactions, customers, products

### Sales
- Revenue by product category (bar chart)
- Daily revenue trend
- Filter by date range

### Customers
- Customer distribution by province
- Top customers by revenue
- Transaction frequency analysis

### Products
- Top performing products
- Revenue and quantity breakdown by brand
- Category comparison

### System Health
- ETL pipeline status
- Last run timestamp
- Data quality check results
- Record counts per table

---

## Step 5: Keeping it running

Streamlit runs in your terminal. To keep it running in the background on Windows:

```bash
Start-Process python -ArgumentList "-m streamlit run streamlit_app.py" -WindowStyle Hidden
```

Or just leave the terminal window open.

---

## Troubleshooting

**App shows no data:**
- Check Docker is running: `docker ps`
- Check data is loaded: `docker exec -it unilever_postgres psql -U postgres -d unilever_warehouse -c "SELECT COUNT(*) FROM fact_sales;"`
- Make sure local PostgreSQL is stopped (port conflict)

**Connection refused error:**
- Your local PostgreSQL may be conflicting on port 5433
- Run PowerShell as Administrator and stop it: `Stop-Service postgresql-x64-16 -Force`

**Module not found:**
- Make sure your virtual environment is active: look for `(venv)` at the start of your terminal prompt
- Re-run: `pip install -r streamlit_requirements.txt`

**Port 8501 already in use:**
- Run on a different port: `streamlit run streamlit_app.py --server.port 8502`

---

## Restarting after a machine reboot

Every time you restart your machine, do this in order:

```bash
# 1. Start Docker containers
cd "c:\Users\Mfobe Ntintelo\Documents\unilever_pipeline\11-infrastructure\network"
docker-compose up -d

# 2. Wait 20 seconds, then reload data
cd "c:\Users\Mfobe Ntintelo\Documents\unilever_pipeline"
python generate_unilever_data_v2.py
python load_etl_logs_final.py

# 3. Launch Streamlit
streamlit run streamlit_app.py
```

> Note: Data needs to be reloaded after restart because the Docker PostgreSQL container resets. This is a local dev setup — in production the database would persist.
