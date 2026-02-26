variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
  type        = string
}

variable "environment" {
  description = "Environment name"
  default     = "production"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR for VPC"
  default     = "10.0.0.0/16"
  type        = string
}

variable "public_subnet_cidr" {
  description = "Public subnet CIDR"
  default     = "10.0.1.0/24"
  type        = string
}

variable "private_subnet_cidr" {
  description = "Private subnet CIDR"
  default     = "10.0.2.0/24"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  default     = "t3.medium"
  type        = string
}

variable "db_instance_class" {
  description = "RDS instance class"
  default     = "db.t3.micro"
  type        = string
}

variable "db_storage_gb" {
  description = "RDS storage in GB"
  default     = 100
  type        = number
}

variable "db_master_username" {
  description = "RDS master username"
  default     = "postgres"
  type        = string
  sensitive   = true
}

variable "multi_az" {
  description = "Enable multi-AZ for RDS"
  default     = true
  type        = bool
}

variable "key_pair_name" {
  description = "EC2 key pair name"
  type        = string
}

variable "ssh_cidr" {
  description = "CIDR for SSH access"
  default     = "0.0.0.0/0"
  type        = string
}
