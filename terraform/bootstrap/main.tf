# Bootstrap configuration to create Terraform backend resources
# This should be run first in any AWS account with AdministratorAccess
#
# Usage:
#   cd bootstrap
#   terraform init
#   terraform apply
#   cd ..
#   terraform init

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Get current AWS account ID dynamically
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Generate unique bucket name using account ID and region
locals {
  bucket_name     = "${var.prefix}-${data.aws_caller_identity.current.account_id}-${data.aws_region.current.name}-tfstate"
  dynamodb_table  = "${var.prefix}-terraform-lock"
}

# S3 bucket for Terraform state
resource "aws_s3_bucket" "terraform_state" {
  bucket = local.bucket_name

  tags = {
    Name        = "Terraform State"
    Environment = "global"
    ManagedBy   = "terraform-bootstrap"
  }
}

# Enable versioning for state history
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block all public access
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# DynamoDB table for state locking
resource "aws_dynamodb_table" "terraform_lock" {
  name         = local.dynamodb_table
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = "Terraform State Lock"
    Environment = "global"
    ManagedBy   = "terraform-bootstrap"
  }
}

# Output the backend configuration to use
output "backend_config" {
  value = <<-EOT

    # Add this to your backend.tf file:
    terraform {
      backend "s3" {
        bucket         = "${local.bucket_name}"
        key            = "${var.state_key}"
        region         = "${var.aws_region}"
        encrypt        = true
        dynamodb_table = "${local.dynamodb_table}"
      }
    }
  EOT

  description = "Backend configuration to use in main Terraform"
}

output "bucket_name" {
  value       = local.bucket_name
  description = "Name of the S3 bucket for Terraform state"
}

output "dynamodb_table_name" {
  value       = local.dynamodb_table
  description = "Name of the DynamoDB table for state locking"
}

output "region" {
  value       = var.aws_region
  description = "AWS region where backend resources were created"
}
