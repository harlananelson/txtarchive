#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== TxtArchive Developer Setup ===${NC}"
echo "This script will help you set up your development environment."
echo ""

# 1. Check for Nix (Preferred Path)
if command -v nix &> /dev/null; then
    echo -e "${GREEN}[✔] Nix is installed.${NC}"
    echo -e "We recommend using the Nix environment for perfect reproducibility."
    echo ""
    read -p "Do you want to enter the Nix dev shell now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Entering Nix shell... (This may take a moment to download dependencies)${NC}"
        # Execute nix develop replacing the current process
        exec nix develop
    fi
else
    echo -e "${YELLOW}[!] Nix is NOT installed.${NC}"
    echo "Nix handles Python, Pandoc, and system tools automatically."
    echo ""
    read -p "Would you like to install Nix via Determinate Systems? (Recommended) (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Running Nix Installer...${NC}"
        curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
        echo -e "${GREEN}Nix installed! Please restart your terminal and run 'nix develop'.${NC}"
        exit 0
    fi
fi

# 2. Fallback: Standard Setup (The "Hard" Way)
echo ""
echo -e "${YELLOW}=== Proceeding with Standard Local Setup ===${NC}"

# Check for Pandoc (Critical)
if ! command -v pandoc &> /dev/null; then
    echo -e "${RED}[✘] CRITICAL ERROR: Pandoc is missing!${NC}"
    echo "You must install pandoc manually for txtarchive to work."
    echo "  macOS: brew install pandoc"
    echo "  Linux: sudo apt-get install pandoc"
    exit 1
else
    echo -e "${GREEN}[✔] Pandoc found: $(pandoc --version | head -n 1)${NC}"
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[✘] Python 3 is missing.${NC}"
    exit 1
fi

# Check for uv (Package Manager)
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}[!] 'uv' not found. Installing via pip...${NC}"
    pip install uv
else
    echo -e "${GREEN}[✔] uv found.${NC}"
fi

# Setup Venv
echo -e "${GREEN}Setting up virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    uv venv .venv --seed
fi

# Install Dependencies
echo -e "${GREEN}Installing dependencies in editable mode...${NC}"
source .venv/bin/activate
uv pip install -e ".[dev]"

echo ""
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "To start working, run:"
echo -e "  ${YELLOW}source .venv/bin/activate${NC}"
echo -e "  ${YELLOW}python -m txtarchive --help${NC}"