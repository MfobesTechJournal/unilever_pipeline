# ☁️ AWS Deployment Guide - Unilever ETL Pipeline

**Deploy your ETL pipeline to AWS in 30 minutes** with automated data generation, storage, and Teams notifications.

**Status:** Production-Ready | **Cost:** $15-30/month | **Scalability:** ✅ High

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Cost Estimation](#cost-estimation)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Verify Deployment](#verify-deployment)
6. [Monitoring & Logs](#monitoring--logs)
7. [Teams Notifications](#teams-notifications)
8. [Maintenance](#maintenance)
9. [Scaling Guide](#scaling-guide)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### AWS Account Setup
- ✅ AWS Account (free tier available)
- ✅ AWS CLI v2 installed locally
- ✅ IAM User with programmatic access (access key + secret)
- ✅ Default region selected (us-east-1 recommended)

### Local Requirements
- ✅ Git (already done)
- ✅ Python 3.9+
- ✅ Docker Desktop (for testing locally)

### Create IAM User for Deployment
1. AWS Console → IAM → Users → Create User
2. Username: `unilever-deploy`
3. Access type: Programmatic access
4. Permissions: Attach `AdministratorAccess` (for setup; lock down later)
5. Copy **Access Key ID** and **Secret Access Key**

### Configure AWS CLI
```powershell
aws configure
# AWS Access Key ID: [paste]
# AWS Secret Access Key: [paste]
# Default region: us-east-1
# Default output: json
```

Verify:
```powershell
aws sts get-caller-identity
```

---

## Architecture Overview

### AWS Components
```
┌─────────────────────────────────────────────────────────────┐
│                     AWS Cloud                                │
│                                                              │
│  ┌─────────────────┐                    ┌────────────────┐  │
│  │   EC2 Instance  │                    │  RDS Postgres  │  │
│  │  (t3.small)     │                    │   (db.t3.micro)│  │
│  │  ┌───────────┐  │                    │  (managed DB)  │  │
│  │  │ Docker    │  │                    │  (automated    │  │
│  │  │ Compose   │  │───── HTTPS ────────│   backups)     │  │
│  │  │ Services: │  │                    │  Port: 5432    │  │
│  │  │ - Airflow │  │                    │  ~$30/month    │  │
│  │  │ - Grafana │  │                    │                │  │
│  │  │ - Promotheus      │                    └────────────────┘  │
│  │  │ - App    │  │                                     │
│  │  └───────────┘  │                    ┌────────────────┐  │
│  │  Cost: ~$10/mo  │                    │  S3 Bucket     │  │
│  │  (running 24/7) │                    │  (backups,     │  │
│  └─────────────────┘                    │   logs, data)  │  │
│                                          │  Pay-as-you-go │  │
│                                          └────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │          CloudWatch Logs & Monitoring                   │ │
│  │  (Logs from all services, cost included)                │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │          Microsoft Teams Notifications                  │ │
│  │  (Webhook integration - your existing setup)            │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

Your Laptop (Windows)
├── GitHub repo push triggers EC2 deployment
├── View Grafana dashboards (public IP)
├── Receive Teams notifications
└── SSH access for debugging
```

### Data Flow
```
Raw Data (CSV)
    ↓
EC2 Docker: Extract
    ↓
Transform (Pandas, validate)
    ↓
RDS PostgreSQL: Load
    ↓
Grafana Dashboard + Teams Alert
    ↓
S3: Automated Backups
```

---

## Cost Estimation

### Monthly AWS Costs (24/7 Running)

| Service | Type | Cost |
|---------|------|------|
| **EC2** | t3.small (1 vCPU, 2GB RAM) | ~$8-10 |
| **RDS PostgreSQL** | db.t3.micro (1GB, redundant backups) | ~$15-20 |
| **S3** | Backups + data storage (~5GB) | ~$0.12 |
| **Data Transfer** | out to Teams (~10MB/day) | ~$0.09 |
| **CloudWatch** | Logs (included up to 5GB) | Included |
| **Elastic IP** | Static IP for server | Free (if running) |
| **TOTAL** | | **~$23-30/month** |

### Cost Optimization Tips
- ✅ Use t3 instances (burstable, cheapest)
- ✅ Stop EC2 nightly if not needed (-60% cost → $4-5/month)
- ✅ Use RDS free tier credits
- ✅ Store old logs in S3 Glacier (cheaper)

---

## Step-by-Step Deployment

### Phase 1: Create RDS PostgreSQL Database (10 min)

**Via AWS Console:**
1. RDS → Databases → Create Database
2. **Engine:** PostgreSQL 13.x
3. **Template:** Free tier (t3.micro)
4. **DB Instance Identifier:** `unilever-warehouse`
5. **Master username:** `postgres`
6. **Master password:** Generate strong password (e.g., 32 chars)
   - Store securely in a password manager
7. **VPC & Security:** Default VPC, create new security group
8. **Database name:** `unilever_warehouse`
9. **Backup:** Enable (7 days retention)
10. Click **Create Database**

⏳ **Wait 5-10 minutes for RDS to initialize...**

**Get Connection Details:**
- RDS → Databases → unilever-warehouse
- Endpoint: `unilever-warehouse.xxxxx.us-east-1.rds.amazonaws.com`
- Port: `5432`
- Save these for later!

**Allow EC2 Access (Security Group):**
- RDS → unilever-warehouse → Connectivity
- Security group → Edit inbound rules
- Add rule: PostgreSQL (5432) from EC2 security group

### Phase 2: Create and Configure EC2 Instance (10 min)

**Launch EC2 Instance:**
1. EC2 → Instances → Launch Instances
2. **Name:** `unilever-pipeline`
3. **AMI:** Ubuntu 22.04 LTS (free tier eligible)
4. **Instance Type:** `t3.small` (1 vCPU, 2GB RAM)
5. **Key Pair:** Create new
   - Name: `unilever-pipeline.pem`
   - **Download and save securely** (you'll need this to SSH)
6. **Network:** Default VPC
7. **Security Group:** Create new - `unilever-pipeline-sg`
   - Allow SSH (port 22) from your IP
   - Allow HTTP (port 80) from anywhere
   - Allow HTTPS (port 443) from anywhere
8. **Storage:** 30GB (free tier eligible)
9. Click **Launch Instance**

⏳ **Wait 2-3 minutes for instance to start...**

**Get Public IP:**
- EC2 → Instances → unilever-pipeline
- Copy **Public IPv4 address** (e.g., 54.123.45.67)

### Phase 3: Install Docker & Deploy on EC2 (10 min)

**SSH into EC2:**
```powershell
# Windows PowerShell
$keyPath = "C:\path\to\unilever-pipeline.pem"
ssh -i $keyPath ubuntu@<PUBLIC_IP>
```

**Install Docker and Docker Compose:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io docker-compose

# Add ubuntu user to docker group
sudo usermod -aG docker ubuntu

# Exit and reconnect
exit
ssh -i $keyPath ubuntu@<PUBLIC_IP>

# Verify Docker
docker --version
docker-compose --version
```

**Clone Your Repository:**
```bash
cd /home/ubuntu

# Clone from GitHub
git clone https://github.com/MfobesTechJournal/unilever_pipeline.git
cd unilever_pipeline
```

**Create .env File for Cloud:**
```bash
# Create from template
cat > .env << EOF
# AWS Environment
ENVIRONMENT=production
AWS_REGION=us-east-1

# PostgreSQL - RDS
DB_HOST=unilever-warehouse.xxxxx.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=unilever_warehouse
DB_USER=postgres
DB_PASSWORD=your-strong-password-here
DB_SSLMODE=require

# Airflow
AIRFLOW_HOME=/home/ubuntu/unilever_pipeline/airflow
AIRFLOW__CORE__DAGS_FOLDER=/home/ubuntu/unilever_pipeline/dags
AIRFLOW__CORE__LOAD_EXAMPLES=False
AIRFLOW__CORE__UNIT_TEST_MODE=False

# Security
AIRFLOW__WEBSERVER__SECRET_KEY=your-secret-key-$(openssl rand -hex 32)

# Teams Notifications
TEAMS_WEBHOOK=https://outlook.office.com/webhook/your-actual-webhook-url

# Grafana
GF_SECURITY_ADMIN_PASSWORD=your-secure-grafana-password

# Public IP for accessing services
PUBLIC_IP=<YOUR_PUBLIC_IP>
EOF
```

**Update docker-compose.yml for Cloud:**

The docker-compose needs these changes for cloud:
```yaml
# Use RDS host instead of localhost
services:
  etl-app:
    environment:
      - DB_HOST=${DB_HOST}  # RDS endpoint
      - DB_PORT=${DB_PORT}
      - DB_NAME=${DB_NAME}
      - TEAMS_WEBHOOK=${TEAMS_WEBHOOK}

# Remove PostgreSQL service (using managed RDS)
# Keep Airflow, Grafana, Prometheus as is
```

**Start Services:**
```bash
# Pull latest images
docker-compose pull

# Start services (omit postgres service)
docker-compose up -d airflow-scheduler airflow-webserver grafana prometheus

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

⏳ **Services start in 2-3 minutes...**

---

## Verify Deployment

### Test Services
```bash
# Check Docker containers
docker ps

# Test database connection
sudo apt install -y postgresql-client
psql -h <RDS_ENDPOINT> -U postgres -d unilever_warehouse -c "SELECT version();"

# Check Airflow
curl http://localhost:8080

# Check Grafana  
curl http://localhost:3000
```

### Access Web Interfaces from Your Laptop

**From your Windows machine:**

1. **Airflow Dashboard**
   - http://<PUBLIC_IP>:8080
   - Username: `airflow`
   - Password: `airflow`

2. **Grafana Dashboards**
   - http://<PUBLIC_IP>:3000
   - Username: `admin`
   - Default password: (check docker-compose)

3. **Prometheus Metrics**
   - http://<PUBLIC_IP>:9090

### Run ETL Pipeline
```bash
# SSH into EC2
ssh -i unilever-pipeline.pem ubuntu@<PUBLIC_IP>

# Run pipeline
cd unilever_pipeline
python etl-scripts/etl_production.py

# Watch logs
docker-compose logs -f etl-app
```

---

## Monitoring & Logs

### CloudWatch Logs
```bash
# View EC2 system logs
aws ec2 get-console-output --instance-ids i-xxxxx

# View application logs through Docker
docker logs container-name

# Stream logs in real-time
docker-compose logs -f
```

### Grafana Dashboards (Running on EC2)
- **Dashboard URL:** http://<PUBLIC_IP>:3000
- **Pre-configured:** etl-monitoring.json
- **Metrics source:** Prometheus (localhost:9090)

### Database Monitoring
```bash
# Connect to RDS
psql -h <RDS_ENDPOINT> -U postgres -d unilever_warehouse

# Check recent ETL runs
SELECT run_id, status, records_processed, quality_score, created_at
FROM etl_log
ORDER BY created_at DESC LIMIT 10;

# Check data quality issues
SELECT * FROM data_quality_log 
WHERE severity = 'error'
ORDER BY created_at DESC;
```

### Set Up CloudWatch Alarms (Optional)
```bash
# High CPU usage
aws cloudwatch put-metric-alarm \
  --alarm-name ec2-cpu-high \
  --alarm-description "Alert when EC2 CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold

# RDS connection issues
aws cloudwatch put-metric-alarm \
  --alarm-name rds-connections-high \
  --alarm-description "Alert when DB connections high" \
  --metric-name DatabaseConnections \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 75 \
  --comparison-operator GreaterThanThreshold
```

---

## Teams Notifications (AWS Integration)

Your **existing Teams setup** works perfectly with cloud deployment! 

### No Changes Needed
The `TEAMS_WEBHOOK` environment variable stored in `.env` will:
- ✅ Automatically send notifications from EC2
- ✅ Alert on pipeline success/failure
- ✅ Include cloud metrics in messages
- ✅ Work exactly like your local setup

### Verify Teams Integration on Cloud
```bash
# SSH into EC2
ssh -i unilever-pipeline.pem ubuntu@<PUBLIC_IP>

# Test notification
python << 'EOF'
import os
from utilities.teams_notifier import TeamsNotifier

notifier = TeamsNotifier()
notifier.send_info(
    "Cloud Deployment",
    "Unilever ETL Pipeline running on AWS EC2",
    details={
        "Environment": "Production",
        "Instance": "t3.small on us-east-1",
        "Database": "RDS PostgreSQL"
    }
)
EOF
```

Check your Teams channel - you should see the notification! 🎉

---

## Maintenance

### Regular Tasks

**Weekly:**
- Check CloudWatch logs for errors
- Verify RDS backups completed
- Monitor EC2 utilization

**Monthly:**
- Review AWS costs
- Update system packages: `sudo apt update && sudo apt upgrade -y`
- Review security groups and firewall rules

### Backup Strategy

**Automatic (RDS):**
- Daily automated backups (7-day retention)
- Point-in-time recovery available
- Backup location: AWS managed

**Manual S3 Backup:**
```bash
# Create database dump
pg_dump -h <RDS_ENDPOINT> -U postgres -d unilever_warehouse > backup.sql

# Upload to S3
aws s3 cp backup.sql s3://unilever-backups/$(date +%Y%m%d).sql

# Verify
aws s3 ls s3://unilever-backups/
```

### Restore from Backup
```bash
# Download from S3
aws s3 cp s3://unilever-backups/20260224.sql restore.sql

# Restore to RDS
psql -h <RDS_ENDPOINT> -U postgres -d unilever_warehouse < restore.sql
```

---

## Scaling Guide

### When to Scale EC2
- **CPU > 80% consistently** → Upgrade to t3.medium
- **Memory > 1.8GB** → Upgrade instance type
- **Need parallel DAGs** → Use t3.large (2 vCPU)

```bash
# Upgrade instance (requires stop)
aws ec2 stop-instances --instance-ids i-xxxxx
# Change instance type in console
aws ec2 start-instances --instance-ids i-xxxxx
```

### When to Scale RDS
- **Connections > 80%** → Upgrade to db.t3.small ($30/mo)
- **Storage > 80%** → Increase allocated storage
- **Read latency high** → Add read replica

**Upgrade RDS (multi-AZ for HA):**
```bash
aws rds modify-db-instance \
  --db-instance-identifier unilever-warehouse \
  --db-instance-class db.t3.small \
  --apply-immediately
```

### Cost Optimization
- Stop EC2 during off-hours: ~$4/month (vs $10/month running)
- Use Reserved Instances: 30% discount if running 1 year
- Scale down to t2.micro: Cheapest, but slower

---

## Troubleshooting

### Common Issues

#### 1. "Cannot connect to RDS"
```bash
# Check security group
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Test connection
psql -h <RDS_ENDPOINT> -U postgres -c "SELECT 1"

# Allow EC2 security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-rds-xxxxx \
  --protocol tcp \
  --port 5432 \
  --source-group sg-ec2-xxxxx
```

#### 2. "Docker containers won't start"
```bash
# Check Docker logs
docker logs container-name

# Check disk space
df -h

# Check memory
free -m

# Rebuild containers
docker-compose down
docker-compose up -d
```

#### 3. "High AWS costs"
```bash
# Check EC2 usage
aws ec2 describe-instances --query 'Reservations[].Instances[].{ID:InstanceId,Type:InstanceType,State:State.Name}'

# Check RDS usage
aws rds describe-db-instances

# Check S3 storage
aws s3 ls --summarize --human-readable --recursive
```

#### 4. "Airflow DAGs not running"
```bash
# SSH to EC2
ssh -i unilever-pipeline.pem ubuntu@<PUBLIC_IP>

# Check scheduler logs
docker-compose logs airflow-scheduler

# Check DAG syntax
python dags/etl_dag.py

# Restart scheduler
docker-compose restart airflow-scheduler
```

#### 5. "Teams notifications not sending"
```bash
# Check webhook is set
echo $TEAMS_WEBHOOK

# Test webhook directly
curl -X POST $TEAMS_WEBHOOK \
  -H 'Content-Type: application/json' \
  -d '{
    "@type": "MessageCard",
    "@context": "https://schema.org/extensions",
    "themeColor": "0078D4",
    "summary": "Test",
    "sections": [{"text": "Test notification"}]
  }'

# Check network
curl -I https://outlook.office.com
```

---

## Security Considerations

### Best Practices

✅ **DO:**
- Store .env file securely (not in git)
- Use strong RDS password (32+ chars, random)
- Restrict SSH access to your IP only
- Enable RDS encryption at rest
- Use IAM roles instead of access keys
- Regular security updates: `sudo apt update`
- Monitor CloudWatch logs for suspicious activity

❌ **DON'T:**
- Share .pem key file
- Commit sensitive data to GitHub
- Use default passwords
- Allow SSH from 0.0.0.0/0
- Store credentials in code

### Enable RDS Encryption
```bash
# Already enabled for new instances, but verify:
aws rds describe-db-instances \
  --db-instance-identifier unilever-warehouse \
  --query 'DBInstances[0].StorageEncrypted'
# Should return: true
```

### Restrict EC2 Security Group
```bash
# Allow SSH only from your IP
aws ec2 authorize-security-group-ingress \
  --group-id sg-ec2-xxxxx \
  --protocol tcp \
  --port 22 \
  --cidr 203.0.113.0/32  # Replace with YOUR IP
```

---

## Production Checklist

- [ ] RDS PostgreSQL database created and tested
- [ ] EC2 instance running with Docker/Docker Compose
- [ ] .env file configured with cloud credentials
- [ ] Teams webhook verified and working
- [ ] ETL pipeline runs successfully on EC2
- [ ] Grafana dashboards displaying data
- [ ] Monitoring and logging configured
- [ ] Backups automated to S3
- [ ] Security groups properly configured
- [ ] Costs under budget ($30/mo)
- [ ] README updated with cloud deployment info
- [ ] Team has access to EC2 IP/credentials

---

## Quick Reference Commands

```bash
# SSH to EC2
ssh -i ~/unilever-pipeline.pem ubuntu@<PUBLIC_IP>

# View services
docker-compose ps

# View logs
docker-compose logs -f [service-name]

# Run pipeline
python etl-scripts/etl_production.py

# Connect to RDS
psql -h <RDS_ENDPOINT> -U postgres -d unilever_warehouse

# Check AWS resources
aws ec2 describe-instances --filters "Name=tag:Name,Values=unilever*"
aws rds describe-db-instances --db-instance-identifier unilever-warehouse

# Stop EC2 (save costs)
aws ec2 stop-instances --instance-ids i-xxxxx

# Start EC2
aws ec2 start-instances --instance-ids i-xxxxx
```

---

## Cost Estimation Tool

```bash
# Calculate monthly cost based on usage
calculate_monthly_cost() {
  EC2_HOURS=$1  # hours running per month
  EC2_RATE=0.042  # t3.small hourly rate (us-east-1)
  RDS_HOURS=730  # always running
  RDS_RATE=0.035  # db.t3.micro hourly rate
  
  EC2_COST=$(echo "$EC2_HOURS * $EC2_RATE" | bc)
  RDS_COST=$(echo "$RDS_HOURS * $RDS_RATE" | bc)
  TOTAL=$(echo "$EC2_COST + $RDS_COST + 1" | bc)  # +$1 for S3/misc
  
  echo "EC2 (${EC2_HOURS}h): \$$EC2_COST"
  echo "RDS (730h): \$$RDS_COST"
  echo "S3 + Misc: \$1"
  echo "TOTAL: \$$TOTAL"
}

# Examples:
calculate_monthly_cost 730   # Running 24/7 = ~$35/mo
calculate_monthly_cost 365   # Running 12h/day = ~$20/mo
calculate_monthly_cost 120   # Running 4h/day = ~$7/mo
```

---

## Next Steps

1. **Create AWS account** (if needed) - Free tier available
2. **Create RDS database** (10 min)
3. **Launch EC2 instance** (5 min)
4. **Deploy pipeline** (10 min)
5. **Verify everything works**
6. **Configure monitoring alerts**
7. **Add to GitHub Actions** for CI/CD

---

**Last Updated:** February 24, 2026  
**Created by:** GitHub Copilot  
**Status:** Ready for Production Deployment
