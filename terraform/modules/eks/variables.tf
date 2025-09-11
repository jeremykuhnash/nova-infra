variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "eks_cluster_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "private_subnet_ids" {
  description = "IDs of private subnets for EKS nodes"
  type        = list(string)
}

variable "node_group_instance_types" {
  description = "EC2 instance types for EKS node group"
  type        = list(string)
}

variable "node_group_min_size" {
  description = "Minimum size of the node group"
  type        = number
}

variable "node_group_max_size" {
  description = "Maximum size of the node group"
  type        = number
}

variable "node_group_desired_size" {
  description = "Desired size of the node group"
  type        = number
}

variable "node_group_disk_size" {
  description = "Disk size in GiB for worker nodes"
  type        = number
  default     = 20
}

variable "enable_cluster_autoscaler" {
  description = "Enable cluster autoscaler"
  type        = bool
  default     = true
}

variable "enable_metrics_server" {
  description = "Enable metrics server"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
