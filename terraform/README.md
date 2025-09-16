# Nova Infrastructure - Terraform Configuration

**100% portable** Terraform configuration that works in **ANY AWS account** with AdministratorAccess credentials. No hardcoded values, no manual steps.

## Prerequisites

- **AWS CLI** with AdministratorAccess credentials
- **Terraform** >= 1.5.0
- **kubectl** (optional, for EKS management)

## Quick Start (3 Simple Steps)

### 1. Configure AWS Credentials

```bash
# Option A: AWS CLI (recommended)
aws configure

# Option B: Environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Verify authentication
aws sts get-caller-identity
```

### 2. Initialize Backend (One Command)

```bash
# This single command does everything:
# - Creates S3 bucket with unique name
# - Creates DynamoDB table for locking
# - Configures backend.tf automatically
# - Initializes Terraform
./init-backend.sh
```

### 3. Deploy Infrastructure

```bash
# Review what will be created
terraform plan

# Deploy everything
terraform apply
```

## Backend Configuration

### Production (S3 Backend)

- **Bucket**: `nova-infra-terraform-state`
- **Region**: `us-east-1`
- **State Locking**: `nova-infra-terraform-lock` (DynamoDB)
- **Encryption**: AES256

The `init-backend.sh` script automatically creates these resources with proper security settings.

### Local Development

For testing without S3 backend:

```bash
terraform init -backend=false
```

## Infrastructure Components

### Networking Module

- VPC with CIDR 10.0.0.0/16
- 2 Public subnets (10.0.101.0/24, 10.0.102.0/24)
- 2 Private subnets (10.0.1.0/24, 10.0.2.0/24)
- Internet Gateway and NAT Gateways
- Security groups with least privilege

### EKS Module

- EKS cluster version 1.28
- Managed node groups with t3.medium instances
- Auto-scaling (min: 1, max: 3, desired: 2)
- OIDC provider for IRSA
- CloudWatch logging enabled

### ECR Module

- Container registry for Docker images
- Lifecycle policies for image management
- Vulnerability scanning enabled

## Configuration Variables

Key variables in `variables.tf`:

| Variable                    | Default         | Description                    |
| --------------------------- | --------------- | ------------------------------ |
| `project_name`              | `tf-visualizer` | Project name prefix            |
| `environment`               | `dev`           | Environment (dev/staging/prod) |
| `aws_region`                | `us-east-1`     | AWS deployment region          |
| `eks_cluster_version`       | `1.28`          | Kubernetes version             |
| `node_group_instance_types` | `["t3.medium"]` | EC2 instance types             |

## Access EKS Cluster

After deployment:

```bash
# Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name tf-visualizer-dev

# Verify connection
kubectl get nodes
```

## Outputs

View infrastructure outputs:

```bash
terraform output

# Key outputs:
# - vpc_id
# - eks_cluster_endpoint
# - eks_cluster_name
# - ecr_repository_urls
```

## Security Features

✅ Encryption at rest for all data stores
✅ Private subnets for compute resources
✅ VPC endpoints for AWS service access
✅ CloudWatch audit logging
✅ IRSA for pod-level IAM permissions

## Destroy Infrastructure

```bash
terraform destroy
```

⚠️ **Warning**: This deletes all resources including data.

## Troubleshooting

### State Lock Issues

```bash
terraform force-unlock <LOCK_ID>
```

### EKS Access Issues

```bash
aws eks update-kubeconfig --region us-east-1 --name <cluster-name>
```
