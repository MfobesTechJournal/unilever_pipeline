#!/bin/bash
# AWS Deployment Helper Script
# Quick commands for deploying Unilever ETL Pipeline to AWS

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}→${NC} $1"
}

# ============================================================================
# Check AWS CLI
# ============================================================================

check_aws_cli() {
    print_header "Checking AWS CLI"
    
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found"
        echo "Install from: https://aws.amazon.com/cli/"
        exit 1
    fi
    
    AWS_VERSION=$(aws --version)
    print_success "AWS CLI installed: $AWS_VERSION"
    
    # Check credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured"
        echo "Run: aws configure"
        exit 1
    fi
    
    print_success "AWS credentials configured"
}

# ============================================================================
# Create RDS Database
# ============================================================================

create_rds_database() {
    print_header "Creating RDS PostgreSQL Database"
    
    print_info "This will create an RDS PostgreSQL database"
    print_info "Estimated cost: \$15-20/month"
    
    read -p "Continue? (y/n) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Skipped RDS creation"
        return
    fi
    
    # Check if database already exists
    EXISTING=$(aws rds describe-db-instances \
        --db-instance-identifier unilever-warehouse \
        2>/dev/null || echo "")
    
    if [ ! -z "$EXISTING" ]; then
        print_error "Database 'unilever-warehouse' already exists"
        return
    fi
    
    # Generate random master password
    MASTER_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-20)
    
    print_info "Creating RDS instance..."
    print_info "Master Password: $MASTER_PASSWORD"
    print_info "Save this password securely!"
    
    aws rds create-db-instance \
        --db-instance-identifier unilever-warehouse \
        --db-instance-class db.t3.micro \
        --engine postgres \
        --engine-version 13.7 \
        --master-username postgres \
        --master-user-password "$MASTER_PASSWORD" \
        --allocated-storage 20 \
        --db-name unilever_warehouse \
        --backup-retention-period 7 \
        --multi-az \
        --publicly-accessible false \
        --enable-cloudwatch-logs-exports postgresql \
        --enable-iam-database-authentication \
        --tags Key=Project,Value=UnileverETL Key=Environment,Value=Production \
        --no-deletion-protection \
        --enable-storage-encryption
    
    print_success "RDS instance creation started"
    print_info "Wait 5-10 minutes for completion"
    echo
    echo "View progress:"
    echo "  AWS Console: https://console.aws.amazon.com/rds/home"
    echo "  Or run: aws rds describe-db-instances --db-instance-identifier unilever-warehouse"
    echo
    echo "Next steps:"
    echo "  1. Wait for RDS to be 'available'"
    echo "  2. Copy the Endpoint (e.g., unilever-warehouse.xxxxx.rds.amazonaws.com)"
    echo "  3. Update .env file with DB_HOST, DB_PASSWORD"
}

# ============================================================================
# Launch EC2 Instance
# ============================================================================

launch_ec2_instance() {
    print_header "Launching EC2 Instance"
    
    print_info "This will launch an EC2 instance"
    print_info "Estimated cost: \$8-10/month (running 24/7)"
    
    read -p "Continue? (y/n) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Skipped EC2 launch"
        return
    fi
    
    # Check if instance already exists
    EXISTING=$(aws ec2 describe-instances \
        --filters "Name=tag:Name,Values=unilever-pipeline" \
        --query 'Reservations[0].Instances[0].InstanceId' \
        --output text 2>/dev/null)
    
    if [ "$EXISTING" != "None" ] && [ ! -z "$EXISTING" ]; then
        print_error "Instance 'unilever-pipeline' already exists: $EXISTING"
        return
    fi
    
    # Get latest Ubuntu 22.04 AMI
    AMI_ID=$(aws ec2 describe-images \
        --owners 099720109477 \
        --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
        --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
        --output text)
    
    print_info "Using AMI: $AMI_ID (Ubuntu 22.04 LTS)"
    
    # Get your IP
    YOUR_IP=$(curl -s https://api.ipify.org)
    print_info "Your IP: $YOUR_IP"
    
    # Create security group
    SG_ID=$(aws ec2 create-security-group \
        --group-name unilever-pipeline-sg \
        --description "Security group for Unilever ETL Pipeline" \
        --query 'GroupId' \
        --output text)
    
    print_success "Security group created: $SG_ID"
    
    # Add inbound rules
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 22 \
        --cidr "$YOUR_IP/32"
    
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0
    
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 443 \
        --cidr 0.0.0.0/0
    
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 8080 \
        --cidr 0.0.0.0/0
    
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 3000 \
        --cidr 0.0.0.0/0
    
    print_success "Security group rules configured"
    
    # Create key pair
    print_info "Creating key pair..."
    aws ec2 create-key-pair \
        --key-name unilever-pipeline \
        --query 'KeyMaterial' \
        --output text > ~/unilever-pipeline.pem
    
    chmod 600 ~/unilever-pipeline.pem
    print_success "Key pair created: ~/unilever-pipeline.pem"
    print_error "IMPORTANT: Keep this file safe! Don't share or commit it."
    
    # Launch instance
    print_info "Launching EC2 instance..."
    INSTANCE_ID=$(aws ec2 run-instances \
        --image-id "$AMI_ID" \
        --instance-type t3.small \
        --key-name unilever-pipeline \
        --security-group-ids "$SG_ID" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=unilever-pipeline}]" \
        --query 'Instances[0].InstanceId' \
        --output text)
    
    print_success "EC2 instance launched: $INSTANCE_ID"
    print_info "Waiting for instance to start..."
    
    # Wait for instance
    aws ec2 wait instance-running \
        --instance-ids "$INSTANCE_ID"
    
    # Get public IP
    PUBLIC_IP=$(aws ec2 describe-instances \
        --instance-ids "$INSTANCE_ID" \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)
    
    print_success "Instance is running!"
    echo
    echo "Instance Details:"
    echo "  Instance ID: $INSTANCE_ID"
    echo "  Public IP: $PUBLIC_IP"
    echo "  Security Group: $SG_ID"
    echo
    echo "SSH into instance:"
    echo "  ssh -i ~/unilever-pipeline.pem ubuntu@$PUBLIC_IP"
    echo
    echo "Next steps:"
    echo "  1. Wait 1-2 minutes for system startup"
    echo "  2. SSH into the instance"
    echo "  3. Run: sudo apt update && sudo apt install -y docker.io docker-compose"
    echo "  4. Clone repository: git clone https://github.com/MfobesTechJournal/unilever_pipeline.git"
}

