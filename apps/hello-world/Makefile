# Makefile for Terraform Visualizer Application

.PHONY: all format lint type-check clean test help
.PHONY: docker-build docker-run docker-push docker-clean
.PHONY: tf-init tf-plan tf-apply tf-destroy tf-output tf-clean
.PHONY: frontend-install frontend-lint frontend-format frontend-build frontend-dev frontend-test

# Default target - show available commands
.DEFAULT_GOAL := help

# Python interpreter
PYTHON := python3
VENV := venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

# Source directories
SRC_DIRS := backend tests
FRONTEND_DIR := frontend

# Docker settings
DOCKER_IMAGE := tf-visualizer
DOCKER_TAG := latest
DOCKER_REGISTRY :=
DOCKER_FULL_IMAGE := $(if $(DOCKER_REGISTRY),$(DOCKER_REGISTRY)/$(DOCKER_IMAGE),$(DOCKER_IMAGE))
DOCKER_PORT := 5000

# Terraform settings
TF_DIR := ../../terraform
TF_ENV := dev
TF_WORKSPACE := $(TF_ENV)
TF_VARS_FILE := $(TF_DIR)/environments/$(TF_ENV)/terraform.tfvars

# Help target
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@echo ""
	@echo "Python Development:"
	@echo "  make all         - Run format and lint checks"
	@echo "  make format      - Format code with ruff"
	@echo "  make lint        - Run linting with ruff"
	@echo "  make type-check  - Run type checking with mypy"
	@echo "  make test        - Run tests with pytest"
	@echo "  make clean       - Clean temporary files"
	@echo "  make venv        - Create virtual environment"
	@echo "  make install     - Install dependencies"
	@echo ""
	@echo "Frontend Development:"
	@echo "  make frontend-install  - Install frontend dependencies"
	@echo "  make frontend-lint     - Lint frontend with ESLint"
	@echo "  make frontend-format   - Format frontend with Prettier"
	@echo "  make frontend-build    - Build frontend for production"
	@echo "  make frontend-dev      - Run frontend dev server"
	@echo "  make frontend-test     - Run frontend tests"
	@echo ""
	@echo "Docker Operations:"
	@echo "  make docker-build    - Build Docker image"
	@echo "  make docker-run      - Run Docker container locally"
	@echo "  make docker-push     - Push image to registry"
	@echo "  make docker-clean    - Remove Docker images and containers"
	@echo ""
	@echo "Docker Compose Operations:"
	@echo "  make up              - Build and start services (recommended)"
	@echo "  make down            - Stop services"
	@echo "  make restart         - Restart with rebuild"
	@echo "  make compose-up      - Start services without rebuild"
	@echo "  make compose-down    - Stop services (same as 'make down')"
	@echo "  make compose-build   - Build services"
	@echo "  make compose-logs    - Show service logs"
	@echo "  make compose-restart - Restart services"
	@echo "  make compose-dev     - Start development services with hot reload"
	@echo "  make compose-prod    - Start production-like services with nginx"
	@echo "  make compose-clean   - Clean all compose resources"
	@echo ""
	@echo "Terraform Operations:"
	@echo "  make tf-init         - Initialize Terraform"
	@echo "  make tf-plan         - Show Terraform plan"
	@echo "  make tf-apply        - Apply Terraform changes"
	@echo "  make tf-destroy      - Destroy Terraform resources"
	@echo "  make tf-output       - Show Terraform outputs"
	@echo "  make tf-clean        - Clean Terraform files"
	@echo ""
	@echo "Full Deployment:"
	@echo "  make deploy          - Full deployment (test, build, push, terraform)"
	@echo "  make deploy-local    - Local deployment (test, build, run)"
	@echo ""
	@echo "Quick Start:"
	@echo "  make install         # Install all dependencies"
	@echo "  make all            # Run all quality checks and build"
	@echo "  make up             # Build and run the application"
	@echo "  make down           # Stop the application"
	@echo "  make restart        # Rebuild and restart application"

# Main target - runs quality checks and builds all artifacts
all: install format lint type-check test frontend-build docker-build

# Create virtual environment
venv:
	@echo "Creating virtual environment..."
	@$(PYTHON) -m venv $(VENV)
	@echo "Virtual environment created."

