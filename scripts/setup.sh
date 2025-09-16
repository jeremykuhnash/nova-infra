#!/bin/bash
# Nova Infrastructure Setup Script
# Installs all required tools, dependencies, and configures the development environment

set -euo pipefail

# Determine project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
}

# Install system packages (optional)
install_system_packages() {
    log_section "Installing System Packages"

    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        log_warn "System package installation only supported on Linux"
        return 0
    fi

    if ! command -v apt &> /dev/null; then
        log_warn "APT package manager not found. Skipping system packages."
        return 0
    fi

    log_info "Updating package lists..."
    sudo apt update

    log_info "Installing development tools and Python dependencies..."
    sudo apt install -y \
        build-essential \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        git \
        curl \
        wget \
        unzip \
        jq \
        pkg-config \
        software-properties-common

    log_info "✅ System packages installed"
}

# Install AWS CLI v2
install_aws_cli() {
    if command -v aws &> /dev/null; then
        log_info "AWS CLI already installed: $(aws --version)"
        return 0
    fi

    log_section "Installing AWS CLI v2"

    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
    unzip -q /tmp/awscliv2.zip -d /tmp/
    sudo /tmp/aws/install
    rm -rf /tmp/awscliv2.zip /tmp/aws/

    log_info "✅ AWS CLI installed: $(aws --version)"
}

# Install Terraform
install_terraform() {
    if command -v terraform &> /dev/null; then
        log_info "Terraform already installed: $(terraform version | head -1)"
        return 0
    fi

    log_section "Installing Terraform"

    wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
    sudo apt update && sudo apt install -y terraform

    log_info "✅ Terraform installed: $(terraform version | head -1)"
}

# Install kubectl
install_kubectl() {
    if command -v kubectl &> /dev/null; then
        log_info "kubectl already installed: $(kubectl version --client --short 2>/dev/null || echo 'installed')"
        return 0
    fi

    log_section "Installing kubectl"

    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
    rm kubectl

    log_info "✅ kubectl installed"
}

# Install GitHub CLI
install_gh_cli() {
    if command -v gh &> /dev/null; then
        log_info "GitHub CLI already installed: $(gh --version | head -1)"
        return 0
    fi

    log_section "Installing GitHub CLI"

    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt update && sudo apt install -y gh

    log_info "✅ GitHub CLI installed"
}

# Check for required system tools
check_requirements() {
    log_section "Checking System Requirements"

    local missing_tools=()
    local required_tools=("python3" "pip" "docker" "aws" "terraform" "kubectl" "node" "npm")

    for tool in "${required_tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            version_info=""
            case "$tool" in
                python3)
                    version_info=$(python3 --version 2>&1)
                    ;;
                terraform)
                    version_info=$(terraform version -json 2>/dev/null | jq -r '.terraform_version' || terraform version | head -n1)
                    ;;
                docker)
                    version_info=$(docker --version 2>&1)
                    ;;
                aws)
                    version_info=$(aws --version 2>&1)
                    ;;
                helm)
                    version_info=$(helm version --short 2>&1)
                    ;;
                kubectl)
                    version_info=$(kubectl version --client --short 2>&1 || kubectl version --client -o json | jq -r .clientVersion.gitVersion)
                    ;;
                node)
                    version_info=$(node --version 2>&1)
                    ;;
                npm)
                    version_info=$(npm --version 2>&1)
                    ;;
                *)
                    version_info=$($tool --version 2>&1 | head -n1)
                    ;;
            esac
            log_info "✅ $tool: $version_info"
        else
            log_error "❌ $tool: NOT FOUND"
            missing_tools+=("$tool")
        fi
    done

    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_error ""
        log_error "Missing required tools: ${missing_tools[*]}"
        log_error "Please install the missing tools before continuing."
        exit 1
    fi
}

# Setup Python environment
setup_python() {
    log_section "Setting up Python Environment"

    cd "$PROJECT_ROOT/apps/tf-visualizer"

    # Check if Poetry is installed
    if ! command -v poetry &> /dev/null; then
        log_info "Installing Poetry..."
        curl -sSL https://install.python-poetry.org | python3 -
        export PATH="$HOME/.local/bin:$PATH"
    else
        log_info "Poetry already installed: $(poetry --version)"
    fi

    # Install dependencies with Poetry
    log_info "Installing Python dependencies with Poetry..."
    poetry install

    log_info "✅ Python environment setup complete"
}

# Setup Node.js environment
setup_node() {
    log_section "Setting up Node.js Environment"

    cd "$PROJECT_ROOT/apps/tf-visualizer/frontend"

    log_info "Installing Node.js dependencies..."
    npm install

    log_info "✅ Node.js environment setup complete"
}

