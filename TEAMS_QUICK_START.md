# 🚀 Teams Notifications - Quick Start

**Get Microsoft Teams alerts for your ETL pipeline in 5 minutes.**

---

## Step 1: Create Teams Webhook (2 minutes)

1. Open **Microsoft Teams**
2. Go to your desired channel (or create: `#etl-pipeline-alerts`)
3. Click **⋯** → **Connectors** → Search **"Incoming Webhook"**
4. Click **Add** or **Configure**
5. Name it: `Unilever ETL Pipeline Alerts`
6. Click **Create**
7. **Copy the Webhook URL** (looks like: `https://outlook.office.com/webhook/...`)

---

## Step 2: Set Environment Variable (1 minute)

**Windows PowerShell (Admin):**
```powershell
[System.Environment]::SetEnvironmentVariable(
  "TEAMS_WEBHOOK",
  "https://outlook.office.com/webhook/YOUR-ACTUAL-URL-HERE",
  "User"
)
```

**Restart PowerShell/VS Code** (important!)

Verify it's set:
```powershell
$env:TEAMS_WEBHOOK
```

---

## Step 3: Install Required Package (30 seconds)

```bash
pip install requests
```

---

## Step 4: Test It Works (1 minute)

```bash
python utilities/teams_notifier.py
```

You should see 3 test notifications in your Teams channel.

---

## Step 5: Integrate Into Your Code (1 minute)

### Option A: Simple Wrapper (Recommended)
```python
from utilities.teams_notifier import TeamsNotifier

notifier = TeamsNotifier()

try:
    # Your ETL code here
    print("Running ETL pipeline...")
    
    notifier.send_success(
        "ETL Pipeline",
        "Pipeline completed successfully",
        details={
            "Records": "55,550",
            "Duration": "2m 34s",
            "Quality": "98.5%"
        }
    )
except Exception as e:
    notifier.send_failure(
        "ETL Pipeline",
        "Pipeline failed",
        error_details=str(e)
    )
    raise
```

### Option B: Context Manager (Cleaner)
```python
from utilities.examples_integration import ETLNotificationContext

with ETLNotificationContext("Data Ingestion") as notifier:
    # Your code automatically gets notifications!
    data = load_data()
    transform_data(data)
    load_to_warehouse(data)
```

### Option C: Decorator (Minimal code)
```python
from utilities.examples_integration import notify_on_execution

@notify_on_execution("Data Quality Check")
def check_quality(data):
    # Your validation logic
    return True
```

---

## Common Patterns

| Use Case | Pattern | Example |
|----------|---------|---------|
| Wrap entire ETL | Context Manager | See Option B above |
| Wrap single function | Decorator | See Option C above |
| Custom messages | Wrapper | See Option A above |
| Full control | TeamsNotifier direct | `notifier.send_success(...)` |

---

## Notification Types Available

```python
notifier.send_success(...)     # ✅ Pipeline succeeded
notifier.send_failure(...)     # ❌ Pipeline failed
notifier.send_warning(...)     # ⚠️ Non-critical issue
notifier.send_info(...)        # ℹ️ Information
notifier.send_in_progress(...) # ⏳ Currently running
```

---

## Security Reminders

✅ **DO:**
- Store URL only in `TEAMS_WEBHOOK` environment variable
- Use `.env` file (already in .gitignore)
- Rotate webhook if exposed

❌ **DON'T:**
- Hardcode URLs in code
- Commit URLs to GitHub
- Share URLs in messages

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Teams webhook not configured" | Run: `[System.Environment]::SetEnvironmentVariable("TEAMS_WEBHOOK", "your-url", "User")` then restart |
| Still not found after restart | Verify with: `$env:TEAMS_WEBHOOK` |
| "401 Unauthorized" | Webhook URL is invalid/expired—create new one |
| "No module named 'requests'" | Run: `pip install requests` |
| Message not appearing | Check Teams channel has incoming webhooks enabled |

---

## Full Documentation

For complete setup, advanced patterns, and Airflow integration: **[TEAMS_NOTIFICATIONS.md](TEAMS_NOTIFICATIONS.md)**

For code examples and patterns: **[utilities/examples_integration.py](utilities/examples_integration.py)**

---

## Next: Integrate Into Your ETL

Update these files to use notifications:
- `etl-scripts/run_pipeline.py`
- `airflow-dags/etl_dag.py`
- `monitoring/monitor_etl.py`

Start with one file, test it, then expand to others.

**Questions?** Check [TEAMS_NOTIFICATIONS.md](TEAMS_NOTIFICATIONS.md) for detailed Q&A section.
