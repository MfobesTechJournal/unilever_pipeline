# 📢 Microsoft Teams Notifications Setup
**Project:** Unilever ETL Pipeline & Data Warehouse
**Component:** Pipeline Success/Failure Alerting System
**Created:** February 24, 2026

---

## 1️⃣ Overview

This document explains how to configure Microsoft Teams notifications for the Unilever ETL Pipeline.

The notification system sends alerts to a Microsoft Teams channel when:
- ✅ ETL pipeline starts
- ✅ Data ingestion completes successfully
- ✅ Data quality checks pass
- ❌ An ingestion/transformation error occurs
- ❌ Data quality violations detected
- ⏳ Pipeline is in progress
- ⚠️ Performance warnings triggered

Microsoft Teams uses an **Incoming Webhook URL** as the authentication mechanism (not username/password).

---

## 2️⃣ Creating a Microsoft Teams Incoming Webhook

### Step 1: Open Microsoft Teams
- Navigate to the desired **Team**
- Select the appropriate **Channel** where you want pipeline alerts
- Example channel names:
  - `#etl-pipeline-alerts`
  - `#data-warehouse-monitoring`
  - `#production-incidents`

### Step 2: Configure Incoming Webhook
1. Click the **⋯** (three dots) next to the channel name
2. Select **Connectors**
3. Search for **"Incoming Webhook"**
4. Click **Add** or **Configure**
5. Provide a **Name** (e.g., "Unilever ETL Pipeline Alerts")
6. Optionally upload an image for the bot avatar
7. Click **Create**
8. **Copy the generated Webhook URL**

### Example Webhook URL Format:
```
https://outlook.office.com/webhook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx@xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/IncomingWebhook/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

⚠️ **CRITICAL:** This URL is a secret credential. **Do NOT share or commit it to version control.**

---

## 3️⃣ Secure Credential Storage (Recommended Approach)

### Option A – Environment Variables (Permanent - Recommended for Production)

#### **Windows PowerShell (Recommended)**
Run in PowerShell as Administrator:

```powershell
[System.Environment]::SetEnvironmentVariable(
  "TEAMS_WEBHOOK",
  "https://outlook.office.com/webhook/your-real-url-here",
  "User"
)
```

**After executing, restart PowerShell or VS Code for changes to take effect.**

Verify the variable is set:
```powershell
$env:TEAMS_WEBHOOK
```

#### **Windows Command Prompt (CMD)**
```cmd
setx TEAMS_WEBHOOK "https://outlook.office.com/webhook/your-real-url-here"
```

#### **Linux/macOS (Bash/Zsh)**
Add to `~/.bashrc` or `~/.zshrc`:
```bash
export TEAMS_WEBHOOK="https://outlook.office.com/webhook/your-real-url-here"
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

### Option B – .env File (For Development)

Create `.env` file in the project root:

```bash
TEAMS_WEBHOOK=https://outlook.office.com/webhook/your-real-url-here
```

**Add to .gitignore:**
```
.env
.env.local
.env.*.local
```

**Load in Python (automatic with python-dotenv):**
```python
from dotenv import load_dotenv
load_dotenv()  # Loads from .env automatically
```

---

## 4️⃣ Python Implementation: teams_notifier.py

The `utilities/teams_notifier.py` module provides a clean interface for sending notifications.

### Basic Usage:

```python
from utilities.teams_notifier import TeamsNotifier

# Initialize notifier (reads from TEAMS_WEBHOOK env var)
notifier = TeamsNotifier()

# Send success notification
notifier.send_success(
    pipeline="ETL Pipeline",
    message="Daily data ingestion and transformation completed successfully",
    details={
        "Records Inserted": "55,550",
        "Duration": "2m 34s",
        "Data Quality Score": "98.5%"
    }
)

# Send failure notification
notifier.send_failure(
    pipeline="ETL Pipeline",
    message="Data quality check failed during transformation",
    error_details="Duplicate records detected in sales_fact table",
    details={
        "Pipeline": "etl_dag_production",
        "Task": "data_quality_check",
        "Duplicate Count": "245"
    }
)

# Send warning notification
notifier.send_warning(
    pipeline="Database Optimization",
    message="Slow query detected",
    details={
        "Query Duration": "45s (threshold: 30s)",
        "Recommendation": "Create composite index"
    }
)
```

### Notification Types:
- **`send_success()`** - ✅ Pipeline completed successfully
- **`send_failure()`** - ❌ Pipeline failed with error details
- **`send_warning()`** - ⚠️ Non-critical issues detected
- **`send_info()`** - ℹ️ Informational messages
- **`send_in_progress()`** - ⏳ Pipeline is running

---

## 5️⃣ Integration with Existing Scripts

### Example 1: ETL Pipeline Script (etl-scripts/run_pipeline.py)