# Install dependencies
install: venv frontend-install
	@echo "Installing backend dependencies..."
	@$(VENV_PIP) install --upgrade pip
	@$(VENV_PIP) install -r requirements.txt
	@$(VENV_PIP) install ruff mypy types-flask types-requests
	@echo "All dependencies installed."

# Format code with ruff
format:
	@echo "Formatting code with ruff..."
	@if [ -d "$(VENV)" ]; then \
		$(VENV)/bin/ruff format $(SRC_DIRS); \
		$(VENV)/bin/ruff check --fix $(SRC_DIRS); \
	else \
		ruff format $(SRC_DIRS); \
		ruff check --fix $(SRC_DIRS); \
	fi
	@echo "Code formatting complete."

# Lint code with ruff
lint:
	@echo "Linting code with ruff..."
	@if [ -d "$(VENV)" ]; then \
		$(VENV)/bin/ruff check $(SRC_DIRS); \
	else \
		ruff check $(SRC_DIRS); \
	fi
	@echo "Linting complete."

# Type check with mypy
type-check:
	@echo "Type checking with mypy..."
	@if [ -d "$(VENV)" ]; then \
		$(VENV)/bin/mypy $(SRC_DIRS) --ignore-missing-imports; \
	else \
		mypy $(SRC_DIRS) --ignore-missing-imports; \
	fi
	@echo "Type checking complete."

# Run tests
test:
	@echo "Running tests..."
	@if [ -d "$(VENV)" ]; then \
		$(VENV_PYTHON) -m pytest tests/ -v --cov=backend --cov-report=term-missing; \
	else \
		pytest tests/ -v --cov=backend --cov-report=term-missing; \
	fi

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete."

# Docker build target
docker-build:
	@echo "Building Docker image $(DOCKER_FULL_IMAGE):$(DOCKER_TAG)..."
	@docker build -t $(DOCKER_FULL_IMAGE):$(DOCKER_TAG) .
	@echo "Docker image built successfully."

# Docker run target
docker-run:
	@echo "Running Docker container..."
	@docker run -d \
		--name $(DOCKER_IMAGE) \
		-p $(DOCKER_PORT):$(DOCKER_PORT) \
		-e PORT=$(DOCKER_PORT) \
		$(DOCKER_FULL_IMAGE):$(DOCKER_TAG)
	@echo "Container running at http://localhost:$(DOCKER_PORT)"

# Docker push target
docker-push:
	@echo "Pushing Docker image to registry..."
	@if [ -z "$(DOCKER_REGISTRY)" ]; then \
		echo "Error: DOCKER_REGISTRY not set. Use: make docker-push DOCKER_REGISTRY=your-registry"; \
		exit 1; \
	fi
	@docker push $(DOCKER_FULL_IMAGE):$(DOCKER_TAG)
	@echo "Docker image pushed successfully."

# Docker clean target
docker-clean:
	@echo "Cleaning Docker resources..."
	@docker stop $(DOCKER_IMAGE) 2>/dev/null || true
	@docker rm $(DOCKER_IMAGE) 2>/dev/null || true
	@docker rmi $(DOCKER_FULL_IMAGE):$(DOCKER_TAG) 2>/dev/null || true
	@echo "Docker resources cleaned."

# Docker Compose targets
up:
	@echo "Building and starting services with docker-compose..."
	@docker-compose up --build --force-recreate -d
	@echo "Services started. Application available at http://localhost:5000"

restart:
	@echo "Restarting services with rebuild..."
	@docker-compose down
	@docker-compose up --build --force-recreate -d
	@echo "Services restarted. Application available at http://localhost:5000"

down:
	@echo "Stopping services..."
	@docker-compose down
	@echo "Services stopped."

compose-up:
	@echo "Starting services with docker-compose..."
	@docker-compose up -d
	@echo "Services started. Application available at http://localhost:5000"

compose-down:
	@echo "Stopping services..."
	@docker-compose down
	@echo "Services stopped."

compose-build:
	@echo "Building services with docker-compose..."
	@docker-compose build
	@echo "Services built."

