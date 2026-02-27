# Grafana Setup & Dashboard Provisioning Script

param(
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$GrafanaUser = "admin",
    [string]$GrafanaPassword = "admin"
)

Write-Host "Unilever Grafana Setup & Test" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Error { Write-Host "✗ $args" -ForegroundColor Red }
function Write-Info { Write-Host "ℹ $args" -ForegroundColor Blue }
function Write-Warn { Write-Host "⚠ $args" -ForegroundColor Yellow }

$grafanaDir = "08-monitoring-alerting/grafana"

Write-Info "Checking Grafana directory structure..."
$requiredDirs = @(
    "$grafanaDir/dashboards",
    "$grafanaDir/provisioning/dashboards",
    "$grafanaDir/provisioning/datasources"
)

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Success "Directory exists: $dir"
    } else {
        Write-Warn "Directory missing: $dir"
    }
}

Write-Info "Checking dashboard files..."
$dashboardFiles = Get-ChildItem "$grafanaDir/dashboards/*.json" -ErrorAction SilentlyContinue
if ($dashboardFiles.Count -gt 0) {
    Write-Success "Found $($dashboardFiles.Count) dashboard file(s)"
} else {
    Write-Warn "No dashboard files found"
}

Write-Info "Checking if Grafana is running..."
try {
    $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Success "Grafana is accessible at $GrafanaUrl"
    }
} catch {
    Write-Warn "Grafana not running - make sure to start containers first"
    Write-Warn "Command: docker-compose -f 11-infrastructure/network/docker-compose.yml up"
}

Write-Host ""
Write-Success "Grafana setup checks complete!"
Write-Host ""
Write-Host "Access Grafana at: $GrafanaUrl" -ForegroundColor Cyan
Write-Host "Default credentials: $GrafanaUser / $GrafanaPassword" -ForegroundColor Cyan
