# CI/CD Pipeline Documentation

## Overview

This project uses GitHub Actions for continuous integration and deployment (CI/CD). The pipeline implements enterprise-grade practices including code quality checks, automated testing, security scanning, performance benchmarking, and automated deployment.

## Pipeline Architecture

```
Push/PR Event
    ↓
[Lint] ────→ Code Quality Checks (flake8, black, isort, safety)
    ↓
[Test] ────→ Unit & Integration Tests + Coverage
    ↓
[Docker Build] ─→ Build and cache Docker image
    ↓
[Security Scan] → Vulnerability scanning (Trivy)
    ↓
[Performance] ──→ Benchmark tests (main branch only)
    ↓
[Deploy] ────→ Deploy to staging (develop) or production (main)
    ↓
[Notify] ────→ Slack notifications
```

## Workflow Stages

### 1. **Lint Stage** (Always Runs)

**Purpose:** Enforce code quality and consistency standards

**Tools:**
- **flake8**: Python linter (PEP 8 compliance)
- **black**: Code formatter (automatic formatting check)
- **isort**: Import sorting (consistent import organization)
- **safety**: Dependency vulnerability checking

**Configuration:**
- Max line length: 127 characters
- Max complexity: 10 (McCabe complexity)
- Stops on syntax errors and undefined names

**Failure Conditions:**
- Syntax errors or undefined names
- Dependency vulnerabilities
- Incorrect import ordering

**Typical Errors & Fixes:**
```bash
# Format code automatically
black .

# Sort imports
isort .

# Check linting issues
flake8 . --show-source
```

### 2. **Test Stage** (Always Runs)

**Purpose:** Validate functionality through automated testing

**Components:**

#### Unit Tests (`tests/test_unit.py`)
- Isolated component testing
- No external dependencies
- Fast execution
- Tests:
  - Data quality checkers
  - Type conversions
  - Retry decorators
  - Parameter validation

#### Integration Tests (`tests/test_integration.py`)
- Full system workflows
- Database connectivity
- End-to-end pipeline execution
- Backup/restore functionality
- Airflow DAG validity

#### Performance Tests (`tests/test_performance.py`)
- Batch processing performance
- CSV I/O benchmarks
- Memory usage analysis
- Data aggregation speed
- Scaling behavior

**Coverage Requirements:**
- Minimum 70% code coverage
- Generated reports:
  - XML (for CI consumption)
  - HTML (for review)
  - Terminal output

**Running Tests Locally:**
```bash
# All tests
pytest

# Specific test file
pytest tests/test_unit.py -v

# Only fast tests (skip slow)
pytest -m "not slow" -v

# With coverage report
pytest --cov=. --cov-report=html

# Performance tests only
pytest tests/test_performance.py -v --benchmark-only

# Failing tests only
pytest --failed-last --maxfail=3
```

### 3. **Docker Build Stage** (Always Runs)

**Purpose:** Ensure Docker image can be built successfully

**Features:**
- Automatic caching for faster builds
- Multi-stage builds supported
- Image tagged with commit SHA
- Ready for registry push

**Configuration:**
```yaml
Context: .
Cache: GitHub Actions cache
Tags: unilever/etl:${SHA}
```

**Troubleshooting:**
```bash
# Build locally to test
docker build -t unilever/etl:local .

# Test image
docker run --rm unilever/etl:local python --version
```

### 4. **Security Scanning Stage** (Always Runs)

**Purpose:** Identify vulnerabilities in code and dependencies

**Tools:**
- **Trivy**: Container and filesystem scanning
  - Detects CVEs in dependencies
  - Scans Python packages
  - Reports severity levels

**Severity Levels:**
- **CRITICAL**: Immediate action required
- **HIGH**: Should be addressed soon
- **MEDIUM**: Monitor and plan fixes
- **LOW**: Track for future updates

**SARIF Output:** Results uploaded to GitHub Security tab for tracking

**Ignoring Vulnerabilities:**
```bash
# Create .trivyignore file
echo "CVE-2024-XXXXX" >> .trivyignore
```

### 5. **Performance Testing** (Main Branch Only)

**Purpose:** Track performance metrics over time