compose-logs:
	@echo "Showing service logs..."
	@docker-compose logs -f

compose-restart:
	@echo "Restarting services..."
	@docker-compose restart
	@echo "Services restarted."

# Development mode with hot reload
compose-dev:
	@echo "Starting development services with hot reload..."
	@docker-compose -f docker-compose.dev.yml up
	@echo "Development services started."

compose-dev-down:
	@echo "Stopping development services..."
	@docker-compose -f docker-compose.dev.yml down
	@echo "Development services stopped."

# Production-like testing with nginx
compose-prod:
	@echo "Starting production-like services with nginx..."
	@docker-compose --profile with-nginx up -d
	@echo "Production services started. Application available at http://localhost:80"

# Clean all compose resources
compose-clean:
	@echo "Cleaning all docker-compose resources..."
	@docker-compose down -v --rmi all
	@docker-compose -f docker-compose.dev.yml down -v --rmi all
	@echo "All compose resources cleaned."

# Terraform init
tf-init:
	@echo "Initializing Terraform..."
	@cd $(TF_DIR) && terraform init
	@echo "Terraform initialized."

# Terraform plan
tf-plan: tf-init
	@echo "Creating Terraform plan..."
	@cd $(TF_DIR) && terraform workspace select $(TF_WORKSPACE) 2>/dev/null || terraform workspace new $(TF_WORKSPACE)
	@cd $(TF_DIR) && terraform plan -var-file=$(TF_VARS_FILE) -out=tfplan
	@echo "Terraform plan created."

# Terraform apply
tf-apply: tf-plan
	@echo "Applying Terraform changes..."
	@cd $(TF_DIR) && terraform apply tfplan
	@echo "Terraform changes applied."

# Terraform destroy
tf-destroy:
	@echo "Destroying Terraform resources..."
	@cd $(TF_DIR) && terraform workspace select $(TF_WORKSPACE)
	@cd $(TF_DIR) && terraform destroy -var-file=$(TF_VARS_FILE) -auto-approve
	@echo "Terraform resources destroyed."

# Terraform output
tf-output:
	@echo "Showing Terraform outputs..."
	@cd $(TF_DIR) && terraform workspace select $(TF_WORKSPACE)
	@cd $(TF_DIR) && terraform output

# Terraform clean
tf-clean:
	@echo "Cleaning Terraform files..."
	@rm -rf $(TF_DIR)/.terraform
	@rm -f $(TF_DIR)/.terraform.lock.hcl
	@rm -f $(TF_DIR)/tfplan
	@rm -f $(TF_DIR)/terraform.tfstate*
	@echo "Terraform files cleaned."

# Full deployment pipeline
deploy: test docker-build docker-push tf-apply
	@echo "Full deployment completed!"

# Local deployment pipeline
deploy-local: test docker-build docker-run
	@echo "Local deployment completed!"

# CI/CD targets for GitHub Actions
ci-test: venv install format lint type-check test
	@echo "CI tests completed!"

ci-build: ci-test docker-build
	@echo "CI build completed!"

ci-deploy: ci-build docker-push tf-apply
	@echo "CI deployment completed!"

# Frontend targets
frontend-install:
	@echo "Installing frontend dependencies..."
	@cd $(FRONTEND_DIR) && npm install
	@echo "Frontend dependencies installed."

frontend-lint:
	@echo "Linting frontend code with ESLint..."
	@cd $(FRONTEND_DIR) && npm run lint
	@echo "Frontend linting complete."

frontend-format:
	@echo "Formatting frontend code with Prettier..."
	@cd $(FRONTEND_DIR) && npm run format
	@echo "Frontend formatting complete."

frontend-build: frontend-install
	@echo "Building frontend for production..."
	@cd $(FRONTEND_DIR) && npm run build
	@echo "Frontend build complete."

frontend-dev:
	@echo "Starting frontend development server..."
	@cd $(FRONTEND_DIR) && npm start

frontend-test:
	@echo "Running frontend tests..."
	@cd $(FRONTEND_DIR) && npm test
	@echo "Frontend tests complete."

# Combined frontend quality check
frontend-all: frontend-install frontend-format frontend-lint frontend-build
	@echo "Frontend quality checks complete!"
