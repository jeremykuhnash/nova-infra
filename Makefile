# Top-level Makefile for Nova Infrastructure

.PHONY: help all test build deploy clean
.PHONY: app-help app-all app-test app-build app-deploy app-clean
.PHONY: tf-help tf-init tf-plan tf-apply tf-destroy

# Default target - show available commands
.DEFAULT_GOAL := help

# Application directory
APP_DIR := apps/hello-world

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
	@echo "Application Commands (apps/hello-world):"
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
	@echo "  make tf-destroy      - Destroy infrastructure"
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
tf-init:
	@echo "Initializing Terraform..."
	@$(MAKE) -C $(APP_DIR) tf-init

tf-plan:
	@echo "Creating Terraform plan..."
	@$(MAKE) -C $(APP_DIR) tf-plan

tf-apply:
	@echo "Applying Terraform changes..."
	@$(MAKE) -C $(APP_DIR) tf-apply

tf-destroy:
	@echo "Destroying Terraform infrastructure..."
	@$(MAKE) -C $(APP_DIR) tf-destroy

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

ci-build:
	@$(MAKE) -C $(APP_DIR) ci-build

ci-deploy:
	@$(MAKE) -C $(APP_DIR) ci-deploy
