#!/bin/bash
set -e

# StreamFix Installer
# One-command install for StreamFix JSON repair proxy

INSTALL_DIR="$HOME/.local/bin"
BINARY_NAME="streamfix"
GITHUB_REPO="rozetyp/streamfix"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() { echo -e "${BLUE}ℹ${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }

# Detect platform
case "$(uname -s)" in
    Darwin) PLATFORM="macos" ;;
    Linux) PLATFORM="linux" ;;
    *) error "Unsupported platform: $(uname -s)"; exit 1 ;;
esac

case "$(uname -m)" in
    x86_64|amd64) ARCH="amd64" ;;
    arm64|aarch64) ARCH="arm64" ;;
    *) error "Unsupported architecture: $(uname -m)"; exit 1 ;;
esac

BINARY_URL="https://github.com/${GITHUB_REPO}/releases/latest/download/streamfix-${PLATFORM}-${ARCH}"

info "Installing StreamFix for ${PLATFORM}-${ARCH}"

# Check if Python method is easier
if command -v pip >/dev/null 2>&1; then
    info "Python detected. You can also install with: ${GREEN}pip install streamfix${NC}"
fi

# Create install directory
mkdir -p "$INSTALL_DIR"

# Download binary
info "Downloading from GitHub releases..."
if command -v curl >/dev/null 2>&1; then
    curl -sSL "$BINARY_URL" -o "$INSTALL_DIR/$BINARY_NAME"
elif command -v wget >/dev/null 2>&1; then
    wget -q "$BINARY_URL" -O "$INSTALL_DIR/$BINARY_NAME"
else
    error "Neither curl nor wget found. Please install one or use: pip install streamfix"
    exit 1
fi

# Make executable
chmod +x "$INSTALL_DIR/$BINARY_NAME"

# Check if in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    warn "$INSTALL_DIR is not in your PATH"
    info "Add to your shell config: ${GREEN}export PATH=\"\$PATH:$INSTALL_DIR\"${NC}"
    info "Or run directly: ${GREEN}$INSTALL_DIR/$BINARY_NAME serve${NC}"
else
    success "StreamFix installed successfully!"
fi

info "Quick start:"
echo -e "  ${GREEN}streamfix serve${NC}                    # Start with OpenRouter (need API key)"
echo -e "  ${GREEN}streamfix serve --upstream http://localhost:1234/v1${NC}  # Use LM Studio"
echo -e "  ${GREEN}streamfix serve --help${NC}             # See all options"

success "Ready to use! 🚀"