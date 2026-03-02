# Streamlit Analytics Dashboard

## Overview

Interactive multi-page analytics dashboard built with Streamlit, providing real-time insights into the Unilever data warehouse. This dashboard connects directly to PostgreSQL and displays sales, customer, and product analytics with interactive visualizations.

## Features

✨ **6 Interactive Pages:**
- 🏠 **Home** - Overview and system status
- 📈 **Sales Analytics** - Revenue trends and category analysis
- 👥 **Customer Insights** - Segment analysis and top customers
- 🛍️ **Product Performance** - Top products and performance metrics
- 🔧 **System Health** - Service status and warehouse statistics
- 📚 **Documentation** - Project information and resources

✅ **Key Capabilities:**
- Real-time data queries from PostgreSQL warehouse
- Interactive Plotly visualizations
- 5-minute data caching for performance
- Service health monitoring
- Responsive design with custom styling
- Multi-dimensional analysis

## Installation

### Prerequisites
- Python 3.12+
- PostgreSQL 14+ running (via Docker or local)
- Active Unilever data pipeline setup

### Setup Steps

1. **Install Streamlit packages:**
```bash
pip install -r streamlit_requirements.txt
```

2. **Configure database connection** (optional, uses defaults):
Create `.env` file in project root:
```
DB_HOST=localhost
DB_PORT=5433
DB_NAME=unilever_warehouse
DB_USER=postgres
DB_PASSWORD=123456
```

3. **Ensure PostgreSQL is running:**
```bash
cd 11-infrastructure/network
docker-compose up -d
```

4. **Load sample data** (if not already loaded):
```bash
python load_sales_simple.py
```

## Usage

### Running the Dashboard

```bash
streamlit run streamlit_app.py
```

The dashboard will open at `http://localhost:8501`

### Dashboard Pages

#### 1. Home Page
- **System Overview:** Key metrics (revenue, transactions, customers, products)
- **Project Information:** Architecture and performance metrics
- **Quick Links:** Direct access to external services (Grafana, Airflow, pgAdmin)

#### 2. Sales Analytics
- **Revenue by Category:** Bar and pie charts showing category performance
- **Category Metrics:** Transaction counts and average order values
- **Daily Trend:** 90-day sales trend with revenue and transaction counts

#### 3. Customer Insights
- **Segment Analysis:** Performance by customer segment
- **Order Value Analysis:** Average order value by segment
- **Top 10 Customers:** High-value customer list

#### 4. Product Performance
- **Top 20 Products:** By revenue and units sold
- **Product Analytics:** Revenue and performance metrics
- **Category Trends:** Product category analysis

#### 5. System Health
- **Service Status:** Real-time status of all services (PostgreSQL, Grafana, Airflow, etc.)
- **Warehouse Statistics:** Record counts across tables
- **Data Freshness:** Last update timestamps

#### 6. Documentation
- Architecture overview
- Database schema information
- External service links
- Quick start guide

## Query Examples

### Total Sales Revenue
```sql
SELECT SUM(revenue) as total_revenue FROM fact_sales
```

### Revenue by Category
```sql
SELECT 
    dp.category,
    SUM(fs.revenue) as total_revenue,
    COUNT(*) as transaction_count
FROM fact_sales fs
JOIN dim_product dp ON fs.product_key = dp.product_key
GROUP BY dp.category
ORDER BY total_revenue DESC
```

### Daily Sales Trend
```sql
SELECT 
    dd.sale_date,
    SUM(fs.revenue) as daily_revenue,
    COUNT(*) as daily_transactions
FROM fact_sales fs
JOIN dim_date dd ON fs.date_key = dd.date_key
GROUP BY dd.sale_date
ORDER BY dd.sale_date
```

### Customer Segment Analysis
```sql
SELECT 
    dc.customer_segment,
    COUNT(DISTINCT dc.customer_key) as customer_count,
    SUM(fs.revenue) as segment_revenue
FROM fact_sales fs
JOIN dim_customer dc ON fs.customer_key = dc.customer_key
GROUP BY dc.customer_segment
```

## Architecture

### Components

```
Streamlit App
    ↓
PostgreSQL Connector
    ↓
Database Query Execution
    ↓
Data Processing (Pandas)
    ↓
Visualization (Plotly)
    ↓
Web Dashboard (Streamlit)
```

### Caching Strategy

- **Data Cache:** 5-minute TTL for query results
- **Resource Cache:** Database connection pooling
- **Performance:** Reduced query load on database

## Customization

### Adding a New Page

```python
def page_custom_analytics():
    """Custom analytics page"""
    st.header("📊 Custom Analysis")
    
    # Your custom content here
    query = """SELECT ... FROM ..."""
    df = execute_query(query)
    
    if df is not None:
        st.dataframe(df)

# Add to navigation in main()
page = st.sidebar.radio("Navigation", [
    ...
    "📊 Custom Analytics"
])

# Add route
elif "Custom Analytics" in page:
    page_custom_analytics()
```

