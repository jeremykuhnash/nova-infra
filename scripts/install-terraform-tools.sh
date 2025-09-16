#!/bin/bash
# Install Terraform linting and security tools for nova-infra project
# These are statically-linked Go binaries with no runtime dependencies

set -euo pipefail

# Determine project root and default install directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration - default to project-local work/bin/
INSTALL_DIR="${INSTALL_DIR:-$PROJECT_ROOT/work/bin}"
TFLINT_VERSION="${TFLINT_VERSION:-latest}"
TFSEC_VERSION="${TFSEC_VERSION:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if we need sudo (only for system directories)
if [[ "$INSTALL_DIR" == "/usr/local/bin" || "$INSTALL_DIR" == "/usr/bin" ]]; then
   if [[ "$EUID" -ne 0 ]]; then
      log_warn "Installing to system directory. Will attempt to use sudo."
      SUDO="sudo"
   else
      SUDO=""
   fi
else
   # Installing to user-writable directory (like work/bin/)
   SUDO=""
fi

# Create install directory if it doesn't exist
if [[ ! -d "$INSTALL_DIR" ]]; then
    log_info "Creating install directory: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
fi

# Detect OS and architecture
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "$ARCH" in
    x86_64|amd64)
        ARCH="amd64"
        ;;
    aarch64|arm64)
        ARCH="arm64"
        ;;
    *)
        log_error "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

log_info "Detected platform: $OS/$ARCH"
log_info "Installing to: $INSTALL_DIR"

# Function to download and install a tool
install_tool() {
    local tool_name="$1"
    local download_url="$2"
    local temp_file="/tmp/${tool_name}_download"

    log_info "Installing $tool_name..."

    # Download the tool
    if ! curl -sL -o "$temp_file" "$download_url"; then
        log_error "Failed to download $tool_name"
        return 1
    fi

    # Handle zip files (tflint) vs direct binaries (tfsec)
    if [[ "$download_url" == *.zip ]]; then
        temp_dir="/tmp/${tool_name}_extract"
        mkdir -p "$temp_dir"
        unzip -q "$temp_file" -d "$temp_dir"
        chmod +x "$temp_dir/$tool_name"
        $SUDO mv "$temp_dir/$tool_name" "$INSTALL_DIR/"
        rm -rf "$temp_dir"
    else
        chmod +x "$temp_file"
        $SUDO mv "$temp_file" "$INSTALL_DIR/$tool_name"
    fi

    rm -f "$temp_file"

    # Verify installation
    if command -v "$tool_name" &> /dev/null; then
        local version=$($tool_name --version 2>&1 | head -n1)
        log_info "✅ $tool_name installed successfully: $version"
        return 0
    else
        log_error "Failed to install $tool_name"
        return 1
    fi
}

# Install tflint
if [[ "$TFLINT_VERSION" == "latest" ]]; then
    # Get latest version from GitHub API
    TFLINT_VERSION=$(curl -s https://api.github.com/repos/terraform-linters/tflint/releases/latest | grep tag_name | cut -d '"' -f 4 | sed 's/v//')
fi

TFLINT_URL="https://github.com/terraform-linters/tflint/releases/download/v${TFLINT_VERSION}/tflint_${OS}_${ARCH}.zip"
install_tool "tflint" "$TFLINT_URL"

# Install tfsec
if [[ "$TFSEC_VERSION" == "latest" ]]; then
    TFSEC_VERSION=$(curl -s https://api.github.com/repos/aquasecurity/tfsec/releases/latest | grep tag_name | cut -d '"' -f 4 | sed 's/v//')
fi

TFSEC_URL="https://github.com/aquasecurity/tfsec/releases/download/v${TFSEC_VERSION}/tfsec-${OS}-${ARCH}"
install_tool "tfsec" "$TFSEC_URL"

# Check if tools are in PATH
log_info ""
log_info "Installation Summary:"
log_info "==================="

if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    log_warn "$INSTALL_DIR is not in your PATH"
    log_info "Add it to your shell configuration:"
    log_info "  export PATH=\"$INSTALL_DIR:\$PATH\""
fi

# Show installed versions
if command -v tflint &> /dev/null; then
    log_info "tflint: $(tflint --version 2>&1 | head -n1)"
else
    log_error "tflint not found in PATH"
fi

if command -v tfsec &> /dev/null; then
    log_info "tfsec: $(tfsec --version 2>&1 | head -n1)"
else
    log_error "tfsec not found in PATH"
fi

log_info ""
log_info "✅ Terraform tools installation complete!"

# Provide PATH update command if needed
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    log_info ""
    log_info "📝 To use these tools, add this to your current shell session:"
    log_info "  ${GREEN}export PATH=\"$INSTALL_DIR:\$PATH\"${NC}"
    log_info ""
    log_info "To make it permanent, add the line to your shell configuration:"
    log_info "  echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.bashrc"
    log_info "  source ~/.bashrc"
else
    log_info "✅ $INSTALL_DIR is already in your PATH"
fi

log_info ""
log_info "You can now run 'make lint' or 'make security' from the terraform/ directory."
