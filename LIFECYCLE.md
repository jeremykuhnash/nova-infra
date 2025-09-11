# Nova Infrastructure - Complete Lifecycle Guide

## 🚀 Full Deployment Lifecycle

This guide covers the complete lifecycle from zero to production-ready infrastructure.

## Prerequisites

### Required Tools
- AWS CLI v2
- Terraform >= 1.5.0
- GitHub CLI (gh)
- kubectl
- Docker
- Helm >= 3.0

### AWS Requirements
- AWS Account with AdministratorAccess
- Sufficient quota for:
  - VPCs (1)
  - EKS Clusters (1)
  - EC2 Instances (2-3 t3.medium)
  - Elastic IPs (2)
  - NAT Gateways (2)

## Phase 1: Initial Setup

### 1.1 Clone Repository
```bash
git clone https://github.com/jeremykuhnash/nova-infra.git
cd nova-infra
```

### 1.2 Configure AWS Credentials
```bash
# Configure AWS CLI
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: us-east-1
# - Default output: json

# Verify authentication
aws sts get-caller-identity
```

### 1.3 Install Required Tools
```bash
# Run the setup script
./setup.sh

# Or install manually:
# GitHub CLI
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key C99B11DEB97541F0
sudo apt-add-repository https://cli.github.com/packages
sudo apt update
sudo apt install gh

# Authenticate with GitHub
gh auth login
```

## Phase 2: Backend Infrastructure

### 2.1 Initialize Terraform Backend
```bash
cd terraform
./init-backend.sh
```

This creates:
- S3 bucket: `nova-infra-{ACCOUNT_ID}-{REGION}-tfstate`
- DynamoDB table: `nova-infra-terraform-lock`
- Configures `backend.tf` automatically

### 2.2 Configure GitHub Secrets (Optional for CI/CD)
```bash
# Setup GitHub Actions secrets
./scripts/setup-github-secrets.sh
```

This sets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `TF_STATE_BUCKET`

## Phase 3: Infrastructure Deployment

### 3.1 Plan Infrastructure
```bash
cd terraform
terraform plan -out=tfplan
```

### 3.2 Deploy Infrastructure
```bash
# Apply the plan (15-20 minutes)
terraform apply tfplan

# Or auto-approve
terraform apply -auto-approve
```

### 3.3 Verify Deployment
```bash
# Check resources
terraform state list

# Get outputs
terraform output

# Save important values
export ECR_URL=$(terraform output -raw ecr_repository_url)
export EKS_CLUSTER=$(terraform output -raw eks_cluster_name)
export VPC_ID=$(terraform output -raw vpc_id)
```

## Phase 4: EKS Configuration

### 4.1 Configure kubectl
```bash
# Update kubeconfig
aws eks update-kubeconfig --region us-east-1 --name $EKS_CLUSTER

# Verify connection
kubectl get nodes
kubectl get pods -A
```

### 4.2 Install Add-ons
```bash
# Install metrics server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Install AWS Load Balancer Controller (optional)
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=$EKS_CLUSTER
```

## Phase 5: Application Deployment

### 5.1 Build Application
```bash
cd apps/hello-world

# Build Docker image
docker build -t tf-visualizer .

# Tag for ECR
docker tag tf-visualizer:latest $ECR_URL:latest
```

### 5.2 Push to ECR
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_URL

# Push image
docker push $ECR_URL:latest
```

### 5.3 Deploy with Helm
```bash
# Install application
helm install tf-visualizer ./helm/tf-visualizer \
  --set image.repository=$ECR_URL \
  --set image.tag=latest \
  --namespace default