# Install Terraform tools
install_terraform_tools() {
    log_section "Installing Terraform Tools"

    # Create work/bin directory
    mkdir -p "$PROJECT_ROOT/work/bin"

    # Run the terraform tools installer
    "$SCRIPT_DIR/install-terraform-tools.sh"

    # Add to PATH for this session
    export PATH="$PROJECT_ROOT/work/bin:$PATH"

    log_info "✅ Terraform tools installed to work/bin/"
}

# Initialize Terraform backend
init_terraform() {
    log_section "Initializing Terraform"

    cd "$PROJECT_ROOT/terraform"

    if [ ! -f "backend.tf" ]; then
        log_info "Initializing Terraform backend..."
        ./init-backend.sh
    else
        log_info "Terraform backend already configured"
    fi

    log_info "Running terraform init..."
    terraform init

    log_info "✅ Terraform initialization complete"
}

# Setup pre-commit hooks
setup_precommit() {
    log_section "Setting up Pre-commit Hooks"

    cd "$PROJECT_ROOT"

    if command -v pre-commit &> /dev/null; then
        log_info "Installing pre-commit hooks..."
        pre-commit install
        log_info "✅ Pre-commit hooks installed"
    else
        log_warn "pre-commit not found. Install with: poetry add --dev pre-commit"
    fi
}

# Configure AWS CLI
configure_aws() {
    log_section "Checking AWS Configuration"

    if aws sts get-caller-identity &> /dev/null; then
        identity=$(aws sts get-caller-identity)
        account=$(echo "$identity" | jq -r '.Account')
        arn=$(echo "$identity" | jq -r '.Arn')
        log_info "✅ AWS configured - Account: $account"
        log_info "   ARN: $arn"
    else
        log_warn "AWS CLI not configured. Run 'aws configure' to set up credentials"
    fi
}

# Main setup flow
main() {
    log_section "Nova Infrastructure Setup"
    log_info "Project root: $PROJECT_ROOT"

    # Parse command line arguments
    INSTALL_SYSTEM=false
    SKIP_CHECKS=false
    SKIP_PYTHON=false
    SKIP_NODE=false
    SKIP_TERRAFORM=false
    SKIP_AWS=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --install-system)
                INSTALL_SYSTEM=true
                shift
                ;;
            --skip-checks)
                SKIP_CHECKS=true
                shift
                ;;
            --skip-python)
                SKIP_PYTHON=true
                shift
                ;;
            --skip-node)
                SKIP_NODE=true
                shift
                ;;
            --skip-terraform)
                SKIP_TERRAFORM=true
                shift
                ;;
            --skip-aws)
                SKIP_AWS=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --install-system   Install system packages and tools (AWS CLI, Terraform, kubectl, gh)"
                echo "  --skip-checks      Skip system requirements check"
                echo "  --skip-python      Skip Python environment setup"
                echo "  --skip-node        Skip Node.js environment setup"
                echo "  --skip-terraform   Skip Terraform initialization"
                echo "  --skip-aws         Skip AWS configuration check"
                echo "  --help             Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0                        # Run complete setup"
                echo "  $0 --install-system       # Install system tools first, then run setup"
                echo "  $0 --skip-python --skip-node  # Skip language-specific setups"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                log_info "Run '$0 --help' for usage information"
                exit 1
                ;;
        esac
    done

    # Install system packages if requested
    if [[ "$INSTALL_SYSTEM" == "true" ]]; then
        install_system_packages
        install_aws_cli
        install_terraform
        install_kubectl
        install_gh_cli
    fi

    # Run setup steps
    [[ "$SKIP_CHECKS" == "false" ]] && check_requirements
    [[ "$SKIP_PYTHON" == "false" ]] && setup_python
    [[ "$SKIP_NODE" == "false" ]] && setup_node
    install_terraform_tools
    [[ "$SKIP_TERRAFORM" == "false" ]] && init_terraform
    setup_precommit
    [[ "$SKIP_AWS" == "false" ]] && configure_aws

    # Final summary
    log_section "Setup Complete!"

    log_info "Next steps:"
    log_info "1. Add work/bin to your PATH for this session:"
    log_info "   ${GREEN}export PATH=\"$PROJECT_ROOT/work/bin:\$PATH\"${NC}"
    log_info ""
    log_info "2. To make it permanent, add to your shell configuration:"
    log_info "   ${GREEN}echo 'export PATH=\"$PROJECT_ROOT/work/bin:\$PATH\"' >> ~/.bashrc${NC}"
    log_info "   ${GREEN}source ~/.bashrc${NC}"
    log_info ""
    log_info "3. Run tests to verify setup:"
    log_info "   ${GREEN}cd apps/tf-visualizer && make test${NC}"
    log_info ""
    log_info "4. Deploy infrastructure:"
    log_info "   ${GREEN}cd terraform && make plan${NC}"
    log_info ""
    log_info "✅ All done! Happy coding! 🚀"
}

# Run main function
main "$@"
