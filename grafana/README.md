# Grafana Dashboards

This directory contains Grafana dashboards for monitoring the Unilever ETL Pipeline.

## Available Dashboards

### 1. ETL Pipeline Monitoring (`etl-monitoring.json`)
Monitors the core ETL pipeline operations:
- **ETL Processing Time**: Shows execution time trends over the last 7 days
- **ETL Run Status Distribution**: Pie chart of successful vs failed runs (30-day window)
- **Records Loaded by Type**: Bar chart showing products, customers, dates, and facts loaded
- **Data Quality Issues**: Trends in quality issues detected over time
- **Recent ETL Runs**: Table of the last 20 runs with details

**Key Metrics:**
- Processing duration (seconds)
- Success/failure ratio
- Record counts per load
- Data quality issue counts

### 2. Data Quality Monitoring (`data-quality.json`)
Focuses on data quality metrics and issue tracking:
- **24-Hour Issue Stats**: Quick stat cards showing:
  - Null values count
  - Duplicate records count
  - Outlier records count
  - Negative value records count

- **Quality Issues Over Time**: Time series chart tracking all issue types
- **Issue Distribution**: Pie chart showing breakdown of issue types
- **Recent Issues**: Detailed table of the last 100 quality issues

**Alert Thresholds:**
- Red alert at 100+ null values
- Red alert at 50+ duplicates
- Red alert at 10+ outliers
- Red alert at 5+ negative values

## Installing Dashboards

### Option 1: Using Docker Compose (Recommended)
The dashboards are automatically provisioned when using `docker-compose up`:

```bash
docker-compose up -d grafana
```

Grafana will automatically load all dashboards from the `provisioning/` directory.

### Option 2: Manual Import in Grafana UI

1. Open Grafana: http://localhost:3000
2. Login with default credentials: admin/admin
3. Go to **Dashboards** → **Import**
4. Upload JSON file or paste content from `dashboards/*.json`
5. Select PostgreSQL as the data source
6. Click **Import**

### Option 3: Using Grafana API

```bash
# Export and import dashboard via API
curl -X POST \
  -H "Content-Type: application/json" \
  -d @grafana/dashboards/etl-monitoring.json \
  http://admin:admin@localhost:3000/api/dashboards/db
```

## Configuring Data Sources

### Prerequisites
- PostgreSQL must be running with the Unilever data warehouse schema
- Database credentials: postgres/123456 (configured in .env)

### Automatic Configuration
When using Docker Compose, data sources are automatically provisioned:
- **PostgreSQL**: Connected to postgres:5432
- **Prometheus**: Connected to prometheus:9090

### Manual Configuration
If using Docker Compose without automatic provisioning:

1. Go to **Configuration** → **Data Sources**
2. Click **Add Data Source**
3. Select **PostgreSQL**
4. Configure:
   - **Name**: PostgreSQL
   - **Host**: postgres:5432 (or localhost:5433 if not using Docker)
   - **Database**: unilever_warehouse
   - **User**: postgres
   - **Password**: 123456
   - **SSL Mode**: disable
5. Click **Save & Test**

## Dashboard Variables

Dashboards support the following time ranges:
- Last 7 days (ETL Processing Time)
- Last 30 days (Status distribution, Records loaded, Quality issues)
- Configurable in dashboard settings

To modify the time range:
1. Click the time picker in the top right
2. Select desired range or enter custom dates

## Customizing Dashboards

### Adding New Panels

1. Open dashboard in edit mode
2. Click **Add Panel**
3. Configure PostgreSQL query using the etl_log or data_quality_log tables
4. Example query:
```sql
SELECT
  start_time AS time,
  COUNT(*) as run_count
FROM etl_log
WHERE status = 'SUCCESS'
  AND start_time > NOW() - INTERVAL '30 days'
GROUP BY DATE(start_time)
ORDER BY start_time
```

### Modifying Thresholds

1. Edit dashboard
2. Click panel
3. Go to **Field** tab
4. Adjust **Thresholds** section
5. Set desired alert colors and values

### Adding Alerts

1. Edit dashboard panel
2. Go to **Alert** tab
3. Configure alert rules
4. Set notification channels (email, Slack, etc.)

## Query Examples

### Successful Runs Last 7 Days
```sql
SELECT COUNT(*) as successful_runs
FROM etl_log
WHERE status = 'SUCCESS'
  AND start_time > NOW() - INTERVAL '7 days'
```

### Average Processing Time
```sql
SELECT 
  AVG(EXTRACT(EPOCH FROM (end_time - start_time))) as avg_duration_seconds
FROM etl_log
WHERE status = 'SUCCESS'
  AND start_time > NOW() - INTERVAL '30 days'
```

### Data Quality Score
```sql
SELECT 
  100 * (1 - (SUM(issue_count)::FLOAT / (SELECT COUNT(*) FROM fact_sales))) as quality_score
FROM data_quality_log
WHERE timestamp > NOW() - INTERVAL '24 hours'
```

### Failed Runs with Errors
```sql
SELECT
  run_id,
  start_time,
  error_message
FROM etl_log
WHERE status = 'FAILURE'
  AND start_time > NOW() - INTERVAL '7 days'
ORDER BY start_time DESC
```

## Troubleshooting

### Dashboards Not Loading
1. Check PostgreSQL is running: `docker ps | grep postgres`
2. Verify database connection in Grafana: Configuration → Data Sources
3. Check logs: `docker-compose logs grafana`

### Out of Data
1. Ensure ETL pipeline is running: `python etl_load_staging.py`
2. Check for errors in `etl_log` table
3. Verify data is being generated: `SELECT COUNT(*) FROM fact_sales`

### Query Errors
1. Check table schema: `\dt` in PostgreSQL
2. Verify column names in queries
3. Test query directly in PostgreSQL:
```sql
SELECT * FROM etl_log LIMIT 1;
SELECT * FROM data_quality_log LIMIT 1;
```

### Performance Issues
1. Add indexes to frequently queried columns
2. Partition data by date (already configured)
3. Adjust dashboard refresh rate in dashboard settings

## Dashboard Refresh Rates

Current refresh rates:
- **ETL Monitoring**: 30 seconds
- **Data Quality**: 30 seconds

To adjust:
1. Edit dashboard
2. Click dashboard settings (gear icon)
3. Modify "Refresh Rate"

## Exporting Dashboards

### Export to JSON
```bash
# Via API
curl http://admin:admin@localhost:3000/api/dashboards/uid/unilever-etl-dashboard > my-dashboard.json

# Or via UI:
# Dashboard menu → Export → Save JSON
```

### Sharing Dashboards
1. Click dashboard menu (top right)
2. Select **Share**
3. Choose sharing option (public URL, embed, etc.)

## Integration with CI/CD

To version control dashboard changes:

```bash
# Export all dashboards
for dashboard in etl-monitoring data-quality; do
  curl http://admin:admin@localhost:3000/api/dashboards/uid/$dashboard > grafana/dashboards/$dashboard.json
done

# Commit to Git
git add grafana/dashboards/
git commit -m "Update Grafana dashboards"
```

---

For more information, see the main [README.md](../../README.md) and [OPERATIONS.md](../../OPERATIONS.md).