# ============================================================================
# Get Deployment Status
# ============================================================================

get_deployment_status() {
    print_header "Deployment Status"
    
    print_info "RDS Instances:"
    aws rds describe-db-instances \
        --query 'DBInstances[?DBInstanceIdentifier==`unilever-warehouse`].[DBInstanceIdentifier,Engine,DBInstanceStatus]' \
        --output table
    
    echo
    print_info "EC2 Instances:"
    aws ec2 describe-instances \
        --filters "Name=instance-state-name,Values=running,stopped" \
        --query 'Reservations[].Instances[?Tags[?Key==`Name` && Value==`unilever-pipeline`]].[InstanceId,InstanceType,State.Name,PublicIpAddress]' \
        --output table
    
    echo
    print_info "Security Groups:"
    aws ec2 describe-security-groups \
        --filters "Name=group-name,Values=unilever-pipeline-sg" \
        --query 'SecurityGroups[].GroupId' \
        --output table
}

# ============================================================================
# Stop EC2 (Save Costs)
# ============================================================================

stop_ec2_instance() {
    print_header "Stopping EC2 Instance"
    
    INSTANCE_ID=$(aws ec2 describe-instances \
        --filters "Name=tag:Name,Values=unilever-pipeline" \
        --query 'Reservations[0].Instances[0].InstanceId' \
        --output text 2>/dev/null)
    
    if [ -z "$INSTANCE_ID" ] || [ "$INSTANCE_ID" == "None" ]; then
        print_error "No running instance found"
        return
    fi
    
    print_info "Stopping instance: $INSTANCE_ID"
    aws ec2 stop-instances --instance-ids "$INSTANCE_ID"
    print_success "Instance stop request sent"
    print_info "This will save ~\$5/month in EC2 costs"
    print_info "RDS will continue running"
}

# ============================================================================
# Estimate Costs
# ============================================================================

estimate_costs() {
    print_header "AWS Monthly Cost Estimation"
    
    echo "Scenario 1: Always Running (24/7)"
    echo "  EC2 t3.small: \$0.042 × 730h = \$30.66"
    echo "  RDS t3.micro: \$0.035 × 730h = \$25.55"
    echo "  S3 + Data: \$1.00"
    echo "  CloudWatch: \$0 (free tier)"
    echo "  TOTAL: ~\$57/month"
    echo
    
    echo "Scenario 2: Stopped at Nights/Weekends (12h/day)"
    echo "  EC2 t3.small: \$0.042 × 365h = \$15.33"
    echo "  RDS t3.micro: \$0.035 × 730h = \$25.55"
    echo "  S3 + Data: \$1.00"
    echo "  TOTAL: ~\$42/month"
    echo
    
    echo "Scenario 3: Stopped During Off-hours (8h/day)"
    echo "  EC2 t3.small: \$0.042 × 240h = \$10.08"
    echo "  RDS t3.micro: \$0.035 × 730h = \$25.55"
    echo "  S3 + Data: \$1.00"
    echo "  TOTAL: ~\$36/month"
    echo
    
    echo "To reduce costs:"
    echo "  • Stop EC2 when not needed: saves ~\$10/month"
    echo "  • Use RDS free tier credits: saves ~\$25/month"
    echo "  • Store old backups in S3 Glacier: saves ~\$0.50/month"
}

# ============================================================================
# Main Menu
# ============================================================================

print_header "Unilever ETL Pipeline - AWS Deployment Helper"

echo "Commands:"
echo "  1. check_aws_cli           - Verify AWS CLI is installed"
echo "  2. create_rds_database     - Create RDS PostgreSQL database"
echo "  3. launch_ec2_instance     - Launch EC2 instance"
echo "  4. get_deployment_status   - Show deployment status"
echo "  5. stop_ec2_instance       - Stop EC2 (save costs)"
echo "  6. estimate_costs          - Show cost scenarios"
echo
echo "Usage: ./aws-deploy.sh [command]"
echo "Example: ./aws-deploy.sh create_rds_database"
echo

if [ $# -eq 0 ]; then
    print_error "No command specified"
    exit 1
fi

case "$1" in
    check_aws_cli)
        check_aws_cli
        ;;
    create_rds_database)
        check_aws_cli
        create_rds_database
        ;;
    launch_ec2_instance)
        check_aws_cli
        launch_ec2_instance
        ;;
    get_deployment_status)
        check_aws_cli
        get_deployment_status
        ;;
    stop_ec2_instance)
        check_aws_cli
        stop_ec2_instance
        ;;
    estimate_costs)
        estimate_costs
        ;;
    *)
        print_error "Unknown command: $1"
        exit 1
        ;;
esac
