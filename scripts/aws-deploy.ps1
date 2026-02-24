# AWS Deployment Helper Script (Windows PowerShell Version)
# For deploying Unilever ETL Pipeline to AWS from Windows

param(
    [Parameter(Position = 0)]
    [ValidateSet('check-aws-cli', 'create-rds', 'launch-ec2', 'deployment-status', 'estimate-costs', 'help')]
    [string]$Command = 'help'
)

# Color functions
function Write-Header {
    param([string]$Message)
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Blue
    Write-Host "║ $Message" -ForegroundColor Blue -NoNewline
    Write-Host (" " * (61 - $Message.Length)) -ForegroundColor Blue -NoNewline
    Write-Host "║" -ForegroundColor Blue
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "→ $Message" -ForegroundColor Yellow
}

# ============================================================================
# Check AWS CLI
# ============================================================================

function Check-AwsCli {
    Write-Header "Checking AWS CLI"
    
    try {
        $version = aws --version
        Write-Success "AWS CLI installed: $version"
    }
    catch {
        Write-Error "AWS CLI not found"
        Write-Host "Install from: https://aws.amazon.com/cli/"
        return $false
    }
    
    try {
        $identity = aws sts get-caller-identity | ConvertFrom-Json
        Write-Success "AWS credentials configured"
        Write-Info "Account: $($identity.Account)"
        return $true
    }
    catch {
        Write-Error "AWS credentials not configured"
        Write-Host "Run: aws configure"
        return $false
    }
}

# ============================================================================
# Create RDS Database
# ============================================================================

function Create-RdsDatabase {
    Write-Header "Creating RDS PostgreSQL Database"
    
    Write-Info "This will create an RDS PostgreSQL database"
    Write-Info "Estimated cost: `$15-20/month"
    
    $continue = Read-Host "Continue? (y/n)"
    if ($continue -ne 'y') {
        Write-Info "Skipped RDS creation"
        return
    }
    
    # Check if database already exists
    try {
        $existing = aws rds describe-db-instances `
            --db-instance-identifier unilever-warehouse `
            --output text 2>$null
        
        if ($null -ne $existing) {
            Write-Error "Database 'unilever-warehouse' already exists"
            return
        }
    }
    catch {
        # Database doesn't exist - good!
    }
    
    # Generate master password
    $bytes = New-Object byte[] 20
    $rng = [System.Security.Cryptography.RNGCryptoServiceProvider]::new()
    $rng.GetBytes($bytes)
    $masterPassword = [System.Convert]::ToBase64String($bytes).Substring(0, 20)
    
    Write-Info "Creating RDS instance..."
    Write-Info "Master Password: $masterPassword"
    Write-Error "Save this password securely!"
    
    aws rds create-db-instance `
        --db-instance-identifier unilever-warehouse `
        --db-instance-class db.t3.micro `
        --engine postgres `
        --engine-version 13.7 `
        --master-username postgres `
        --master-user-password $masterPassword `
        --allocated-storage 20 `
        --db-name unilever_warehouse `
        --backup-retention-period 7 `
        --publicly-accessible false `
        --enable-cloudwatch-logs-exports postgresql `
        --tags Key=Project,Value=UnileverETL Key=Environment,Value=Production
    
    Write-Success "RDS instance creation started"
    Write-Info "Wait 5-10 minutes for completion"
    Write-Host ""
    Write-Host "View progress:"
    Write-Host "  AWS Console: https://console.aws.amazon.com/rds/home"
    Write-Host "  Or run: aws rds describe-db-instances --db-instance-identifier unilever-warehouse"
}

# ============================================================================
# Launch EC2 Instance
# ============================================================================

