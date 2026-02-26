# Terraform Configuration for Unilever ETL Pipeline on AWS

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
  
  backend "s3" {
    bucket         = "unilever-terraform-state"
    key            = "etl-pipeline/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "Unilever ETL Pipeline"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# VPC for ETL Pipeline
resource "aws_vpc" "etl_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "unilever-etl-vpc"
  }
}

# Public Subnet
resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.etl_vpc.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "unilever-public-subnet"
  }
}

# Private Subnet for RDS
resource "aws_subnet" "private_subnet" {
  vpc_id            = aws_vpc.etl_vpc.id
  cidr_block        = var.private_subnet_cidr
  availability_zone = data.aws_availability_zones.available.names[1]
  
  tags = {
    Name = "unilever-private-subnet"
  }
}

# EC2 Instance for Airflow/ETL
resource "aws_instance" "etl_server" {
  ami                    = data.aws_ami.amazon_linux_2.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.etl_sg.id]
  key_name               = var.key_pair_name
  
  iam_instance_profile = aws_iam_instance_profile.etl_profile.name
  
  user_data = base64encode(templatefile("${path.module}/init.sh", {
    db_endpoint = aws_db_instance.postgres.endpoint
    db_name     = aws_db_instance.postgres.db_name
  }))
  
  depends_on = [aws_db_instance.postgres]
  
  tags = {
    Name = "unilever-etl-server"
  }
}

# RDS PostgreSQL Database
resource "aws_db_instance" "postgres" {
  allocated_storage      = var.db_storage_gb
  storage_type           = "gp2"
  engine                 = "postgres"
  engine_version         = "13.7"
  instance_class         = var.db_instance_class
  db_name                = "unilever_warehouse"
  username               = var.db_master_username
  password               = random_password.db_password.result
  skip_final_snapshot    = false
  final_snapshot_identifier = "unilever-warehouse-final-snapshot"
  
  db_subnet_group_name   = aws_db_subnet_group.default.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  
  backup_retention_period = 30
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"
  
  multi_az = var.multi_az
  
  tags = {
    Name = "unilever-warehouse-db"
  }
}

# Security Groups
resource "aws_security_group" "etl_sg" {
  name        = "unilever-etl-sg"
  description = "Security group for ETL server"
  vpc_id      = aws_vpc.etl_vpc.id
  
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_cidr]
  }
  
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "rds_sg" {
  name        = "unilever-rds-sg"
  description = "Security group for RDS"
  vpc_id      = aws_vpc.etl_vpc.id
  
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.etl_sg.id]
  }
}

# DB Subnet Group
resource "aws_db_subnet_group" "default" {
  name       = "unilever-db-subnet-group"
  subnet_ids = [aws_subnet.public_subnet.id, aws_subnet.private_subnet.id]
}

# IAM Role for EC2
resource "aws_iam_role" "etl_role" {
  name = "unilever-etl-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "etl_policy" {
  name = "unilever-etl-policy"
  role = aws_iam_role.etl_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = ["arn:aws:s3:::unilever-backups/*"]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "etl_profile" {
  name = "unilever-etl-profile"
  role = aws_iam_role.etl_role.name
}

# Data sources
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]
  
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

# Random password for RDS
resource "random_password" "db_password" {
  length  = 16
  special = true
}

# Outputs
output "ec2_public_ip" {
  value       = aws_instance.etl_server.public_ip
  description = "Public IP of ETL server"
}

output "rds_endpoint" {
  value       = aws_db_instance.postgres.endpoint
  description = "RDS endpoint"
}

output "db_password_ssm" {
  value = "Stored in AWS Secrets Manager"
}
