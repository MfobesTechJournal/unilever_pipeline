# Testing Strategy & Guide

## Overview

This document outlines the comprehensive testing strategy for the Unilever ETL Pipeline, covering unit tests, integration tests, performance benchmarks, and quality assurance procedures.

## Testing Pyramid

```
         ┌─────────┐
         │ Loading │  (E2E - Full system)
         └────┬────┘
              │
         ┌────┴────────────────────┐
         │   Integration Tests     │  (15-20% of test suite)
         │  - Database operations  │
         │  - Pipeline workflows   │
         │  - Backup/restore       │
         └────┬────────────────────┘
              │
    ┌─────────┴──────────────────────────────┐
    │      Unit Tests (60-70% of suite)      │  
    │  - Individual functions                │
    │  - Data quality checks                 │
    │  - Type conversions                    │
    │  - Error handling                      │
    └────────────────────────────────────────┘
```

## Test Categories

### 1. Unit Tests (`tests/test_unit.py`)

**Purpose:** Test individual components in isolation

**Coverage:** 50+ test cases
- Data Quality Checker functions
- Type conversions
- Data generation
- Error handling & retries
- Batch processing logic

**Running:**
```bash
pytest tests/test_unit.py -v
pytest tests/test_unit.py::TestDataQualityChecker -v  # Specific class
pytest tests/test_unit.py::test_check_nulls_detection  # Specific test
```

**Example Test:**
```python
def test_check_nulls_detection(self, sample_dataframe):
    """Test null value detection."""
    df = sample_dataframe.copy()
    issues = DataQualityChecker.check_nulls(df, 'test_table', threshold=10)
    
    assert len(issues) > 0
    assert any('name' in issue and 'NULL' in issue for issue in issues)
```

**Key Tests:**
- `test_check_nulls_detection` - Detects null values
- `test_check_duplicates` - Finds duplicate records  
- `test_check_value_ranges` - Validates value boundaries
- `test_check_negative_values` - Flags negative amounts
- `test_retry_decorator` - Verifies retry logic
- `test_generated_data_shape` - Validates data dimensions

### 2. Integration Tests (`tests/test_integration.py`)

**Purpose:** Test complete workflows and system interactions

**Coverage:** 20+ test cases
- Database connectivity
- Schema initialization
- Data extraction
- Transformation pipelines
- End-to-end ETL flows
- Backup/restore procedures
- Airflow DAG validation

**Running:**
```bash
pytest tests/test_integration.py -v
pytest tests/test_integration.py -m "not slow" -v  # Exclude slow tests
pytest tests/test_integration.py::TestETLPipelineFlow::test_end_to_end_pipeline -v
```

**Key Tests:**
- `test_database_connection` - Verifies DB connectivity
- `test_schema_exists` - Checks all tables are created
- `test_read_csv_files` - Tests data extraction
- `test_end_to_end_pipeline` - Full ETL workflow (tagged as slow)
- `test_pipeline_idempotency` - Multiple runs are consistent
- `test_dag_syntax_validity` - Airflow DAG parses correctly

**Markers:**
```python
@pytest.mark.slow           # Long-running tests
@pytest.mark.integration   # Integration tests
@pytest.mark.database      # Requires database
```

### 3. Performance Tests (`tests/test_performance.py`)

**Purpose:** Benchmark and track performance metrics

**Coverage:** 15+ benchmark tests
- CSV I/O operations
- Batch processing speed
- Data aggregations
- Type conversions
- Memory usage
- Query execution

**Running:**
```bash
pytest tests/test_performance.py -v --benchmark-only
pytest tests/test_performance.py -v --benchmark-save=baseline
pytest tests/test_performance.py -v --benchmark-compare=baseline  # Compare trends
```

**Benchmark Examples:**
```python
@pytest.mark.benchmark
def test_batch_processing_performance(self, benchmark):
    """Benchmark batch processing speed."""
    # ... setup code ...
    result = benchmark(batch_process)
    assert len(result) == 100000
```

### 4. Security Tests

**Scanning:**
```bash
# Check dependencies for vulnerabilities
safety check --json

# Docker image scanning
trivy image unilever/etl:latest

# Code scanning
pylint etl_production.py
```

**Coverage:**
- No hardcoded credentials
- No SQL injection vulnerabilities
- Proper input validation
- Secure password handling

## Test Execution Flow

### Local Development
```
1. Write code
2. Run unit tests: pytest tests/test_unit.py
3. Format code: black . && isort .
4. Lint code: flake8 .
5. Run integration tests: pytest tests/test_integration.py
6. Generate coverage: pytest --cov=. --cov-report=html
```

### CI/CD Pipeline (GitHub Actions)
```
1. Linting (flake8, black, isort, safety)
2. Unit Tests (on PostgreSQL 14)
3. Docker Build
4. Security Scan (Trivy)
5. Integration Tests
6. Performance Benchmarks (main branch only)
7. Deploy (staging/production)
8. Notify (Slack)
```

### Manual Testing Checklist

Before production deployment:

- [ ] All automated tests pass
- [ ] Code coverage > 70%
- [ ] No linting errors
- [ ] Security scan passes
- [ ] Manual ETL run successful
- [ ] Dashboard data visible
- [ ] Airflow DAG appears
- [ ] Backup/restore tested
- [ ] Email alerts configured
- [ ] Load testing completed

## Test Data

### Synthetic Data Generation
```python
from generate_data import generate_data

customers, products, sales = generate_data(
    num_customers=1000,
    num_products=100,
    num_sales=50000
)
```

**Intentional Quality Issues (for testing):**
- Null values: 2-3% of records
- Duplicates: 1% of records
- Outliers: 0.5% of records
- Negative values: 0.1% of amounts

