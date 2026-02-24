@echo off
REM Import ETL Monitoring Dashboard
echo Importing ETL Monitoring Dashboard...
curl -X POST "http://localhost:3000/api/dashboards/db" ^
  -H "Content-Type: application/json" ^
  -u "admin:admin" ^
  -d @grafana/dashboards/etl-monitoring.json

echo.
echo Importing Data Quality Dashboard...
curl -X POST "http://localhost:3000/api/dashboards/db" ^
  -H "Content-Type: application/json" ^
  -u "admin:admin" ^
  -d @grafana/dashboards/data-quality.json

echo.
echo Dashboard import complete!