**Benchmarks:**
- CSV read/write performance
- Batch processing speed
- DataFrame merging efficiency
- Aggregation performance
- Query execution time

**Results Storage:**
- Stored in benchmark artifacts
- Trend tracking across commits
- Performance regression detection

**Local Benchmarking:**
```bash
pytest tests/test_performance.py -v --benchmark-only --benchmark-save=baseline
```

### 6. **Deploy Staging** (Develop Branch)

**Trigger:** Successful push to `develop` branch

**Deployment Steps:**
1. All previous stages pass
2. Deploy to staging environment
3. Run smoke tests
4. Verify all services healthy

**Environment:**
- Database: Staging PostgreSQL
- Services: All containers deployed
- Data: Test/non-production data only

### 7. **Deploy Production** (Main Branch)

**Trigger:** Successful push to `main` branch

**Requirements:**
- All stages pass
- Security scan passes
- Code review approved
- Tests coverage ≥70%

**Deployment Steps:**
1. Build and push Docker image
2. Deploy to production
3. Run health checks
4. Verify data integrity
5. Monitor for errors

**Rollback Procedure:**
```bash
# If issues detected
git revert <commit-sha>
git push origin main
# This will trigger deployment of previous version
```

### 8. **Notifications** (Always Runs)

**Slack Integration:**

Posts to Slack channel with:
- Build status (✅ success or ❌ failed)
- Branch and commit information
- Link to GitHub Actions logs

**Configuration:**
```yaml
webhook-url: ${{ secrets.SLACK_WEBHOOK }}
```

**Setup:**
1. Create Slack App
2. Generate webhook URL
3. Add to GitHub repository secrets as `SLACK_WEBHOOK`

## Environment Variables

### Required Secrets

All secrets must be configured in GitHub repository settings:

```
DATABASE_URL              # Production database connection
DATABASE_URL_STAGING      # Staging database connection
SLACK_WEBHOOK            # Slack notification webhook
DOCKER_REGISTRY_TOKEN   # Docker registry credentials
```

### Workflow Environment Variables

Defined in workflow file:

```yaml
PYTHON_VERSION: '3.9'
POSTGRES_VERSION: '14'
```

## Branch Strategy

### `main` Branch
- Production code
- Deployments trigger on push
- Requires PR review
- Tags: `v*` for releases

### `develop` Branch  
- Integration branch
- Staging deployments
- Nightly test runs
- Pre-release testing

### Feature Branches
- Branch from `develop`
- PR triggers full testing
- Merge back to `develop` when ready

## Schedule Triggers

**Every 6 Hours:**
```yaml
schedule:
  - cron: '0 */6 * * *'
```

Runs full test suite even without commits to catch:
- Dependency updates breaking code
- External API changes
- Environment drift

## Running Tests Locally

### Quick Start

```bash
# Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install pytest pytest-cov pytest-benchmark

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing
```

### Specific Test Scenarios

```bash
# Only unit tests (fast)
pytest tests/test_unit.py -v

# Only fast tests
pytest -m "not slow"

# Only database tests
pytest -m "database"

# Failed tests from last run
pytest --failed-last

# Stop after first failure
pytest -x

# Show print statements
pytest -s

# Run with specific markers
pytest -m "integration and not slow"
```

### Performance Testing

```bash
# Baseline benchmark
pytest tests/test_performance.py --benchmark-save=baseline

# Compare with baseline
pytest tests/test_performance.py --benchmark-compare=baseline

# Save to JSON
pytest tests/test_performance.py --benchmark-json=results.json
```

## Code Coverage

### Viewing Reports

**Terminal Output:**
```
Name                  Stmts   Miss  Cover   Missing
─────────────────────────────────────────────────
etl_production.py      200   15   92%     45-50, 120
etl_dag_production.py  150   8    94%     78-82
...
─────────────────────────────────────────────────
TOTAL                 1200   45   96%
```

**HTML Report:**
```bash
pytest --cov=. --cov-report=html
# Open: htmlcov/index.html
```

### Coverage Goals

- Minimum overall: 70%
- Critical modules: 85%+
- Exclusions:
  - Main entry points
  - Exception handlers (rare paths)
  - Debug code

