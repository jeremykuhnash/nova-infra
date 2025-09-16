# Terraform Makefile for nova-infra
# Provides linting, security scanning, and common terraform operations

.PHONY: help init plan apply destroy lint security validate fmt clean all

# Default target
.DEFAULT_GOAL := help

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Check for required tools
REQUIRED_TOOLS := terraform
OPTIONAL_TOOLS := tflint tfsec

help: ## Show this help message
	@echo "$(CYAN)Nova Infrastructure - Terraform Makefile$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Tool Status:$(NC)"
	@for tool in $(REQUIRED_TOOLS); do \
		if command -v $$tool >/dev/null 2>&1; then \
			echo "  ✅ $$tool: $$($$tool version -json 2>/dev/null | jq -r '.terraform_version' || $$tool version | head -n1)"; \
		else \
			echo "  ❌ $$tool: NOT FOUND (required)"; \
		fi; \
	done
	@for tool in $(OPTIONAL_TOOLS); do \
		if command -v $$tool >/dev/null 2>&1; then \
			echo "  ✅ $$tool: $$($$tool --version 2>&1 | head -n1)"; \
		else \
			echo "  ⚠️  $$tool: NOT FOUND (optional - run ../scripts/install-terraform-tools.sh)"; \
		fi; \
	done

init: ## Initialize Terraform backend and providers
	@echo "$(GREEN)[INFO]$(NC) Initializing Terraform..."
	@if [ ! -f backend.tf ]; then \
		echo "$(YELLOW)[WARN]$(NC) backend.tf not found. Running init-backend.sh..."; \
		./init-backend.sh; \
	fi
	terraform init

validate: ## Validate Terraform configuration
	@echo "$(GREEN)[INFO]$(NC) Validating Terraform configuration..."
	terraform validate

fmt: ## Format Terraform files
	@echo "$(GREEN)[INFO]$(NC) Formatting Terraform files..."
	terraform fmt -recursive

fmt-check: ## Check Terraform formatting (CI mode)
	@echo "$(GREEN)[INFO]$(NC) Checking Terraform formatting..."
	terraform fmt -check -recursive

lint: ## Run tflint on Terraform files
	@if command -v tflint >/dev/null 2>&1; then \
		echo "$(GREEN)[INFO]$(NC) Running tflint..."; \
		tflint --init && tflint; \
	else \
		echo "$(YELLOW)[WARN]$(NC) tflint not installed. Run: ../scripts/install-terraform-tools.sh"; \
		exit 1; \
	fi

security: ## Run tfsec security scanner
	@if command -v tfsec >/dev/null 2>&1; then \
		echo "$(GREEN)[INFO]$(NC) Running tfsec security scan..."; \
		tfsec . --no-color; \
	else \
		echo "$(YELLOW)[WARN]$(NC) tfsec not installed. Run: ../scripts/install-terraform-tools.sh"; \
		exit 1; \
	fi

plan: init validate ## Create Terraform plan
	@echo "$(GREEN)[INFO]$(NC) Creating Terraform plan..."
	terraform plan -out=tfplan

apply: ## Apply Terraform changes (requires existing plan)
	@if [ ! -f tfplan ]; then \
		echo "$(RED)[ERROR]$(NC) No plan file found. Run 'make plan' first."; \
		exit 1; \
	fi
	@echo "$(YELLOW)[WARN]$(NC) About to apply Terraform changes..."
	terraform apply tfplan

destroy: ## Destroy all Terraform-managed infrastructure
	@echo "$(RED)[WARN]$(NC) About to destroy all infrastructure!"
	@echo "$(RED)[WARN]$(NC) This action cannot be undone."
	@read -p "Type 'yes' to confirm: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		terraform destroy -auto-approve; \
	else \
		echo "$(GREEN)[INFO]$(NC) Destroy cancelled."; \
	fi

clean: ## Clean up generated files
	@echo "$(GREEN)[INFO]$(NC) Cleaning up..."
	@rm -f tfplan
	@rm -f *.tfplan
	@rm -rf .terraform.lock.hcl.backup
	@echo "$(GREEN)[INFO]$(NC) Clean complete"

all: fmt validate lint security ## Run all checks (format, validate, lint, security)
	@echo "$(GREEN)✅ All checks passed!$(NC)"

ci: fmt-check validate lint security ## Run CI checks (non-modifying)
	@echo "$(GREEN)✅ CI checks passed!$(NC)"

install-tools: ## Install terraform linting and security tools
	@echo "$(GREEN)[INFO]$(NC) Installing Terraform tools..."
	@../scripts/install-terraform-tools.sh

workspace-list: ## List Terraform workspaces
	@echo "$(GREEN)[INFO]$(NC) Terraform workspaces:"
	@terraform workspace list

workspace-select: ## Select a workspace (use with WORKSPACE=name)
	@if [ -z "$(WORKSPACE)" ]; then \
		echo "$(RED)[ERROR]$(NC) WORKSPACE not specified. Usage: make workspace-select WORKSPACE=dev"; \
		exit 1; \
	fi
	@echo "$(GREEN)[INFO]$(NC) Selecting workspace: $(WORKSPACE)"
	terraform workspace select -or-create $(WORKSPACE)

outputs: ## Show Terraform outputs
	@terraform output

refresh: ## Refresh Terraform state
	@echo "$(GREEN)[INFO]$(NC) Refreshing Terraform state..."
	terraform refresh

graph: ## Generate resource dependency graph
	@echo "$(GREEN)[INFO]$(NC) Generating dependency graph..."
	@terraform graph | dot -Tpng > terraform-graph.png
	@echo "$(GREEN)[INFO]$(NC) Graph saved to terraform-graph.png"