function Launch-Ec2Instance {
    Write-Header "Launching EC2 Instance"
    
    Write-Info "This will launch an EC2 instance"
    Write-Info "Estimated cost: `$8-10/month (running 24/7)"
    
    $continue = Read-Host "Continue? (y/n)"
    if ($continue -ne 'y') {
        Write-Info "Skipped EC2 launch"
        return
    }
    
    # Get latest Ubuntu 22.04 AMI
    Write-Info "Finding latest Ubuntu 22.04 LTS AMI..."
    $amiId = aws ec2 describe-images `
        --owners 099720109477 `
        --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" `
        --query "Images | sort_by(@, &CreationDate) | [-1].ImageId" `
        --output text
    
    Write-Success "AMI: $amiId"
    
    # Get your IP
    $yourIp = (Invoke-WebRequest -UseBasicParsing https://api.ipify.org).Content.Trim()
    Write-Info "Your IP: $yourIp"
    
    # Create security group
    Write-Info "Creating security group..."
    $sgId = aws ec2 create-security-group `
        --group-name unilever-pipeline-sg `
        --description "Security group for Unilever ETL Pipeline" `
        --query 'GroupId' `
        --output text
    
    Write-Success "Security group created: $sgId"
    
    # Add inbound rules
    $rules = @(
        @{Protocol='tcp'; Port=22; Cidr="$yourIp/32"; Description="SSH from your IP"},
        @{Protocol='tcp'; Port=80; Cidr="0.0.0.0/0"; Description="HTTP"},
        @{Protocol='tcp'; Port=443; Cidr="0.0.0.0/0"; Description="HTTPS"},
        @{Protocol='tcp'; Port=8080; Cidr="0.0.0.0/0"; Description="Airflow"},
        @{Protocol='tcp'; Port=3000; Cidr="0.0.0.0/0"; Description="Grafana"}
    )
    
    foreach ($rule in $rules) {
        aws ec2 authorize-security-group-ingress `
            --group-id $sgId `
            --protocol $rule.Protocol `
            --port $rule.Port `
            --cidr $rule.Cidr | Out-Null
        Write-Success "Rule added: $($rule.Description)"
    }
    
    # Create key pair
    Write-Info "Creating key pair..."
    $keyContent = aws ec2 create-key-pair `
        --key-name unilever-pipeline `
        --query 'KeyMaterial' `
        --output text
    
    $keyPath = "$HOME\unilever-pipeline.pem"
    $keyContent | Out-File -FilePath $keyPath -Encoding UTF8
    
    Write-Success "Key pair created: $keyPath"
    Write-Error "IMPORTANT: Keep this file safe! Don't share or commit it."
    
    # Launch instance
    Write-Info "Launching EC2 instance..."
    $instanceId = aws ec2 run-instances `
        --image-id $amiId `
        --instance-type t3.small `
        --key-name unilever-pipeline `
        --security-group-ids $sgId `
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=unilever-pipeline}]" `
        --query 'Instances[0].InstanceId' `
        --output text
    
    Write-Success "EC2 instance launched: $instanceId"
    Write-Info "Waiting for instance to start..."
    
    $maxWait = 60
    $elapsed = 0
    while ($elapsed -lt $maxWait) {
        $state = aws ec2 describe-instances `
            --instance-ids $instanceId `
            --query 'Reservations[0].Instances[0].State.Name' `
            --output text
        
        if ($state -eq "running") {
            break
        }
        
        Start-Sleep -Seconds 5
        $elapsed += 5
    }
    
    # Get public IP
    $publicIp = aws ec2 describe-instances `
        --instance-ids $instanceId `
        --query 'Reservations[0].Instances[0].PublicIpAddress' `
        --output text
    
    Write-Success "Instance is running!"
    Write-Host ""
    Write-Host "Instance Details:"
    Write-Host "  Instance ID: $instanceId"
    Write-Host "  Public IP: $publicIp"
    Write-Host "  Security Group: $sgId"
    Write-Host ""
    Write-Host "SSH into instance:"
    Write-Host "  ssh -i '$keyPath' ubuntu@$publicIp"
    Write-Host ""
    Write-Host "Or using PuTTY/MobaXterm on Windows with the .pem key"
}

# ============================================================================
# Get Deployment Status
# ============================================================================

function Get-DeploymentStatus {
    Write-Header "Deployment Status"
    
    Write-Info "RDS Instances:"
    $rds = aws rds describe-db-instances `
        --query 'DBInstances[?DBInstanceIdentifier==`unilever-warehouse`].[DBInstanceIdentifier,Engine,DBInstanceStatus,Endpoint.Address]' `
        --output table
    
    if ($null -ne $rds) {
        Write-Host $rds
    }
    else {
        Write-Host "No RDS instance found"
    }
    
    Write-Host ""
    Write-Info "EC2 Instances:"
    $ec2 = aws ec2 describe-instances `
        --filters "Name=instance-state-name,Values=running,stopped" `
        --query 'Reservations[].Instances[?Tags[?Key==`Name` && Value==`unilever-pipeline`]].[InstanceId,InstanceType,State.Name,PublicIpAddress]' `
        --output table
    
    if ($null -ne $ec2) {
        Write-Host $ec2
    }
    else {
        Write-Host "No EC2 instance found"
    }
}

