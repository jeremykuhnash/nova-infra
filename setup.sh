#!/bin/bash
# Nova Infrastructure Setup Script
# Sets up development environment, AWS CLI, Terraform, and GitHub integration

set -e

echo "🚀 Nova Infrastructure Setup"
echo "============================"
echo ""

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install core dev tools and Python
echo "🐍 Installing Python and development tools..."
sudo apt install -y \
  build-essential \
  python3 \
  python3-pip \
  python3-venv \
  python3-dev \
  python3-setuptools \
  python3-wheel \
  python-is-python3 \
  git \
  curl \
  wget \
  unzip \
  jq \
  pkg-config \
  software-properties-common \
  libssl-dev \
  libffi-dev \
  libbz2-dev \
  libreadline-dev \
  libsqlite3-dev \
  zlib1g-dev \
  libncursesw5-dev \
  libgdbm-dev \
  liblzma-dev \
  lsb-release \
  ca-certificates

# Set python and pip aliases if not default
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1
sudo update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Install AWS CLI v2
echo "☁️  Installing AWS CLI v2..."
if ! command -v aws &> /dev/null; then
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip -q awscliv2.zip
    sudo ./aws/install
    rm -rf awscliv2.zip aws/
else
    echo "   AWS CLI already installed: $(aws --version)"
fi

# Install Terraform
echo "🏗️  Installing Terraform..."
if ! command -v terraform &> /dev/null; then
    wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
    sudo apt update && sudo apt install -y terraform
else
    echo "   Terraform already installed: $(terraform version | head -1)"
fi

# Install GitHub CLI
echo "🐙 Installing GitHub CLI..."
if ! command -v gh &> /dev/null; then
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt update && sudo apt install -y gh
else
    echo "   GitHub CLI already installed: $(gh --version | head -1)"
fi

# Install kubectl (optional, for EKS management)
echo "☸️  Installing kubectl..."
if ! command -v kubectl &> /dev/null; then
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
    rm kubectl
else
    echo "   kubectl already installed: $(kubectl version --client --short 2>/dev/null || echo 'installed')"
fi

echo ""
echo "✅ Base tools installed successfully!"
echo ""

# Configure AWS (if not already configured)
if [ ! -f ~/.aws/credentials ]; then
    echo "⚠️  AWS credentials not found. Please configure AWS:"
    echo "   Run: aws configure"
    echo ""
else
    echo "✅ AWS credentials found"
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
    if [ -n "$ACCOUNT_ID" ]; then
        echo "   Account: $ACCOUNT_ID"
        echo "   User: $(aws sts get-caller-identity --query Arn --output text)"
    fi
    echo ""
fi

# Setup Terraform backend
echo "🏗️  Setting up Terraform backend..."
if [ -f terraform/init-backend.sh ]; then
    echo "   Run './terraform/init-backend.sh' to initialize Terraform backend"
else
    echo "   Terraform init script not found"
fi
echo ""

# Setup GitHub secrets (if in a git repo with GitHub remote)
if git remote -v 2>/dev/null | grep -q github.com; then
    echo "🔐 GitHub repository detected"
    if [ -f scripts/setup-github-secrets.sh ] && [ -f ~/.aws/credentials ]; then
        echo "   To configure GitHub Actions secrets, run:"
        echo "   ./scripts/setup-github-secrets.sh"
    else
        echo "   Configure AWS credentials first, then run setup-github-secrets.sh"
    fi
else
    echo "ℹ️  No GitHub repository detected. Skipping GitHub setup."
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Configure AWS credentials (if not done): aws configure"
echo "  2. Initialize Terraform backend: cd terraform && ./init-backend.sh"
echo "  3. Setup GitHub secrets: ./scripts/setup-github-secrets.sh"
echo "  4. Deploy infrastructure: cd terraform && terraform apply"
echo ""
echo "For more information, see README.md"
