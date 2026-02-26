# Infrastructure & DevOps Guide

## Overview

This guide covers the complete infrastructure setup, deployment procedures, monitoring, and operations for the Unilever ETL Pipeline production environment.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions (CI/CD)                  │
│              (Code → Build → Test → Deploy)                │
└────────┬─────────────────────────────────┬─────────────────┘
         │                                 │
    ┌────▼────┐                    ┌──────▼──────┐
    │  Staging │                    │ Production  │
    │Environment                    │ Environment │
    └────┬────┘                    └──────┬──────┘
         │                                │
    ┌────▼──────────────────────────────▼────┐
    │    Docker Compose Services              │
    │  ┌─────────┐  ┌────────────┐           │
    │  │postgres │  │pgAdmin     │           │
    │  │  (DB)   │  │ (Console)  │           │
    │  └─────────┘  └────────────┘           │
    │  ┌─────────────────────────────┐       │
    │  │ Airflow (Orchestration)     │       │
    │  │ ├─ Webserver (UI)           │       │
    │  │ ├─ Scheduler (DAG runner)   │       │
    │  │ └─ Logs                     │       │
    │  └─────────────────────────────┘       │
    │  ┌──────────────────────────────┐      │
    │  │ Monitoring Stack             │      │
    │  │ ├─ Prometheus (metrics)      │      │
    │  │ └─ Grafana (dashboards)      │      │
    │  └──────────────────────────────┘      │
    └─────────────────────────────────────────┘
```

## Deployment Environments

### Development
- **Location:** Local machine or dev server
- **Database:** PostgreSQL 14 (local)
- **Services:** Docker Compose (all 6 containers)
- **Airflow:** LocalExecutor
- **Data:** Test/sample data only
- **Monitoring:** Basic Grafana dashboards

### Staging
- **Location:** Cloud/On-premises staging server
- **Database:** PostgreSQL 14 (managed/dedicated)
- **Services:** Docker Compose stack
- **Airflow:** LocalExecutor or CeleryExecutor
- **Data:** Real data (anonymized/sanitized)
- **Monitoring:** Full Grafana dashboards + Prometheus
- **SLA:** 99.5% availability
- **Backup:** Daily automated backups

### Production
- **Location:** Cloud/On-premises production cluster
- **Database:** PostgreSQL 14 HA cluster (replicated)
- **Services:** Kubernetes or Docker Swarm
- **Airflow:** CeleryExecutor or KubernetesExecutor
- **Data:** Full real data
- **Monitoring:** Complete observability stack
- **SLA:** 99.9% availability (4.3 hours downtime/month)
- **Backup:** Hourly automated backups + cross-region replication
- **Security:** TLS encryption, secrets management, WAF

## Docker Deployment

### Docker Compose Services

#### 1. PostgreSQL Database
```yaml
postgres:
  image: postgres:14-alpine
  container_name: unilever_postgres
  ports:
    - "5433:5432"
  environment:
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: ${DB_PASSWORD}
    POSTGRES_DB: unilever
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./setup_warehouse.sql:/docker-entrypoint-initdb.d/01-schema.sql
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 10s
    timeout: 5s
    retries: 5
```

**Features:**
- Persistent volume for data
- Auto-initialization with schema
- Health checks
- Network isolation

#### 2. pgAdmin (Database UI)
```yaml
pgadmin:
  image: dpage/pgadmin4:latest
  container_name: unilever_pgadmin
  ports:
    - "5050:80"
  environment:
    PGADMIN_DEFAULT_EMAIL: admin@example.com
    PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
  depends_on:
    - postgres
```

**Features:**
- Web-based database management
- Query execution
- Connection pooling

#### 3. Apache Airflow (Orchestration)

**Webserver:**
```yaml
airflow-webserver:
  image: puckel/docker-airflow:latest
  container_name: unilever_airflow_webserver
  ports:
    - "8080:8080"
  environment:
    AIRFLOW_HOME: /airflow
    AIRFLOW__CORE__DAGS_FOLDER: /airflow/dags
    AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql://...
    AIRFLOW__CORE__EXECUTOR: LocalExecutor
  volumes:
    - ./etl_dag.py:/airflow/dags/etl_dag.py
    - ./etl_dag_production.py:/airflow/dags/etl_dag_production.py
    - ./logs:/airflow/logs
  depends_on:
    - postgres
  command: webserver
```

**Scheduler:**
```yaml
airflow-scheduler:
  image: puckel/docker-airflow:latest
  container_name: unilever_airflow_scheduler
  environment:
    AIRFLOW_HOME: /airflow
    AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql://...
  volumes:
    - ./etl_dag.py:/airflow/dags/etl_dag.py
    - ./etl_dag_production.py:/airflow/dags/etl_dag_production.py
    - ./logs:/airflow/logs
  depends_on:
    - postgres
  command: scheduler