# Check deployment
kubectl get deployments
kubectl get services
kubectl get pods
```

### 5.4 Get Application URL
```bash
# Get Load Balancer URL
kubectl get service tf-visualizer -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Wait for DNS propagation (2-3 minutes)
# Then access: http://LOAD_BALANCER_URL
```

## Phase 6: Testing & Validation

### 6.1 Test Application
```bash
# Health check
LB_URL=$(kubectl get service tf-visualizer -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl http://$LB_URL/health

# API endpoints
curl http://$LB_URL/api/sample
curl -X POST http://$LB_URL/api/parse -F "file=@terraform/main.tf"
```

### 6.2 Check Logs
```bash
# Application logs
kubectl logs -l app=tf-visualizer

# EKS cluster logs (CloudWatch)
aws logs tail /aws/eks/$EKS_CLUSTER/cluster --follow
```

## Phase 7: Monitoring & Scaling

### 7.1 Enable Monitoring
```bash
# Check metrics
kubectl top nodes
kubectl top pods

# View HPA status
kubectl get hpa
```

### 7.2 Scale Application
```bash
# Manual scaling
kubectl scale deployment tf-visualizer --replicas=3

# Or update Helm values
helm upgrade tf-visualizer ./helm/tf-visualizer \
  --set replicaCount=3
```

## Phase 8: Updates & Maintenance

### 8.1 Update Application
```bash
# Build new version
docker build -t tf-visualizer:v2 .
docker tag tf-visualizer:v2 $ECR_URL:v2
docker push $ECR_URL:v2

# Deploy update
helm upgrade tf-visualizer ./helm/tf-visualizer \
  --set image.tag=v2
```

### 8.2 Update Infrastructure
```bash
cd terraform
# Modify configuration
terraform plan
terraform apply
```

## Phase 9: Cleanup

### 9.1 Remove Application
```bash
# Uninstall Helm release
helm uninstall tf-visualizer

# Clean up PVCs if any
kubectl delete pvc --all
```

### 9.2 Destroy Infrastructure
```bash
cd terraform
terraform destroy -auto-approve

# This removes:
# - EKS cluster and node groups
# - VPC and networking
# - ECR repository
# - All IAM roles and policies
```

### 9.3 Clean Backend Resources (Optional)
```bash
cd terraform/bootstrap
terraform destroy -auto-approve

# This removes:
# - S3 state bucket
# - DynamoDB lock table
```

## Troubleshooting

### Common Issues

#### EKS Node Not Ready
```bash
# Check node status
kubectl describe nodes

# Check instance profile
aws eks describe-nodegroup \
  --cluster-name $EKS_CLUSTER \
  --nodegroup-name nova-infra-production-node-group
```

#### Pods Not Starting
```bash
# Check pod events
kubectl describe pod POD_NAME

# Check ECR permissions
aws ecr get-repository-policy --repository-name nova-infra-production
```

#### Load Balancer Not Accessible
```bash
# Check security groups
aws ec2 describe-security-groups --group-ids $(terraform output -raw eks_cluster_security_group_id)

# Check target health
aws elbv2 describe-target-health --target-group-arn TARGET_GROUP_ARN
```

## Cost Optimization

### Estimated Costs
- EKS Control Plane: $0.10/hour
- Node Group (2 x t3.medium): $0.084/hour
- NAT Gateways (2x): $0.090/hour
- Load Balancer: $0.025/hour
- **Total: ~$0.30/hour ($7.20/day)**

### Cost Saving Tips
1. Use spot instances for node groups
2. Scale down to 1 node for development
3. Delete NAT gateways for testing (use public subnets)
4. Use t3.small instead of t3.medium
5. Destroy resources when not in use

## CI/CD Integration

### GitHub Actions Workflow
```bash
# Trigger deployment
gh workflow run terraform-deploy.yml \
  -f action=apply \
  -f environment=production

# Check status
gh run list --workflow=terraform-deploy.yml
```

### Manual Deployment
```bash
# From any machine with credentials
git pull origin main
cd terraform
terraform apply -auto-approve
```

## Security Best Practices

1. **Never commit credentials** - Use AWS profiles or environment variables
2. **Enable MFA** for AWS console access
3. **Use IRSA** for pod-level permissions
4. **Rotate credentials** regularly
5. **Enable GuardDuty** for threat detection
6. **Use private subnets** for compute resources
7. **Enable VPC Flow Logs** for network monitoring

## Backup & Recovery

### State Backup
```bash
# Backup state file
aws s3 cp s3://$TF_STATE_BUCKET/terraform.tfstate ./backup/

# Restore if needed
aws s3 cp ./backup/terraform.tfstate s3://$TF_STATE_BUCKET/
```

### Application Data
```bash
# Backup persistent volumes
kubectl get pv -o yaml > pv-backup.yaml

# Backup ConfigMaps and Secrets
kubectl get configmap -o yaml > configmap-backup.yaml
kubectl get secret -o yaml > secret-backup.yaml
```

## Support & Resources

- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)

---

Last Updated: 2025-09-11
Version: 1.0.0