```python
import sys
from pathlib import Path
from utilities.teams_notifier import TeamsNotifier
from etl_production import run_etl_pipeline

def main():
    notifier = TeamsNotifier()
    
    try:
        notifier.send_in_progress(
            "Unilever ETL Pipeline",
            "Starting daily data ingestion and transformation...",
            details={"Timestamp": "2026-02-24 10:00:00"}
        )
        
        # Run your ETL pipeline
        result = run_etl_pipeline()
        
        # Send success notification
        notifier.send_success(
            "Unilever ETL Pipeline",
            f"Pipeline completed successfully",
            details={
                "Records Processed": f"{result['total_records']:,}",
                "Duration": f"{result['duration']:.2f}s",
                "Quality Score": f"{result['quality_score']:.1f}%"
            }
        )
        
    except Exception as e:
        # Send failure notification
        notifier.send_failure(
            "Unilever ETL Pipeline",
            "Pipeline failed during execution",
            error_details=str(e),
            details={
                "Error Type": type(e).__name__,
                "Pipeline Stage": "data_transformation"
            }
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Example 2: Apache Airflow DAG (airflow-dags/etl_dag.py)

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from utilities.teams_notifier import TeamsNotifier

notifier = TeamsNotifier()

def on_success_callback(context):
    """Called when task succeeds."""
    task_instance = context['task_instance']
    notifier.send_success(
        "Unilever ETL Pipeline",
        f"Task '{task_instance.task_id}' completed successfully",
        details={
            "DAG": context['dag'].dag_id,
            "Execution Date": context['execution_date'].strftime("%Y-%m-%d %H:%M:%S")
        }
    )

def on_failure_callback(context):
    """Called when task fails."""
    task_instance = context['task_instance']
    exception = context.get('exception', 'Unknown error')
    
    notifier.send_failure(
        "Unilever ETL Pipeline",
        f"Task '{task_instance.task_id}' failed",
        error_details=str(exception),
        details={
            "DAG": context['dag'].dag_id,
            "Retry Number": task_instance.try_number
        }
    )

default_args = {
    'owner': 'data-engineering',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'on_failure_callback': on_failure_callback,
    'on_success_callback': on_success_callback,
}

with DAG(
    'unilever_etl_pipeline',
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval='0 2 * * *',  # 2 AM daily
) as dag:
    
    # Your tasks here
    pass
```

### Example 3: Monitoring Script (monitoring/monitor_etl.py)

```python
from utilities.teams_notifier import TeamsNotifier
import psycopg2

def check_data_quality():
    """Check data quality and send notifications."""
    notifier = TeamsNotifier()
    
    try:
        # Get data quality metrics
        conn = psycopg2.connect(
            host="localhost",
            database="unilever_warehouse",
            user="etl_user",
            password="secure_password",
            port=5433
        )
        cursor = conn.cursor()
        
        # Check for duplicates
        cursor.execute("""
            SELECT COUNT(*) as duplicate_count 
            FROM fact_sales 
            GROUP BY customer_id, product_id, sale_date 
            HAVING COUNT(*) > 1
        """)
        
        duplicate_count = sum(row[0] for row in cursor.fetchall())
        
        if duplicate_count > 0:
            notifier.send_warning(
                "Data Quality Monitor",
                f"Potential duplicates detected in fact_sales table",
                details={"Duplicate Count": duplicate_count}
            )
        else:
            notifier.send_success(
                "Data Quality Monitor",
                "All data quality checks passed",
                details={
                    "Fact Records": "55,550",
                    "Duplicate Issues": "0",
                    "Check Time": "3.4s"
                }
            )
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        notifier.send_failure(
            "Data Quality Monitor",
            "Quality check failed",
            error_details=str(e)
        )
```

---

## 6️⃣ Directory Structure

```
unilever_pipeline/
│
├── utilities/
│   ├── teams_notifier.py          ← Teams notification module
│   └── __init__.py
│
├── etl-scripts/
│   ├── run_pipeline.py            ← Integrated with notifications
│   ├── etl_dag_production.py
│   └── etl_production.py
│
├── airflow-dags/
│   ├── etl_dag.py                 ← Integrated with Airflow callbacks
│   └── etl_load_staging.py
│
├── monitoring/
│   ├── monitor_etl.py             ← Integrated with quality checks
│   └── __init__.py
│
├── .env                           ← Not committed to GitHub
├── .gitignore                     ← Add .env to ignore
└── TEAMS_NOTIFICATIONS.md         ← This file
```

---

## 7️⃣ Security Best Practices

### ✅ DO:
- ✅ Store webhook URLs in environment variables
- ✅ Add `.env` files to `.gitignore`
- ✅ Rotate webhook URLs if accidentally exposed
- ✅ Use HTTPS-only connections
- ✅ Test notifications in dev/staging before production
- ✅ Log notification success/failure for auditing