```

**Features:**
- DAG scheduling
- Task orchestration
- Retry logic
- Monitoring

#### 4. Prometheus (Metrics Collection)
```yaml
prometheus:
  image: prom/prometheus:latest
  container_name: unilever_prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus_data:/prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
```

**Configuration:**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'etl-metrics'
    static_configs:
      - targets: ['localhost:8000']
```

#### 5. Grafana (Dashboards)
```yaml
grafana:
  image: grafana/grafana:latest
  container_name: unilever_grafana
  ports:
    - "3000:3000"
  environment:
    GF_SECURITY_ADMIN_USER: admin
    GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
  volumes:
    - grafana_data:/var/lib/grafana
    - ./grafana/provisioning:/etc/grafana/provisioning
```

**Provisioning:**
- Auto-configure data sources
- Import dashboards on startup
- Dashboard templates

### Starting Services

```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d postgres
docker-compose up -d airflow-webserver

# View logs
docker-compose logs -f postgres

# Stop services
docker-compose down

# Remove volumes (reset data)
docker-compose down -v
```

### Health Checks

```bash
# Check all services
docker-compose ps

# Test database
docker-compose exec postgres pg_isready -U postgres

# Test Airflow
curl http://localhost:8080/api/v1/health

# Test Grafana
curl http://localhost:3000/api/health

# Test Prometheus
curl http://localhost:9090/-/healthy
```

## Kubernetes Deployment (Production)

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: unilever-etl-pipeline
  namespace: production
spec:
  replicas: 2
  selector:
    matchLabels:
      app: unilever-etl
  template:
    metadata:
      labels:
        app: unilever-etl
    spec:
      containers:
      - name: etl-pipeline
        image: unilever/etl:latest
        resources:
          limits:
            cpu: "1000m"
            memory: "2Gi"
          requests:
            cpu: "500m"
            memory: "1Gi"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: connection-string
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Database Service (Kubernetes)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: production
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: production
spec:
  serviceName: postgres-service
  replicas: 3  # High availability
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:14-alpine
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-password
              key: password
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
```

## Security & Secrets Management

### Environment Variables (Sensitive)

Store in `.env` or secrets manager:
```bash
DATABASE_URL=postgresql://user:password@host:port/db
AIRFLOW_FERNET_KEY=<generated-fernet-key>
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
SMTP_PASSWORD=smtp_app_password
```

### Kubernetes Secrets

```bash
# Create secret from literal values
kubectl create secret generic db-credentials \
  --from-literal=connection-string='postgresql://...'

# Create secret from file
kubectl create secret generic db-password \
  --from-file=password=./db-password.txt

# View secrets
kubectl get secrets
kubectl describe secret db-credentials
```

### Secret Rotation

```bash
# Rotate password (Docker)
docker-compose exec postgres alter user postgres with password 'new_password';

# Update environment
export DB_PASSWORD=new_password
docker-compose restart

# Kubernetes secret rotation
kubectl delete secret db-password
kubectl create secret generic db-password \
  --from-literal=password='new_password'
kubectl rollout restart deployment unilever-etl-pipeline
```

## Backup & Disaster Recovery

### Automated Backups

```bash
# Daily backup at 1 AM
# In .env or crontab
0 1 * * * cd /path/to/app && bash backup_restore.sh backup

# Weekly backup retention check
0 2 * * 0 bash backup_restore.sh cleanup
```

### Backup Strategy

- **RTO (Recovery Time Objective):** 30 minutes
- **RPO (Recovery Point Objective):** 24 hours
- **Retention Policy:** 30 days of daily backups + monthly archives
- **Location:** Local + cross-region replication (S3/GCS)

### Restore Procedure

```bash
# List available backups
bash backup_restore.sh list

# Validate backup integrity
bash backup_restore.sh validate

# Restore from specific backup
bash backup_restore.sh restore backups/backup_20240101_000000.sql.gz

# Restore to specific point in time
# (With WAL archiving enabled)
pg_restore -d unilever_new -Fc backups/backup.dump
```

## Monitoring & Alerting

### Metrics Collected

**System Metrics:**
- CPU usage
- Memory consumption
- Disk space
- Network I/O

**Application Metrics:**
- ETL pipeline duration
- Records processed
- Error rate
- Quality score

**Database Metrics:**
- Query performance
- Connection count
- Replication lag
- Cache hit ratio

### Alert Rules (Prometheus)

```yaml
groups:
- name: etl_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(etl_errors_total[5m]) > 0.05
    for: 5m
    annotations:
      summary: "High ETL error rate detected"
  
  - alert: LowDataQuality
    expr: etl_quality_score < 90
    for: 10m
    annotations:
      summary: "Data quality below threshold"
  
  - alert: DBConnectionPoolExhausted
    expr: db_connections_active >= db_connections_max
    for: 1m
    annotations:
      summary: "Database connection pool exhausted"