## Troubleshooting

### Tests Fail Locally But Pass in CI

**Common Causes:**
1. Missing environment variables
2. Database not running
3. Port conflicts
4. Different Python version

**Solutions:**
```bash
# Check Python version
python --version  # Should be 3.9+

# Start services
docker-compose up -d postgres

# Set environment variables
export DATABASE_URL=postgresql://...

# Clear cache
pytest --cache-clear
```

### Docker Build Fails

**Check logs:**
```bash
docker build -t test . --verbose
```

**Common issues:**
- Base image not found
- Network issues
- Disk space

### Performance Tests Timeout

**Solutions:**
```bash
# Skip slow tests
pytest -m "not slow"

# Increase timeout
pytest --timeout=300

# Run benchmarks only
pytest tests/test_performance.py --benchmark-only
```

### Linting Failures

**Auto-fix issues:**
```bash
# Format code
black .

# Sort imports
isort .

# Check issues
flake8 . --show-source
```

## Best Practices

### 1. **Commit Messages**
```
[TYPE] Brief description

Detailed explanation of changes.
- Point 1
- Point 2

Fixes #123
```

Types: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`

### 2. **Pull Requests**
- Link to issue
- Describe changes
- Include test results
- Request reviewers

### 3. **Test Writing**
- One assertion per unit test
- Use fixtures for setup
- Name tests descriptively
- Handle cleanup

### 4. **Performance**
- Monitor benchmark trends
- Investigate regressions
- Set realistic thresholds
- Document baselines

### 5. **Security**
- Review dependency updates
- Keep secrets in GitHub secrets
- Scan before merge
- Follow OWASP guidelines

## Accessing Artifacts

### Coverage Reports
```
Build → Artifacts → coverage.xml or htmlcov/
```

### Benchmark Results
```
Build → Artifacts → benchmark_results/
```

### Docker Images
```
Stored in registry after successful build
Tag format: unilever/etl:${COMMIT_SHA}
```

## Advanced Configuration

### Adding New Tests

1. Create test file in `tests/` directory
2. Name: `test_*.py`
3. Add markers: `@pytest.mark.slow`, `@pytest.mark.integration`
4. Run locally: `pytest tests/test_newfile.py`

### Custom Markers

Define in `pytest.ini`:
```ini
[pytest]
markers =
    custom_name: description
```

Use in tests:
```python
@pytest.mark.custom_name
def test_something():
    pass
```

### Conditional Workflows

Skip stages based on conditions:
```yaml
if: github.event_name == 'push' && github.ref == 'refs/heads/main'
```

## Getting Help

### Local Debugging

```bash
# Verbose output
pytest -vv --tb=long

# PDB debugger
pytest --pdb

# Show captured output
pytest -s
```

### Workflow Logs

GitHub Actions runs → Select workflow → View logs

Look for:
- Job initialization
- Step output
- Error messages
- Artifact uploads

### Common Commands Reference

```bash
# Run specific test
pytest tests/test_file.py::TestClass::test_method

# Run tests matching pattern
pytest -k "pattern_name"

# Parallel execution
pytest -n auto

# Generate report
pytest --html=report.html

# Stop on first failure
pytest -x -v
```

## Migration Guide

### From Manual Testing to CI/CD

1. **Set up GitHub Actions secrets**
   - DATABASE_URL
   - SLACK_WEBHOOK
   - Registry credentials

2. **Write tests** for critical functionality

3. **Configure workflow** in `.github/workflows/`

4. **Protect main branch**
   - Require PR reviews
   - Require passing checks
   - Enforce branch protection

5. **Monitor and iterate**
   - Review metrics
   - Adjust thresholds
   - Document learnings

## Metrics & KPIs

**Success Criteria:**
- Pipeline success rate: >95%
- Test coverage: >70%
- Deploy frequency: Daily
- Mean time to recovery: <30 min
- Security scanning: 100% pass

**Monitoring:**
- GitHub Actions dashboard
- Slack notifications
- Metrics tracking
- Historical trends

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024 | Initial CI/CD setup with GitHub Actions, comprehensive testing, security scanning, and automated deployment |

---

**For questions or issues, contact the DevOps team.**
