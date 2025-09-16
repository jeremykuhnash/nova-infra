# Top-level Makefile for Nova Infrastructure

.PHONY: help all test build deploy clean
.PHONY: app-help app-all app-test app-build app-deploy app-clean
.PHONY: tf-help tf-init tf-plan tf-apply tf-destroy tf-destroy-confirm tf-output tf-lint tf-security
.PHONY: aws-auth aws-auth-check aws-auth-test
.PHONY: deps-graph deps-analyze validate-tools security-scan
.PHONY: pre-commit-install pre-commit-run format lint typecheck

# Default target - show available commands
.DEFAULT_GOAL := help

# Application directory
APP_DIR := apps/tf-visualizer

# Terraform directory
TF_DIR := terraform

# Help target
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@echo ""
	@echo "Quick Commands:"
	@echo "  make all             - Run all quality checks and builds"
	@echo "  make test            - Run all tests"
	@echo "  make build           - Build all components"
	@echo "  make deploy          - Deploy infrastructure and applications"
	@echo "  make clean           - Clean all build artifacts"
	@echo ""
	@echo "Application Commands (apps/tf-visualizer):"
	@echo "  make app-help        - Show application-specific targets"
	@echo "  make app-all         - Run all app checks and build"
	@echo "  make app-test        - Run application tests"
	@echo "  make app-build       - Build application Docker image"
	@echo "  make app-deploy      - Deploy application"
	@echo "  make app-clean       - Clean application artifacts"
	@echo ""
	@echo "Infrastructure Commands (terraform):"
	@echo "  make tf-init         - Initialize Terraform"
	@echo "  make tf-plan         - Create Terraform plan"
	@echo "  make tf-apply        - Apply Terraform changes"
	@echo "  make tf-destroy      - Destroy infrastructure (auto-approve)"
	@echo "  make tf-destroy-confirm - Destroy infrastructure (with confirmation)"
	@echo "  make tf-output       - Show Terraform outputs"
	@echo "  make tf-lint         - Run Terraform linting (tflint)"
	@echo "  make tf-security     - Run Terraform security scan (tfsec)"
	@echo ""
	@echo "AWS Authentication Commands:"
	@echo "  make aws-auth        - Interactive AWS authentication helper"
	@echo "  make aws-auth-check  - Quick authentication status check"
	@echo "  make aws-auth-test   - Test AWS permissions"
	@echo ""
	@echo "CI/CD Container Commands:"
	@echo "  make ci-build        - Build CI/CD Docker image with all tools"
	@echo "  make ci-shell        - Start interactive CI container"
	@echo "  make ci-validate     - Run all validations in CI container"
	@echo "  make ci-terraform    - Start Terraform tools container"
	@echo "  make ci-python       - Start Python development container"
	@echo ""
	@echo "Quality & Analysis Commands:"
	@echo "  make validate-tools  - Check all required tools are installed"
	@echo "  make security-scan   - Run all security scans"
	@echo "  make deps-graph      - Generate dependency graphs"
	@echo "  make deps-analyze    - Analyze project dependencies"
	@echo "  make pre-commit-install - Install pre-commit hooks"
	@echo "  make pre-commit-run  - Run pre-commit hooks"
	@echo "  make format          - Format all code"
	@echo "  make lint            - Lint all code"
	@echo "  make typecheck       - Run type checking"
	@echo ""
	@echo "Quick Start:"
	@echo "  make app-help        # See all app-specific commands"
	@echo "  make all            # Run all quality checks"
	@echo "  make deploy         # Full deployment"

# Main targets that delegate to subdirectories
all: app-all

test: app-test

build: app-build

deploy: app-deploy

clean: app-clean

# Application-specific targets
app-help:
	@$(MAKE) -C $(APP_DIR) help

app-all:
	@echo "Running all application checks and builds..."
	@$(MAKE) -C $(APP_DIR) all

app-test:
	@echo "Running application tests..."
	@$(MAKE) -C $(APP_DIR) test

app-build:
	@echo "Building application..."
	@$(MAKE) -C $(APP_DIR) docker-build

app-deploy:
	@echo "Deploying application..."
	@$(MAKE) -C $(APP_DIR) deploy

app-clean:
	@echo "Cleaning application artifacts..."
	@$(MAKE) -C $(APP_DIR) clean

app-install:
	@echo "Installing application dependencies..."
	@$(MAKE) -C $(APP_DIR) install

app-format:
	@echo "Formatting application code..."
	@$(MAKE) -C $(APP_DIR) format

app-lint:
	@echo "Linting application code..."
	@$(MAKE) -C $(APP_DIR) lint

# Frontend-specific shortcuts
frontend-install:
	@$(MAKE) -C $(APP_DIR) frontend-install

frontend-build:
	@$(MAKE) -C $(APP_DIR) frontend-build

frontend-dev:
	@$(MAKE) -C $(APP_DIR) frontend-dev

# Terraform targets
tf-init-backend:
	@echo "Initializing Terraform backend..."
	@cd $(TF_DIR) && ./init-backend.sh

tf-init:
	@echo "Initializing Terraform..."
	@cd $(TF_DIR) && terraform init

