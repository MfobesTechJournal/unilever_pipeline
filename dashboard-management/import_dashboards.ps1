# Import Grafana Dashboards via PowerShell

$GrafanaUrl = "http://localhost:3000"
$Username = "admin"
$Password = "admin"
$Auth = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes("$($Username):$($Password)"))

$Headers = @{
    "Authorization" = "Basic $Auth"
    "Content-Type" = "application/json"
}

# Import ETL Monitoring Dashboard
Write-Host "Importing ETL Monitoring Dashboard..." -ForegroundColor Cyan
$dashboardPath = ".\grafana\dashboards\etl-monitoring.json"
$dashboardJson = Get-Content $dashboardPath -Raw | ConvertFrom-Json

$payload = @{
    dashboard = $dashboardJson
    overwrite = $true
    message = "Auto-imported ETL Monitoring dashboard"
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$GrafanaUrl/api/dashboards/db" `
        -Method POST `
        -Headers $Headers `
        -Body $payload
    Write-Host "✓ ETL Monitoring dashboard imported successfully" -ForegroundColor Green
    Write-Host "  Dashboard URL: $($response.url)" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to import ETL Monitoring dashboard" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""

# Import Data Quality Dashboard
Write-Host "Importing Data Quality Dashboard..." -ForegroundColor Cyan
$dashboardPath = ".\grafana\dashboards\data-quality.json"
$dashboardJson = Get-Content $dashboardPath -Raw | ConvertFrom-Json

$payload = @{
    dashboard = $dashboardJson
    overwrite = $true
    message = "Auto-imported Data Quality dashboard"
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$GrafanaUrl/api/dashboards/db" `
        -Method POST `
        -Headers $Headers `
        -Body $payload
    Write-Host "✓ Data Quality dashboard imported successfully" -ForegroundColor Green
    Write-Host "  Dashboard URL: $($response.url)" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to import Data Quality dashboard" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""
Write-Host "Dashboard import complete! Refresh your browser to see the dashboards." -ForegroundColor Yellow
