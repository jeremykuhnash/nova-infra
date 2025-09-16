# Terraform Infrastructure Visualizer

![Build Status](https://github.com/jeremykuhnash/nova-infra/actions/workflows/build-deploy.yml/badge.svg)
![ECR Push](https://github.com/jeremykuhnash/nova-infra/actions/workflows/ecr-push.yml/badge.svg)
![Terraform](https://github.com/jeremykuhnash/nova-infra/actions/workflows/terraform.yml/badge.svg)

Parses and visualizes Terraform configurations as interactive diagrams. Deployed on AWS EKS.

## Project Status

- Infrastructure: EKS, VPC, ECR, ALB deployed
- Application: Operational
- CI/CD: GitHub Actions
- Test Coverage: 97%
- Security: Trivy scanning
- Monitoring: Health checks configured

## Features

- Parses `.tf` files to extract resources, relationships, and dependencies
- Interactive React-based diagram with drag-and-drop interface
- Complete CI/CD pipeline via GitHub Actions
- Multi-stage Docker builds with production optimization
- Helm chart for Kubernetes deployment
- Horizontal Pod Autoscaler for production scaling
- Health monitoring and smoke tests
- Automated security scanning with Trivy

## Architecture

```
GitHub → GitHub Actions → AWS ECR
                       ↓
                   AWS EKS → ALB → Users
                       ↓
              TF Visualizer App
              (Flask + React)
```

## Prerequisites

- AWS Account with appropriate permissions
- Terraform >= 1.5.0
- kubectl >= 1.28
- Helm >= 3.0
- AWS CLI v2
- Python 3.12+ (development)
- Node.js 18+ (frontend)

## Quick Start

### Step 1: Setup
```bash
git clone https://github.com/jeremykuhnash/nova-infra.git
cd nova-infra
./setup.sh  # Installs AWS CLI, Terraform, GitHub CLI, kubectl
```

### Step 2: Configure AWS
```bash
aws configure  # Enter: Access Key, Secret Key, Region (us-east-1), Output (json)
aws sts get-caller-identity  # Verify
```

### Step 3: Initialize Backend
```bash
cd terraform
./init-backend.sh  # Creates S3 bucket and DynamoDB table
```

### Step 4: Deploy Infrastructure
```bash
terraform plan -out=tfplan
terraform apply tfplan  # Takes 15-20 minutes

export ECR_URL=$(terraform output -raw ecr_repository_url)
export EKS_CLUSTER=$(terraform output -raw eks_cluster_name)
```

### Step 5: Configure Kubernetes
```bash
aws eks update-kubeconfig --region us-east-1 --name $EKS_CLUSTER
kubectl get nodes  # Verify 3 nodes are Ready
kubectl config current-context  # Verify context
```

### Step 6: Build and Deploy Application

#### Option A: GitHub Actions Deploy
```bash
# Push to main triggers automatic deployment
git push origin main

# Or trigger manually
gh workflow run build-deploy.yml
gh run watch  # Monitor deployment
```

#### Option B: Manual Deploy
```bash
cd ../apps/hello-world
docker build -t tf-visualizer .

aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_URL

docker tag tf-visualizer:latest $ECR_URL:latest
docker push $ECR_URL:latest

helm install tf-visualizer ./helm/tf-visualizer \
  --set image.repository=$ECR_URL \
  --set image.tag=latest
```

### Step 7: Access Application
```bash
LB_URL=$(kubectl get service tf-visualizer -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl http://$LB_URL/health
echo "Application URL: http://$LB_URL"
```

### Step 8: Cleanup
```bash
helm uninstall tf-visualizer
cd terraform
terraform destroy -auto-approve
```

## GitHub Actions CI/CD

### Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `build-deploy.yml` | Push to main/develop | Test, build, deploy |
| `terraform.yml` | Push to main, manual | Infrastructure management |
| `ecr-push.yml` | Push to main/develop | Docker image management |
| `terraform-validate.yml` | PR to main | Terraform validation |

### Setup GitHub Secrets
```bash
# Required: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
./scripts/setup-github-secrets.sh  # Reads from ~/.aws/credentials
```

### Deploy via GitHub Actions
```bash
gh workflow run terraform.yml -f action=apply  # Infrastructure
gh workflow run build-deploy.yml               # Application
gh run watch                                   # Monitor
```

### Quality Gates
- Test Coverage: 97% minimum
- Security: Trivy scanning
- Validation: Terraform on PRs
- Testing: Smoke tests post-deploy
- Type Checking: mypy
- Linting: ESLint, ruff

## Features

### Parser
- Extracts resources, modules, variables from .tf files
- Supports nested modules and dependencies
- JSON output for visualization

### Visualization
- React frontend with drag-and-drop
- Color-coded resources by type
- Dependency arrows
- Zoom/pan controls

### API
- `GET /health` - Health check
- `GET /api/entities` - Cached entities
- `POST /api/parse` - Parse .tf files
- `POST /api/parse-directory` - Parse directory
- `GET /api/sample` - Demo data
- `GET /api/scan-paths` - Available directories

## Configuration

### Terraform
```hcl
# terraform/terraform.tfvars
project_name = "tf-visualizer"
environment  = "dev"
aws_region   = "us-east-1"
eks_cluster_version = "1.28"
node_group_instance_types = ["t3.medium"]
```

### Helm
```yaml
# helm/tf-visualizer/values.yaml
replicaCount: 2
image:
  repository: YOUR_ECR_URL
  tag: latest
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
```

## Testing

### Backend Tests
```bash
cd apps/hello-world
make test  # pytest with coverage (97%)
```

### Parser Test
```bash
cd apps/hello-world
python backend/parser.py ./test-terraform
```

### Local Development
```bash
# Backend
cd apps/hello-world
make dev

# Frontend
cd apps/hello-world/frontend
npm install && npm start

# Docker Compose
docker-compose -f docker-compose.local.yml up
```

### Quality Checks
```bash
cd apps/hello-world
make lint      # Linters
make format    # Auto-format
make security  # Security scan
make all       # Full validation
```

## Project Structure

```
nova-infra/
├── .github/workflows/      # CI/CD pipelines
├── terraform/              # Infrastructure as Code
│   ├── modules/           # EKS, networking, ECR
│   ├── bootstrap/         # Backend state setup
│   └── init-backend.sh    # Initialize backend
├── apps/hello-world/       # Application
│   ├── backend/           # Flask API + parser
│   ├── frontend/          # React UI
│   ├── tests/             # Test suite (97%)
│   └── Dockerfile         # Multi-stage build
├── helm/tf-visualizer/     # K8s manifests
├── scripts/                # Automation
└── setup.sh                # Environment setup
```

## Security & Monitoring

### Security
- IRSA for pod authentication
- Network policies
- Security groups
- Trivy scanning
- Non-root containers

### Monitoring
- CloudWatch insights
- Metrics server
- HPA auto-scaling
- Health probes

## Cleanup

```bash
helm uninstall tf-visualizer
cd terraform
terraform destroy -auto-approve
```

## Cost Estimation

| Service | Hourly | Monthly |
|---------|--------|----------|
| EKS Cluster | $0.10 | $73 |
| EC2 Nodes (3x t3.medium) | $0.13 | $92 |
| ALB | $0.03 | $18 |
| NAT Gateways (2x) | $0.09 | $66 |
| **Total** | **$0.35** | **$249** |

*Costs vary by region*

## Advanced Configuration

### Multi-Environment
```bash
cd terraform/environments/prod
terraform apply
```

### Custom Domain
```yaml
# helm/tf-visualizer/values.yaml
ingress:
  enabled: true
  hosts:
    - host: tf-viz.example.com
```

### PostgreSQL
```yaml
postgresql:
  enabled: true
  auth:
    database: tfviz
```

## Contributing

1. Fork repo
2. Create feature branch
3. Submit PR

## License

MIT

## Support

[Issues](https://github.com/your-org/nova-infra/issues)