### ❌ DON'T:
- ❌ Hardcode webhook URLs in Python scripts
- ❌ Commit webhook URLs to GitHub
- ❌ Share webhook URLs via email or chat
- ❌ Use webhook URLs in logs or error messages
- ❌ Pass URLs as command-line arguments
- ❌ Store URLs in plaintext config files (unless in .gitignore)

---

## 8️⃣ Testing the Integration

### Test 1: Direct Python Test
```bash
cd c:\Users\Mfobe Ntintelo\Documents\unilever_pipeline
python utilities/teams_notifier.py
```

Expected output:
```
✅ Teams notification sent: ✅ ETL Pipeline - Success
✅ Teams notification sent: ❌ ETL Pipeline - Failed
✅ Teams notification sent: ⚠️ ETL Pipeline - Warning
```

### Test 2: Import and Test
```python
from utilities.teams_notifier import TeamsNotifier

notifier = TeamsNotifier()
notifier.send_info(
    "Test Notification",
    "If you see this, Teams integration is working!",
    details={"Environment": "Development", "Timestamp": "test"}
)
```

### Test 3: Full Pipeline Test
```bash
python etl-scripts/run_pipeline.py
```

You should see Teams notifications in your channel for pipeline start, progress, and completion.

---

## 9️⃣ Troubleshooting

### Issue: "Teams webhook not configured"
**Solution:**
```powershell
# Verify env variable is set
$env:TEAMS_WEBHOOK

# If empty, set it again
[System.Environment]::SetEnvironmentVariable(
  "TEAMS_WEBHOOK",
  "https://outlook.office.com/webhook/your-url",
  "User"
)

# Restart PowerShell/VS Code
```

### Issue: "Teams notification failed: 401"
**Cause:** Invalid or expired webhook URL
**Solution:**
1. Go to Teams channel → Connectors
2. Delete the old webhook
3. Create a new webhook
4. Update `TEAMS_WEBHOOK` environment variable

### Issue: "Teams notification timeout (10s)"
**Cause:** Network connectivity issue or slow Teams service
**Solution:**
- Check internet connection
- Verify firewall allows HTTPS to outlook.office.com
- Test with: `Test-NetConnection -ComputerName outlook.office.com -Port 443`

### Issue: "No module named 'requests'"
**Solution:**
```bash
pip install requests
```

---

## 🔟 Advanced: Custom Notification Formats

### Create custom notification type:
```python
from utilities.teams_notifier import TeamsNotifier, NotificationType

notifier = TeamsNotifier()

# Use the generic send_notification method
notifier.send_notification(
    title="Custom Alert",
    message="This is a custom formatted notification",
    notification_type=NotificationType.INFO,
    details={
        "Custom Field 1": "Value 1",
        "Custom Field 2": "Value 2",
        "Metrics": "More data here"
    }
)
```

---

## 1️⃣1️⃣ Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     ETL Pipeline                             │
│  (run_pipeline.py, etl_dag_production.py, monitor_etl.py)   │
└──────────────┬──────────────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────────────┐
│              teams_notifier.py Module                        │
│  - Initialize notification object                            │
│  - Format Adaptive Card                                      │
│  - Read TEAMS_WEBHOOK from environment                       │
└──────────────┬──────────────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────────────┐
│        Make HTTPS POST request to webhook URL               │
│        (outlook.office.com/webhook/...)                     │
└──────────────┬──────────────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────────────┐
│         Microsoft Teams Channel                              │
│  #etl-pipeline-alerts (or your chosen channel)              │
│                                                              │
│  ✅ ETL Pipeline - Success                                  │
│  Daily data ingestion and transformation completed          │
│  ✓ Records: 55,550                                          │
│  ✓ Duration: 2m 34s                                         │
│  ✓ Quality Score: 98.5%                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 1️⃣2️⃣ Production Deployment Checklist

- [ ] Webhook URL configured as `TEAMS_WEBHOOK` environment variable
- [ ] `.env` file added to `.gitignore`
- [ ] `requests` module installed: `pip install requests`
- [ ] Test notification sent successfully
- [ ] ETL script integration tested in development
- [ ] Airflow DAG callbacks configured (if using Airflow)
- [ ] Monitoring script has notification support
- [ ] Documentation shared with team
- [ ] Rotation policy for webhook URLs established
- [ ] Alert response procedures documented

---

## 1️⃣3️⃣ Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| Set env var (PowerShell) | Store webhook URL | `[System.Environment]::SetEnvironmentVariable("TEAMS_WEBHOOK", "...", "User")` |
| Test module | Verify setup | `python utilities/teams_notifier.py` |
| Run pipeline | Execute with notifications | `python etl-scripts/run_pipeline.py` |
| Check env var | Verify configuration | `$env:TEAMS_WEBHOOK` |
| View Teams card | See notification format | Visit Teams channel |

---

**Last Updated:** February 24, 2026
**Created by:** GitHub Copilot
**Project:** Unilever ETL Pipeline & Data Warehouse
