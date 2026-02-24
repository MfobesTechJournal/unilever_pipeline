# Email Alerting Configuration Guide

This guide explains how to configure email alerts for the Unilever ETL Pipeline.

## Overview

The pipeline can send email alerts for:
- ETL pipeline failures
- Data quality issues exceeding thresholds
- Multiple consecutive failed runs
- Processing delays

## Prerequisites

### Gmail (Recommended for Testing)
1. A Gmail account
2. An [App Password](https://support.google.com/accounts/answer/185833) (not your regular password)
3. 2FA enabled on your Google account

### Other Email Providers
- **Office 365**: SMTP server: `smtp.office365.com`, Port: 587
- **SendGrid**: SMTP server: `smtp.sendgrid.net`, Port: 587 or 25
- **AWS SES**: SMTP server: `email-smtp.{region}.amazonaws.com`, Port: 587
- **Corporate Email**: Check with your IT department

## Configuration

### Step 1: Get SMTP Credentials

**For Gmail:**
1. Enable 2-Step Verification in Google Account settings
2. Generate an [App Password](https://myaccount.google.com/apppasswords)
3. Choose "Mail" and "Windows Computer" (or your device)
4. Google will generate a 16-character password

**For Office 365:**
1. Use your full email address as username: `user@company.com`
2. Use your Office 365 password (or app password if 2FA enabled)

### Step 2: Update .env File

```bash
# Edit .env file
nano .env

# Add or update these lines:
SMTP_SERVER=smtp.gmail.com        # Gmail
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password   # Use app password, not Gmail password
EMAIL_FROM=noreply@unilever.com
ALERT_EMAIL=alerts@company.com
```

### Step 3: Test Email Configuration

```bash
# Test SMTP connection
python -c "
import smtplib
import os
from dotenv import load_dotenv
load_dotenv()

server = smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT')))
server.starttls()
try:
    server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
    print('✓ SMTP connection successful')
    server.quit()
except Exception as e:
    print(f'✗ SMTP login failed: {e}')
"
```

### Step 4: Send Test Alert

```bash
# Send a test email
python -c "
import sys
sys.path.insert(0, '.')
from monitor_etl import send_alert
send_alert('Test Alert', 'This is a test alert email from Unilever ETL Pipeline')
"
```

## Troubleshooting

### "Connection refused" or "Connection timeout"
- Verify SMTP_SERVER and SMTP_PORT are correct
- Check firewall/network settings are not blocking the SMTP port
- Some corporate networks block port 587; try port 25 or contact IT

### "Authentication failed"
- Gmail: Did you use the **App Password** (not your regular Gmail password)?
- Office 365: Check that 2FA is enabled properly
- Other services: Verify username and password are correct
- Some services require specific format: `user@company.com` vs just `user`

### "SSL: CERTIFICATE_VERIFY_FAILED"
- Update Python certificates: `pip install certifi`
- Or use `PYTHONHTTPSVERIFY=0` (not recommended for production)

### Emails not arriving
- Check ALERT_EMAIL is correct
- Check spam/junk folders
- Verify Email_FROM matches SMTP_USER (some providers require this)
- Check if sender is marked as suspicious/blocked

### "starttls() required"
- Ensure SMTP_PORT is 587 (TLS port)
- Port 25 requires different configuration
- Port 465 is for implicit TLS (different setup)

## SMTP Provider Configurations

### Gmail with App Password
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # 16-character app password
EMAIL_FROM=your_email@gmail.com
ALERT_EMAIL=recipient@gmail.com
```

### Office 365
```
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USER=user@company.com
SMTP_PASSWORD=your_office365_password
EMAIL_FROM=user@company.com
ALERT_EMAIL=alerts@company.com
```

### SendGrid
```
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.xxx_your_sendgrid_api_key_xxx
EMAIL_FROM=noreply@yourdomain.com
ALERT_EMAIL=alerts@yourdomain.com
```

### AWS SES (Example: us-east-1)
```
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your_ses_username
SMTP_PASSWORD=your_ses_password
EMAIL_FROM=noreply@yourdomain.com
ALERT_EMAIL=alerts@yourdomain.com
```

## Alert Thresholds

Configure when alerts are sent by setting these environment variables:

```bash
# Maximum data quality issues before alert
ALERT_QUALITY_ISSUES_MAX=100

# Number of consecutive failed runs before alert
ALERT_FAILED_RUNS_COUNT=3

# Minimum daily records before alert
ALERT_DAILY_RECORDS_MIN=1000
```

## Alert Examples

### Failure Alert
```
Subject: [UNILEVER ETL ALERT] ETL Pipeline Failure

There are 3 failed ETL runs in the last 24 hours

Failed Runs:
- Run #1234: Error loading dimension table
- Run #1233: Database connection timeout
- Run #1232: File validation failed

Action: Check ETL logs and resolve issues
```

### Data Quality Alert
```
Subject: [UNILEVER ETL ALERT] Data Quality Issue

Found 234 data quality issues in the last run

Issue Breakdown:
- Null values: 120
- Duplicate records: 50
- Outliers: 40
- Negative values: 24

Threshold: 100 issues
Action: Review data sources and data cleaning rules
```

## Security Best Practices

⚠️ **DO NOT commit .env file to Git!**

1. Never share your SMTP_PASSWORD
2. Use app passwords instead of account passwords
3. Restrict email recipient to necessary personnel
4. Monitor failed alert attempts
5. Rotate credentials regularly
6. For Docker: Use Docker Secrets instead of .env in production

### Docker Secrets (Production)
```bash
# Create secret
echo "your_api_key" | docker secret create smtp_password -

# Use in docker-compose
docker-compose.yml:
  services:
    pipeline:
      secrets:
        - smtp_password
      environment:
        SMTP_PASSWORD_FILE: /run/secrets/smtp_password
```

## Monitoring Alerts

### View sent alerts
```sql
-- Check alert delivery in logs
SELECT * FROM etl_log 
WHERE error_message LIKE '%alert%'
ORDER BY start_time DESC;
```

### Disable alerts temporarily
```bash
# In .env, set credentials to empty
SMTP_USER=
SMTP_PASSWORD=
```

### Custom alert messages
Edit `monitor_etl.py` to customize alert content:

```python
def check_failed_runs(conn):
    failed_runs = check_failed_runs_impl(conn)
    if failed_runs:
        custom_message = f"Custom alert: {len(failed_runs)} runs failed"
        send_alert("ETL Failure", custom_message)
```

## Testing

### Dry-run (preview alerts without sending)
```bash
# Modify send_alert in monitor_etl.py to log instead of send:
def send_alert(subject, message):
    print(f"[DRY RUN] Would send: {subject}")
    print(f"Message: {message}")
```

### Load testing
```bash
# Send multiple test emails
for i in {1..5}; do
  python -c "from monitor_etl import send_alert; send_alert('Test $i', 'Message $i')"
done
```

## Advanced Configuration

### HTML Email Templates
Modify `send_alert()` function to use custom HTML templates:

```python
def send_alert(subject, message):
    html_template = """
    <html>
        <body style="font-family: Arial">
            <div style="background-color: #f5f5f5; padding: 20px">
                <h1>Unilever ETL Alert</h1>
                <p>{message}</p>
                <a href="http://grafana:3000">View Dashboard</a>
            </div>
        </body>
    </html>
    """
    # ... send with template
```

### Multiple Recipients
```bash
# Comma-separated emails (update send_alert function)
ALERT_EMAIL=alerts@company.com,ops@company.com,admin@company.com
```

### Different alerts to different people
```python
CRITICAL_ALERT_EMAIL = "critical@company.com"
WARNING_ALERT_EMAIL = "warnings@company.com"
INFO_ALERT_EMAIL = "info@company.com"

def send_alert(subject, message, severity='WARNING'):
    if severity == 'CRITICAL':
        recipient = CRITICAL_ALERT_EMAIL
    elif severity == 'INFO':
        recipient = INFO_ALERT_EMAIL
    else:
        recipient = WARNING_ALERT_EMAIL
    # ... send to appropriate recipient
```

---

For more information, see [OPERATIONS.md](../OPERATIONS.md) and [README.md](../README.md).
