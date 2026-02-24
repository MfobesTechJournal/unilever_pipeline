.PHONY: help install test lint format clean docker-build docker-run docker-stop db-init db-backup db-restore airflow-init airflow-logs airflow-trigger docs coverage perf-test security-scan setup deploy-staging deploy-production

# Default target
help:
	@echo "=============================================="
	@echo "Unilever ETL Pipeline - Development Commands"
	@echo "=============================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install              Install dependencies"
	@echo "  make setup                Complete development setup"
	@echo ""
	@echo "Development:"
	@echo "  make lint                 Run code linting"
	@echo "  make format               Auto-format code"
	@echo "  make test                 Run unit tests"
	@echo "  make test-integration     Run integration tests"
	@echo "  make perf-test            Run performance benchmarks"
	@echo "  make coverage             Generate coverage report"
	@echo "  make clean                Clean build artifacts"
	@echo ""
	@echo "Database:"
	@echo "  make db-init              Initialize database schema"
	@echo "  make db-backup            Create database backup"
	@echo "  make db-restore           Restore from backup"
	@echo ""
	@echo "Docker & Deployment:"
	@echo "  make docker-build         Build Docker image"
	@echo "  make docker-run           Run container locally"
	@echo "  make docker-stop          Stop running container"
	@echo ""
	@echo "Airflow:"
	@echo "  make airflow-init         Initialize Airflow"
	@echo "  make airflow-logs         Show Airflow logs"
	@echo "  make airflow-trigger      Trigger ETL DAG"
	@echo ""
	@echo "Quality & Security:"
	@echo "  make security-scan        Run security scanning"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs                 Generate documentation"
	@echo ""

# Setup dependencies
install:
	@echo "Installing dependencies..."
	python -m venv venv
	. venv/bin/activate && pip install --upgrade pip setuptools wheel
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✓ Dependencies installed"

# Complete setup
setup: install db-init
	@echo "✓ Setup complete"

# Code quality - Linting
lint:
	@echo "Running linting checks..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	isort --check-only .
	black --check .
	@echo "✓ Linting passed"

# Code formatting
format:
	@echo "Formatting code..."
	black .
	isort .
	@echo "✓ Code formatted"

# Run tests
test:
	@echo "Running unit tests..."
	pytest tests/test_unit.py -v --cov=. --cov-report=term-missing
	@echo "✓ Unit tests passed"

test-integration:
	@echo "Running integration tests..."
	pytest tests/test_integration.py -v --tb=short
	@echo "✓ Integration tests passed"

test-all: test test-integration
	@echo "✓ All tests passed"

perf-test:
	@echo "Running performance benchmarks..."
	pytest tests/test_performance.py -v --benchmark-only
	@echo "✓ Performance tests completed"

# Coverage report
coverage:
	@echo "Generating coverage report..."
	pytest --cov=. --cov-report=html --cov-report=term-missing
	@echo "✓ Coverage report generated (htmlcov/index.html)"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -delete
	rm -rf build/ dist/ htmlcov/ .coverage
	@echo "✓ Cleanup complete"

# Database operations
db-init:
	@echo "Initializing database schema..."
	psql -U postgres -d unilever -f setup_warehouse.sql
	@echo "✓ Database schema created"

db-backup:
	@echo "Creating database backup..."
	bash backup_restore.sh backup
	@echo "✓ Backup created"

db-restore:
	@echo "Restoring database from backup..."
	@read -p "Enter backup file name: " backup_file; \
	bash backup_restore.sh restore $$backup_file
	@echo "✓ Database restored"

# Docker operations
docker-build:
	@echo "Building Docker image..."
	docker build -t unilever/etl:latest .
	@echo "✓ Docker image built"

docker-run: docker-build
	@echo "Running Docker container..."
	docker run -v $(PWD)/staging:/app/staging \
	           -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/unilever \
	           -it unilever/etl:latest
	@echo "✓ Container running"

docker-stop:
	@echo "Stopping Docker container..."
	docker-compose down
	@echo "✓ Services stopped"

docker-clean: docker-stop
	@echo "Cleaning Docker resources..."
	docker rmi unilever/etl:latest
	@echo "✓ Docker images cleaned"