```

### Slack Notifications

```bash
# Configure in Airflow
AIRFLOW__CORE__SLACK_WEBHOOK_URL=$SLACK_WEBHOOK_URL

# Or in Python
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator

task = SlackWebhookOperator(
    task_id='notify_slack',
    http_conn_id='slack_webhook',
    message='ETL pipeline completed'
)
```

## Performance Tuning

### Database Optimization

```sql
-- Index optimization
CREATE INDEX idx_sales_date ON fact_sales(sale_date);
CREATE INDEX idx_customer_id ON fact_sales(customer_id);

-- Analyze query plans
EXPLAIN ANALYZE SELECT * FROM fact_sales;

-- Vacuum and analyze
VACUUM ANALYZE fact_sales;
```

### Connection Pooling (pgBouncer)

```ini
[databases]
unilever = host=postgres port=5432 dbname=unilever

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 5
```

### ETL Optimization

```python
# Use batch processing
BATCH_SIZE = 10000

# Connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10
)
```

## Scaling Strategies

### Horizontal Scaling

```yaml
# Kubernetes HPA (Horizontal Pod Autoscaling)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: etl-pipeline-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: unilever-etl-pipeline
  minReplicas: 2
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
```

### Vertical Scaling

```yaml
# Increase pod resources
resources:
  limits:
    cpu: "2000m"
    memory: "4Gi"
  requests:
    cpu: "1000m"
    memory: "2Gi"
```

### Database Scaling

```sql
-- Partitioning large fact tables
CREATE TABLE fact_sales_2024_q1 PARTITION OF fact_sales
  FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

-- Read replicas for reporting
-- Configure in PostgreSQL replication
```

## Maintenance Tasks

### Regular Maintenance

```bash
# Daily
- Monitor dashboards
- Check error logs
- Verify backup success

# Weekly
- Analyze performance trends
- Update dependencies
- Review security patches

# Monthly
- Disaster recovery drill
- Performance baseline review
- Capacity planning review
```

### Database Maintenance

```bash
# Update statistics
docker-compose exec postgres analyze

# Reindex tables
docker-compose exec postgres reindex database unilever

# Vacuum dead rows
docker-compose exec postgres vacuum analyze
```

## Troubleshooting

### Common Issues & Solutions

**Issue:** Services won't start
```bash
# Check port conflicts
lsof -i :5432
lsof -i :8080

# Low disk space
df -h

# Docker daemon issues
docker system df
docker system prune
```

**Issue:** Database connection failures
```bash
# Test connection
psql -U postgres -h localhost -d unilever

# Check credentials in .env
cat .env | grep DATABASE

# Reset permissions
docker-compose exec postgres chmod 700 /var/lib/postgresql/data
```

**Issue:** Airflow DAG not visible
```bash
# Check DAG file location
docker-compose exec airflow-webserver ls -la /airflow/dags/

# Validate DAG syntax
python -m py_compile etl_dag_production.py

# Restart scheduler
docker-compose restart airflow-scheduler
```

## Version Control & Release Management

### Git Workflow

```bash
# Feature branch
git checkout -b feature/new-feature
git commit -m "feat: implement new feature"
git push origin feature/new-feature
git pull request

# Release tag
git tag -a v1.0.1 -m "Release version 1.0.1"
git push origin v1.0.1
```

### Deployment Checklist

- [ ] Code review approved
- [ ] All tests pass
- [ ] Security scan passes
- [ ] Database migrations tested
- [ ] Backups verified
- [ ] Staging deployment successful
- [ ] Production deployment approved

## Disaster Recovery

### RTO/RPO Targets

- **RTO:** 30 minutes
- **RPO:** 24 hours
- **Maximum data loss:** < 1 day

### Recovery Procedure

1. **Assess situation** (2 min)
   - Identify failure type
   - Check backup integrity
   - Notify stakeholders

2. **Prepare recovery environment** (10 min)
   - Provision new database/servers
   - Update DNS/routing (if needed)

3. **Restore data** (15 min)
   - Restore from latest backup
   - Validate data integrity

4. **Verification & cutover** (3 min)
   - Verify services running
   - Switch traffic
   - Monitor closely

5. **Post-incident** (ongoing)
   - Root cause analysis
   - Update runbooks
   - Implement improvements

---

**Last Updated:** 2024
**Maintained by:** DevOps Team