# ============================================================================
# Estimate Costs
# ============================================================================

function Estimate-Costs {
    Write-Header "AWS Monthly Cost Estimation"
    
    Write-Host ""
    Write-Host "Scenario 1: Always Running (24/7)" -ForegroundColor Cyan
    Write-Host "  EC2 t3.small: `$0.042 × 730h = `$30.66"
    Write-Host "  RDS t3.micro: `$0.035 × 730h = `$25.55"
    Write-Host "  S3 + Data: `$1.00"
    Write-Host "  CloudWatch: `$0 (free tier)"
    Write-Host "  TOTAL: ~`$57/month"
    Write-Host ""
    
    Write-Host "Scenario 2: Stopped at Nights/Weekends (12h/day)" -ForegroundColor Cyan
    Write-Host "  EC2 t3.small: `$0.042 × 365h = `$15.33"
    Write-Host "  RDS t3.micro: `$0.035 × 730h = `$25.55"
    Write-Host "  S3 + Data: `$1.00"
    Write-Host "  TOTAL: ~`$42/month"
    Write-Host ""
    
    Write-Host "Scenario 3: Stopped During Off-hours (8h/day)" -ForegroundColor Cyan
    Write-Host "  EC2 t3.small: `$0.042 × 240h = `$10.08"
    Write-Host "  RDS t3.micro: `$0.035 × 730h = `$25.55"
    Write-Host "  S3 + Data: `$1.00"
    Write-Host "  TOTAL: ~`$36/month"
    Write-Host ""
    
    Write-Host "To reduce costs:" -ForegroundColor Yellow
    Write-Host "  • Stop EC2 when not needed: saves ~`$10/month"
    Write-Host "  • Use RDS free tier credits: saves ~`$25/month"
    Write-Host "  • Store old backups in S3 Glacier: saves ~`$0.50/month"
}

# ============================================================================
# Display Help
# ============================================================================

function Show-Help {
    Write-Header "Unilever ETL Pipeline - AWS Deployment Helper"
    
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Cyan
    Write-Host "  check-aws-cli       - Verify AWS CLI is installed"
    Write-Host "  create-rds          - Create RDS PostgreSQL database"
    Write-Host "  launch-ec2          - Launch EC2 instance"
    Write-Host "  deployment-status   - Show deployment status"
    Write-Host "  estimate-costs      - Show cost scenarios"
    Write-Host "  help                - Show this help message"
    Write-Host ""
    Write-Host "Usage: .\aws-deploy.ps1 [command]" -ForegroundColor Yellow
    Write-Host "Example: .\aws-deploy.ps1 create-rds" -ForegroundColor Yellow
    Write-Host ""
}

# ============================================================================
# Main
# ============================================================================

# Check if AWS CLI is installed (for most commands)
if ($Command -ne 'help') {
    if (-not (Check-AwsCli)) {
        exit 1
    }
}

switch ($Command) {
    'check-aws-cli' {
        Check-AwsCli
    }
    'create-rds' {
        Create-RdsDatabase
    }
    'launch-ec2' {
        Launch-Ec2Instance
    }
    'deployment-status' {
        Get-DeploymentStatus
    }
    'estimate-costs' {
        Estimate-Costs
    }
    'help' {
        Show-Help
    }
    default {
        Write-Error "Unknown command: $Command"
        Show-Help
        exit 1
    }
}