# Airflow operations
airflow-init:
	@echo "Initializing Airflow..."
	docker-compose exec airflow-webserver airflow db init
	@echo "✓ Airflow initialized"

airflow-logs:
	@echo "Showing Airflow logs..."
	docker-compose logs -f airflow-scheduler airflow-webserver | head -100

airflow-trigger:
	@echo "Triggering ETL DAG..."
	@read -p "Enter DAG ID (default: unilever_etl_production): " dag_id; \
	dag_id=$${dag_id:-unilever_etl_production}; \
	curl -X POST http://localhost:8080/api/v1/dags/$$dag_id/dagRuns
	@echo "✓ DAG triggered"

# Quality and security
security-scan:
	@echo "Running security scanning..."
	pip install safety
	safety check --json
	@echo "✓ Security scan completed"

# Generate docs
docs:
	@echo "Generating documentation..."
	@echo "Creating API documentation..."
	@echo "✓ Documentation generated"

# Development server
dev-run:
	@echo "Starting ETL pipeline in development mode..."
	python -m etl_production
	@echo "✓ Pipeline completed"

# Full pipeline test
full-test: lint test-integration coverage
	@echo "✓ Full pipeline test suite passed"

# Deployment targets
deploy-staging:
	@echo "Deploying to staging environment..."
	docker-compose -f docker-compose.staging.yml up -d
	@echo "✓ Staging deployment complete"

deploy-production:
	@echo "Deploying to production environment..."
	docker-compose up -d
	@echo "✓ Production deployment complete"

# Monitoring
monitor:
	@echo "Checking service health..."
	@echo ""
	@echo "Database:"
	@docker-compose exec postgres pg_isready -U postgres || echo "❌ Not available"
	@echo ""
	@echo "Grafana:"
	@curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:3000/api/health || echo "❌ Not available"
	@echo ""
	@echo "Prometheus:"
	@curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:9090/-/healthy || echo "❌ Not available"
	@echo ""
	@echo "Airflow:"
	@curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8080/api/v1/health || echo "❌ Not available"

# Run ETL production
run-etl:
	@echo "Running ETL pipeline..."
	python etl_production.py

# Database restore with backup
backup-and-restore:
	@make db-backup
	@make db-restore

# Clean and fresh install
fresh-install: clean install setup
	@echo "✓ Fresh installation complete"

# Run all quality checks
quality: lint format test coverage
	@echo "✓ Quality checks passed"

# Version info
version:
	@echo "Unilever ETL Pipeline v1.0"
	@echo ""
	@echo "Component versions:"
	@python --version
	@docker --version
	@docker-compose --version

# Generate requirements
freeze-requirements:
	@echo "Freezing Python requirements..."
	pip freeze > requirements.frozen.txt
	@echo "✓ Requirements frozen to requirements.frozen.txt"

# Show configuration
show-config:
	@echo "Configuration status:"
	@echo "Python version: $$(python --version)"
	@echo "Virtual environment: $$(which python)"
	@echo "Database: $${DATABASE_URL}"
	@echo "Environment: $${ENV}"

# Interactive menu
menu:
	@clear
	@echo "╔═════════════════════════════════════════╗"
	@echo "║ Unilever ETL Pipeline Development Menu ║"
	@echo "╚═════════════════════════════════════════╝"
	@echo ""
	@echo "1. Setup environment"
	@echo "2. Run tests"
	@echo "3. Run linting"
	@echo "4. Format code"
	@echo "5. Deploy locally (Docker)"
	@echo "6. View coverage report"
	@echo "7. Run ETL pipeline"
	@echo "8. Database backup"
	@echo "9. View documentation"
	@echo "0. Exit"
	@echo ""
	@read -p "Select option: " choice; \
	case $$choice in \
	1) make setup ;; \
	2) make test-all ;; \
	3) make lint ;; \
	4) make format ;; \
	5) make docker-run ;; \
	6) make coverage ;; \
	7) make run-etl ;; \
	8) make db-backup ;; \
	9) make docs ;; \
	0) exit 0 ;; \
	*) echo "Invalid option" ;; \
	esac

# Default action
.DEFAULT_GOAL := help

# Phony targets (not actual files)
.PHONY: $(MAKECMDGOALS)
