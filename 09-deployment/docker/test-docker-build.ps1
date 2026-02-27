# Docker Build & Test Script for Unilever ETL Pipeline
Write-Host "Unilever ETL Docker Test Suite" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Error { Write-Host "✗ $args" -ForegroundColor Red }
function Write-Info { Write-Host "ℹ $args" -ForegroundColor Blue }

Write-Info "Checking Docker installation..."
try {
    $dockerVersion = docker --version
    Write-Success "Docker found: $dockerVersion"
} catch {
    Write-Error "Docker not found"
    exit 1
}

Write-Info "Checking Dockerfile..."
if (Test-Path "09-deployment/docker/Dockerfile") {
    Write-Success "Dockerfile found"
} else {
    Write-Error "Dockerfile not found"
    exit 1
}

Write-Info "Checking Docker Compose files..."
$composeFiles = @(
    "11-infrastructure/network/docker-compose.yml",
    "09-deployment/docker-compose/docker-compose.cloud.yml"
)

foreach ($file in $composeFiles) {
    if (Test-Path $file) {
        Write-Success "Found: $file"
    } else {
        Write-Info "Optional: $file not found"
    }
}

Write-Host ""
Write-Success "All Docker checks passed!"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Build image: docker build -t unilever-etl:latest 09-deployment/docker" -ForegroundColor Yellow
Write-Host "2. Run compose: docker-compose -f 11-infrastructure/network/docker-compose.yml up" -ForegroundColor Yellow
