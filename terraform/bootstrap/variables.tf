variable "aws_region" {
  description = "AWS region for backend resources"
  type        = string
  default     = "us-east-1"
}

variable "prefix" {
  description = "Prefix for resource names to ensure uniqueness"
  type        = string
  default     = "nova-infra"
}

variable "state_key" {
  description = "Path to the state file within the S3 bucket"
  type        = string
  default     = "terraform.tfstate"
}