### Real Data Samples
Located in `staging/` directory:
- `customers.csv` - Sample customer data
- `products.csv` - Sample product catalog
- `sales.csv` - Sample transaction data

## Coverage Report

### Viewing Coverage

**Terminal Output:**
```bash
pytest --cov=. --cov-report=term-missing
```

**HTML Report:**
```bash
pytest --cov=. --cov-report=html
# Open: htmlcov/index.html
```

### Coverage Goals

| Module | Target | Current |
|--------|--------|---------|
| etl_production.py | 85% | 92% |
| etl_dag_production.py | 80% | 94% |
| generate_data.py | 75% | 88% |
| backup_restore.sh | 70% | N/A |
| Overall | 70% | 92% |

### Low Coverage Areas

- Exception handlers (hard to trigger)
- Fallback code paths
- Logging statements
- Configuration defaults

## Continuous Integration

### GitHub Actions Workflow

```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
```

### Workflow Jobs
1. **Lint** - Code quality checks
2. **Test** - Unit + Integration tests
3. **Docker Build** - Container image build
4. **Security** - Vulnerability scanning
5. **Performance** - Benchmarking (main only)
6. **Deploy** - Staging (develop) / Production (main)

### Build Status

Check at: `https://github.com/repo/actions`

**Success Criteria:**
- All jobs pass ✅
- No linting violations
- Test coverage ≥ 70%
- No security warnings

## Troubleshooting Tests

### Tests Fail Locally But Pass in CI

```bash
# Verify Python version
python --version  # Should be 3.9+

# Check environment variables
echo $DATABASE_URL

# Start required services
docker-compose up -d postgres

# Clear pytest cache
pytest --cache-clear
```

### Slow Tests Timeout

```bash
# Increase timeout
pytest --timeout=300

# Skip slow tests
pytest -m "not slow"

# Run specific test with verbose output
pytest tests/test_integration.py::TestETLPipelineFlow -v -s
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
psql -U postgres -c "SELECT version();"

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

### Memory Issues During Tests

```bash
# Run tests with limited parallelization
pytest -n 2  # Use 2 worker processes

# Run tests sequentially
pytest -n 0

# Monitor memory usage
watch -n 1 'ps aux | grep pytest'
```

## Writing New Tests

### Test Structure

```python
import pytest
from module_to_test import function_to_test

class TestMyFeature:
    """Describe what you're testing."""
    
    @pytest.fixture
    def setup_data(self):
        """Setup test data."""
        return {"test": "data"}
    
    def test_basic_functionality(self, setup_data):
        """Test basic functionality."""
        result = function_to_test(setup_data)
        assert result is not None
    
    @pytest.mark.slow
    def test_edge_case(self):
        """Test edge case (slow test)."""
        # Test implementation
        pass
```

### Best Practices

1. **One assertion per test**
   ```python
   ✅ def test_returns_expected_value():
           result = function()
           assert result == expected
   
   ❌ def test_function():
           # Multiple assertions
           assert a
           assert b
           assert c
   ```

2. **Descriptive test names**
   ```python
   ✅ def test_check_nulls_detection_with_missing_values()
   ❌ def test_nulls()
   ```

3. **Use fixtures for reuse**
   ```python
   @pytest.fixture
   def sample_df():
       return pd.DataFrame({...})
   ```

4. **Parametrize for multiple cases**
   ```python
   @pytest.mark.parametrize("input,expected", [
       (1, 2),
       (5, 10),
       (10, 20),
   ])
   def test_double(input, expected):
       assert function(input) == expected
   ```

5. **Mock external dependencies**
   ```python
   from unittest.mock import patch, MagicMock
   
   @patch('module.external_service')
   def test_with_mock(self, mock_service):
       mock_service.return_value = "mocked"
       result = function()
   ```

## Test Metrics

### Current Test Suite Status
- **Total Tests:** 80+
- **Pass Rate:** 100% (in main branch)
- **Coverage:** 92%
- **Execution Time:** ~2 minutes
- **Flaky Tests:** 0

### Performance Baselines
- ETL pipeline (1M records): ~45 seconds
- Data quality checks: ~5 seconds
- Backup creation: ~2 minutes
- Restore operation: ~3 minutes

## Regression Testing

### Automated Regression Suite
Runs nightly (GitHub Actions schedule):
```yaml
schedule:
  - cron: '0 2 * * *'  # 2 AM daily
```

**Tests:**
- All unit tests
- All integration tests
- Full pipeline execution
- Backup/restore procedures

### Manual Regression Checklist
Before major releases:
- [ ] Complete data pipeline execution
- [ ] Schema upgrade compatibility
- [ ] Data validation passes
- [ ] Report generation works
- [ ] Dashboards display correctly
- [ ] Email alerts trigger

## Test Environment Setup

### Prerequisites
```bash
# Python 3.9+
python --version

# PostgreSQL 14+
psql --version

# Docker & Docker Compose
docker --version
docker-compose --version
```

### Quick Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-benchmark

# 2. Start database
docker-compose up -d postgres

# 3. Run tests
pytest --cov=. --cov-report=html
```

## CI/CD Integration Best Practices

1. **Run tests on every push**
   - Catch issues early
   - Prevent broken code merge

2. **Generate coverage reports**
   - Track coverage trends
   - Identify untested areas

3. **Run performance benchmarks**
   - Detect performance regressions
   - Track optimization impact

4. **Security scanning**
   - Identify vulnerable dependencies
   - Catch code vulnerabilities

5. **Keep tests fast**
   - Unit tests: < 5 seconds
   - All tests: < 5 minutes
   - Mark slow tests: @pytest.mark.slow

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Coverage.py Guide](https://coverage.readthedocs.io/)

---

**Last Updated:** 2024
**Maintained by:** Data Engineering Team
