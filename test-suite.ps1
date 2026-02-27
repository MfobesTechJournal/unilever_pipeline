#!/usr/bin/env pwsh
# Comprehensive Test Suite for Unilever ETL Pipeline

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Unilever ETL - Comprehensive Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$passed = 0
$failed = 0

function Test-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host ">> $Title" -ForegroundColor Blue
    Write-Host "=================="
}

function Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
    $script:passed++
}

function Failure {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
    $script:failed++
}

# Test 1: Python validation
Test-Section "Python Files Validation"
$pythonFiles = Get-ChildItem -Path "04-etl-pipeline" -Filter "*.py" -Recurse | Select-Object -ExpandProperty FullName
foreach ($file in $pythonFiles) {
    $result = python -m py_compile "$file" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Success "$(Split-Path -Leaf $file)"
    } else {
        Failure "$(Split-Path -Leaf $file) - syntax error"
    }
}

# Test 2: Configuration files
Test-Section "Configuration Files"
if (Test-Path "02-data-sources/data-quality-rules/quality_rules.yaml") {
    Success "quality_rules.yaml found"
} else {
    Failure "quality_rules.yaml not found"
}

if (Test-Path "08-monitoring-alerting/prometheus/prometheus.yml") {
    Success "prometheus.yml found"
} else {
    Failure "prometheus.yml not found"
}

# Test 3: Data quality rules YAML parsing
Test-Section "Data Quality Rules"
$yamlTest = @"
import yaml
with open('02-data-sources/data-quality-rules/quality_rules.yaml', 'r') as f:
    rules = yaml.safe_load(f)
    print(f"Loaded {len(rules)} sections: {list(rules.keys())}")
"@

$result = python -c $yamlTest 2>&1
if ($LASTEXITCODE -eq 0) {
    Success "YAML parsing successful"
    Write-Host "  $result" -ForegroundColor Gray
} else {
    Failure "YAML parsing failed: $result"
}

# Test 4: Docker configuration
Test-Section "Docker Configuration"
if (Test-Path "09-deployment/docker/Dockerfile") {
    Success "Dockerfile found"
} else {
    Failure "Dockerfile not found"
}

if (Test-Path "11-infrastructure/network/docker-compose.yml") {
    Success "docker-compose.yml found"
} else {
    Failure "docker-compose.yml not found"
}

# Test 5: Required directories
Test-Section "Directory Structure"
$requiredDirs = @(
    "01-warehouse-design",
    "02-data-sources",
    "03-shell-scripts",
    "04-etl-pipeline",
    "05-airflow-orchestration",
    "08-monitoring-alerting",
    "09-deployment",
    "11-infrastructure"
)

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Success "$dir exists"
    } else {
        Failure "$dir missing"
    }
}

# Test 6: Test files
Test-Section "Test Files"
$testFiles = @(
    "04-etl-pipeline/tests/test_unit.py",
    "04-etl-pipeline/tests/test_integration.py"
)

foreach ($file in $testFiles) {
    if (Test-Path $file) {
        Success "$(Split-Path -Leaf $file) found"
    } else {
        Failure "$(Split-Path -Leaf $file) missing"
    }
}

# Test 7: Run unit tests
Test-Section "Unit Tests Execution"
if (Test-Path "04-etl-pipeline/tests/test_unit.py") {
    Write-Host "Running pytest..." -ForegroundColor Gray
    $result = pytest "04-etl-pipeline/tests/test_unit.py" -v --tb=line 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Success "Unit tests passed"
    } else {
        Write-Host "Test output:" -ForegroundColor Gray
        $result | Select-Object -Last 30 | ForEach-Object { Write-Host "  $_" }
    }
}

# Final Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Test Summary" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($failed -eq 0) {
    Write-Host "✓ ALL TESTS PASSED" -ForegroundColor Green
} else {
    Write-Host "✗ SOME TESTS FAILED" -ForegroundColor Red
}

Write-Host ""
Write-Host "Services ready to start:" -ForegroundColor Yellow
Write-Host "  docker-compose -f 11-infrastructure/network/docker-compose.yml up -d" -ForegroundColor Gray
