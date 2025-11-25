#!/bin/bash

# PiSQM Installation Script
# This script sets up the PiSQM service with a virtual environment and systemd service

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

echo -e "${GREEN}PiSQM Installation Script${NC}"
echo "Project directory: $PROJECT_DIR"
echo ""

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}Error: This script must be run on Linux${NC}"
    exit 1
fi

# Check if systemd is available
if ! command -v systemctl &> /dev/null; then
    echo -e "${RED}Error: systemd is not available on this system${NC}"
    exit 1
fi

# Check if running with sudo for systemd service installation
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run with sudo${NC}"
    echo "Usage: sudo ./install.sh"
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Creating virtual environment...${NC}"
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists at $VENV_DIR"
    read -p "Do you want to recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_DIR"
        python3 -m venv "$VENV_DIR"
        echo -e "${GREEN}Virtual environment recreated${NC}"
    else
        echo "Using existing virtual environment"
    fi
else
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}Virtual environment created${NC}"
fi

echo ""
echo -e "${YELLOW}Step 2: Installing requirements...${NC}"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
echo -e "${GREEN}Requirements installed${NC}"

echo ""
echo -e "${YELLOW}Step 3: Creating systemd service file...${NC}"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=PiSQM - Sky Quality Meter
After=network.target time-sync.target
Wants=network-online.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_DIR/bin/python $PROJECT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environment
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}Service file created at $SERVICE_FILE${NC}"

echo ""
echo -e "${YELLOW}Step 4: Reloading systemd daemon...${NC}"
systemctl daemon-reload
echo -e "${GREEN}Systemd daemon reloaded${NC}"

echo ""
echo -e "${YELLOW}Step 5: Enabling service to start on boot...${NC}"
systemctl enable $SERVICE_NAME
echo -e "${GREEN}Service enabled${NC}"

echo ""
echo -e "${YELLOW}Step 6: Starting service...${NC}"
systemctl start $SERVICE_NAME
echo -e "${GREEN}Service started${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Installation completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Service status:"
systemctl status $SERVICE_NAME --no-pager -l
echo ""
echo "Useful commands:"
echo "  Check status:  sudo systemctl status $SERVICE_NAME"
echo "  Stop service:  sudo systemctl stop $SERVICE_NAME"
echo "  Start service: sudo systemctl start $SERVICE_NAME"
echo "  View logs:     sudo journalctl -u $SERVICE_NAME -f"
echo "  Uninstall:     sudo ./uninstall.sh"
echo ""
