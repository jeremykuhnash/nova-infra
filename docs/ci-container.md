# CI/CD Container Documentation

## Overview

The CI/CD container provides a consistent environment with all necessary tools for development, testing, and validation of the Nova Infrastructure project.

## Included Tools

### Infrastructure Tools
- **Terraform**: Latest version for infrastructure as code
- **TFLint**: Terraform linter for best practices
- **Trivy**: Security scanning (replaces tfsec)
- **AWS CLI**: AWS command line interface
- **kubectl**: Kubernetes command line tool
- **Helm**: Kubernetes package manager

### Development Tools
- **Python 3.12**: With pip and venv
- **Node.js 18**: For frontend development
- **Git**: Version control
- **GitHub CLI**: GitHub operations
- **Make**: Build automation

### Testing & Validation Tools
- **pre-commit**: Git hook framework
- **ruff**: Python linter and formatter
- **mypy**: Python type checker
- **pytest**: Python testing framework
- **pytest-cov**: Coverage reporting
- **bandit**: Python security linter
- **safety**: Python dependency checker

## Usage

### Building the CI Container

```bash
# Build the CI/CD Docker image
make ci-build
```

### Running the CI Container

#### Interactive Shell
```bash
# Start an interactive shell with all tools
make ci-shell

# You can then run any commands:
terraform --version
tflint --version
pre-commit run --all-files
```

#### Run All Validations
```bash
# Run all validations in one command
make ci-validate
```

This runs:
- Pre-commit hooks on all files
- Terraform format, validate, and lint
- Python tests with coverage
- Frontend build

#### Terraform Development
```bash
# Start container in terraform directory
make ci-terraform

# Now you can run terraform commands:
terraform init
terraform plan
terraform apply
```

#### Python Development
```bash
# Start container in apps/hello-world directory
make ci-python

# Run Python tests:
pytest tests --cov=backend
```

### Docker Compose Usage

You can also use docker-compose directly:

```bash
# Start the CI tools container
docker-compose -f docker-compose.ci.yml run --rm ci-tools

# Run validations
docker-compose -f docker-compose.ci.yml run --rm validate-all

# Start Terraform tools
docker-compose -f docker-compose.ci.yml run --rm terraform-tools

# Start Python dev environment
docker-compose -f docker-compose.ci.yml run --rm python-dev
```

### GitHub Actions Integration

The CI container is automatically used in GitHub Actions workflows:

1. **ci.yml**: Main CI pipeline that uses the container for all checks
2. **build-deploy.yml**: Can optionally use the container for consistent environment

### Local Development Tips

1. **AWS Credentials**: The container mounts `~/.aws` for AWS access
   ```bash
   # Container will use your AWS credentials
   make ci-terraform
   aws s3 ls  # Works with your credentials
   ```

2. **Kubectl Config**: The container mounts `~/.kube` for Kubernetes access
   ```bash
   make ci-shell
   kubectl get pods  # Uses your kubeconfig
   ```

3. **Environment Variables**: Pass environment variables
   ```bash
   AWS_PROFILE=production make ci-terraform
   ```

4. **Custom Commands**: Run specific commands
   ```bash
   docker run --rm -v $(pwd):/workspace nova-infra-ci:latest \
     bash -c "cd /workspace && pre-commit run --all-files"
   ```

## Troubleshooting

### Container Build Issues
- Ensure Docker is running
- Check Docker has enough disk space
- Try `docker system prune` to clean up

### Permission Issues
- The container runs as root by default
- For production, consider using the `ciuser` user

### Tool Version Issues
- The Dockerfile installs latest versions by default
- Pin specific versions in Dockerfile if needed

## Maintenance

### Updating Tools
1. Edit `Dockerfile.ci` to update tool versions
2. Rebuild the container: `make ci-build`
3. Test all validations: `make ci-validate`
4. Commit changes

### Adding New Tools
1. Add installation commands to `Dockerfile.ci`
2. Update this documentation
3. Add corresponding Make targets if needed
4. Test in CI pipeline