### Modifying Visualizations

The dashboard uses Plotly for interactive charts. Customize with:

```python
fig = px.bar(df, x='category', y='revenue')
fig.update_layout(
    title="Custom Title",
    xaxis_title="X Axis",
    yaxis_title="Y Axis",
    height=400,
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)
```

## Performance Optimization

### Tips for Better Performance

1. **Set Appropriate Cache TTL:**
   - Fast-changing data: 1-2 minutes
   - Stable data: 10-30 minutes

2. **Query Optimization:**
   - Add indexes on frequently joined columns
   - Use LIMIT for large result sets
   - Filter by date range when possible

3. **Streamlit Optimization:**
   - Use `@st.cache_resource` for connections
   - Use `@st.cache_data` for query results
   - Avoid recomputing in loops

4. **Example Optimized Query:**
```python
@st.cache_data(ttl=600)  # 10 minute cache
def get_top_products(limit=20):
    query = f"""
    SELECT product_name, revenue
    FROM product_analytics
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
    ORDER BY revenue DESC
    LIMIT {limit}
    """
    return execute_query(query)
```

## Troubleshooting

### Issue: "Unable to connect to database"
**Solution:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Start containers if needed
cd 11-infrastructure/network
docker-compose up -d

# Test connection
psql -h localhost -p 5433 -U postgres
```

### Issue: "No data in dashboard"
**Solution:**
1. Verify data is loaded: `python load_sales_simple.py`
2. Check database: `psql -h localhost -p 5433 -U postgres -c "SELECT COUNT(*) FROM fact_sales"`
3. Clear cache: Delete `.streamlit/cache` folder

### Issue: "Slow dashboard performance"
**Solution:**
1. Increase cache TTL in code
2. Optimize SQL queries with EXPLAIN ANALYZE
3. Add database indexes
4. Reduce number of visible data rows

## Deployment

### Production Deployment

**Using Streamlit Cloud:**
1. Push code to GitHub
2. Deploy from Streamlit Cloud dashboard
3. Configure secrets for database credentials

**Using Docker:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY streamlit_requirements.txt .
RUN pip install -r streamlit_requirements.txt

COPY streamlit_app.py .
EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501"]
```

**Using Docker Compose:**
```yaml
streamlit:
  image: python:3.12-slim
  working_dir: /app
  volumes:
    - .:/app
  ports:
    - "8501:8501"
  environment:
    - DB_HOST=postgres
    - DB_PORT=5432
  command: bash -c "pip install -r streamlit_requirements.txt && streamlit run streamlit_app.py"
  depends_on:
    - postgres
```

## Configuration

### Environment Variables

```bash
# Database Connection
DB_HOST=localhost           # PostgreSQL host
DB_PORT=5433               # PostgreSQL port
DB_NAME=unilever_warehouse # Database name
DB_USER=postgres           # Database user
DB_PASSWORD=123456         # Database password

# Streamlit Settings
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_HEADLESS=true
```

### Streamlit Config

Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#667eea"
backgroundColor = "#f0f2f6"
secondaryBackgroundColor = "#e4e4f7"

[client]
showErrorDetails = true

[server]
maxUploadSize = 200
enableXsrfProtection = true
```

## Advanced Features

### Custom Metrics

```python
# Add custom metric definitions
def calculate_custom_metric(metric_name):
    query = f"SELECT calculate_{metric_name}()"
    return execute_query(query)
```

### Real-time Updates

```python
# Use st.write with streaming
import time
for i in range(10):
    st.write(f"Processing {i}...")
    time.sleep(0.5)
```

### Filtering & Parameters

```python
# Add filters
date_range = st.date_input("Select date range", [date(2024,1,1), date(2024,12,31)])
category = st.selectbox("Category", ["All", "Electronics", "Clothing"])

# Update query based on filters
where_clause = f"WHERE dd.sale_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'"
```

## Monitoring & Logging

The dashboard automatically logs:
- Query execution times
- Data cache hits/misses
- Error messages and exceptions
- User interactions

View logs in Streamlit terminal output.

## Support & Documentation

- **Project Documentation:** See TECHNICAL_REPORT.md
- **Database Schema:** See ERD_STAR_SCHEMA.md
- **Quick Start:** See QUICK_START.md
- **GitHub Issues:** https://github.com/MfobesTechJournal/unilever_pipeline/issues

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Mar 2, 2026 | Initial release with 6 pages and full analytics |

## License

This project is part of the Unilever Data Pipeline initiative.

## Author

Data Engineering Team  
Unilever Analytics Division
