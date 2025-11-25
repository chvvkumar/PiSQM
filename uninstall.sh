#!/bin/bash

# PiSQM Uninstallation Script
# This script removes the PiSQM service and cleans up the installation

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the absolute path of the current directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="pisqm.service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"

echo -e "${RED}PiSQM Uninstallation Script${NC}"
echo "Project directory: $PROJECT_DIR"
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run with sudo${NC}"
    echo "Usage: sudo ./uninstall.sh"
    exit 1
fi

# Confirmation prompt
read -p "Are you sure you want to uninstall PiSQM? This will remove the service and virtual environment. (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled"
    exit 0
fi

echo ""
echo -e "${YELLOW}Step 1: Stopping service...${NC}"
if systemctl is-active --quiet $SERVICE_NAME; then
    systemctl stop $SERVICE_NAME
    echo -e "${GREEN}Service stopped${NC}"
else
    echo "Service is not running"
fi

echo ""
echo -e "${YELLOW}Step 2: Disabling service...${NC}"
if systemctl is-enabled --quiet $SERVICE_NAME 2>/dev/null; then
    systemctl disable $SERVICE_NAME
    echo -e "${GREEN}Service disabled${NC}"
else
    echo "Service is not enabled"
fi

echo ""
echo -e "${YELLOW}Step 3: Removing service file...${NC}"
if [ -f "$SERVICE_FILE" ]; then
    rm "$SERVICE_FILE"
    echo -e "${GREEN}Service file removed${NC}"
else
    echo "Service file not found"
fi

echo ""
echo -e "${YELLOW}Step 4: Reloading systemd daemon...${NC}"
systemctl daemon-reload
systemctl reset-failed
echo -e "${GREEN}Systemd daemon reloaded${NC}"

echo ""
echo -e "${YELLOW}Step 5: Removing virtual environment...${NC}"
if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
    echo -e "${GREEN}Virtual environment removed${NC}"
else
    echo "Virtual environment not found"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Uninstallation completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "The PiSQM service has been removed from your system."
echo "The project files in $PROJECT_DIR remain intact."
echo "You can reinstall by running: sudo ./install.sh"
echo ""