tf-plan:
	@echo "Creating Terraform plan..."
	@cd $(TF_DIR) && terraform workspace select default 2>/dev/null || true
	@cd $(TF_DIR) && terraform plan

tf-apply:
	@echo "Applying Terraform changes..."
	@cd $(TF_DIR) && terraform workspace select default 2>/dev/null || true
	@cd $(TF_DIR) && terraform apply

tf-destroy:
	@echo "Destroying Terraform infrastructure..."
	@cd $(TF_DIR) && terraform workspace select default 2>/dev/null || true
	@cd $(TF_DIR) && terraform destroy -auto-approve

tf-destroy-confirm:
	@echo "Destroying Terraform infrastructure (with confirmation)..."
	@cd $(TF_DIR) && terraform workspace select default 2>/dev/null || true
	@cd $(TF_DIR) && terraform destroy

tf-output:
	@cd $(TF_DIR) && terraform workspace select default 2>/dev/null || true
	@cd $(TF_DIR) && terraform output

# Docker shortcuts
up:
	@$(MAKE) -C $(APP_DIR) up

down:
	@$(MAKE) -C $(APP_DIR) down

restart:
	@$(MAKE) -C $(APP_DIR) restart

docker-build:
	@$(MAKE) -C $(APP_DIR) docker-build

docker-run:
	@$(MAKE) -C $(APP_DIR) docker-run

docker-push:
	@$(MAKE) -C $(APP_DIR) docker-push

docker-clean:
	@$(MAKE) -C $(APP_DIR) docker-clean

# CI/CD targets
ci-test:
	@$(MAKE) -C $(APP_DIR) ci-test

ci-app-build:
	@$(MAKE) -C $(APP_DIR) ci-build

ci-deploy:
	@$(MAKE) -C $(APP_DIR) ci-deploy

# AWS Authentication targets
aws-auth:
	@echo "Starting AWS Authentication Helper..."
	@./scripts/aws-auth.sh

aws-auth-check:
	@echo "Checking AWS authentication status..."
	@./scripts/aws-auth.sh quick

aws-auth-test:
	@echo "Testing AWS permissions..."
	@./scripts/aws-auth.sh test

# CI/CD Container targets
ci-build:
	@echo "Building CI/CD Docker image with all tools..."
	@docker build -f Dockerfile.ci -t nova-infra-ci:latest .

ci-shell:
	@echo "Starting CI/CD container with all tools..."
	@docker-compose -f docker-compose.ci.yml run --rm ci-tools

ci-validate:
	@echo "Running all validations in CI container..."
	@docker-compose -f docker-compose.ci.yml run --rm validate-all

ci-terraform:
	@echo "Starting Terraform tools container..."
	@docker-compose -f docker-compose.ci.yml run --rm terraform-tools

ci-python:
	@echo "Starting Python development container..."
	@docker-compose -f docker-compose.ci.yml run --rm python-dev

# Additional Terraform tool targets
tf-lint:
	@echo "Running Terraform linting..."
	@cd $(TF_DIR) && tflint --init && tflint

tf-security:
	@echo "Running Terraform security scan..."
	@cd $(TF_DIR) && tfsec .

# Dependency analysis targets
deps-graph:
	@echo "Generating dependency graphs..."
	@python scripts/generate-deps.py --format all

deps-analyze:
	@echo "Analyzing project dependencies..."
	@python scripts/generate-deps.py --format json

# Tool validation target
validate-tools:
	@echo "Validating tool installations..."
	@echo "Checking required tools from tools.json..."
	@terraform version || echo "❌ terraform not found"
	@tflint --version || echo "❌ tflint not found"
	@tfsec --version || echo "❌ tfsec not found"
	@kubectl version --client || echo "❌ kubectl not found"
	@helm version || echo "❌ helm not found"
	@python3 --version || echo "❌ python3 not found"
	@poetry --version || echo "❌ poetry not found"
	@node --version || echo "❌ node not found"
	@npm --version || echo "❌ npm not found"
	@aws --version || echo "❌ aws-cli not found"
	@gh --version || echo "❌ gh not found"
	@docker --version || echo "❌ docker not found"
	@pre-commit --version || echo "❌ pre-commit not found"
	@echo "✅ Tool validation complete"

# Security scanning targets
security-scan:
	@echo "Running security scans..."
	@$(MAKE) -C $(APP_DIR) security || echo "⚠️  Application security scan failed"
	@$(MAKE) tf-security || echo "⚠️  Terraform security scan failed"

# Pre-commit targets
pre-commit-install:
	@echo "Installing pre-commit hooks..."
	@pre-commit install

pre-commit-run:
	@echo "Running pre-commit hooks..."
	@pre-commit run --all-files

# Code quality targets
format:
	@echo "Formatting all code..."
	@$(MAKE) -C $(APP_DIR) format

lint:
	@echo "Linting all code..."
	@$(MAKE) -C $(APP_DIR) lint
	@$(MAKE) tf-lint

typecheck:
	@echo "Running type checks..."
	@$(MAKE) -C $(APP_DIR) typecheck
