#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/pigeon.service"

if [ ! -f "$SERVICE_FILE" ]; then
  echo "Error: pigeon.service not found in $SCRIPT_DIR"
  exit 1
fi

echo "Installing PIGEON UI service..."
echo "Make sure you've edited pigeon.service with your username and paths first!"
echo ""

sudo cp "$SERVICE_FILE" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pigeon
sudo systemctl start pigeon
sudo systemctl status pigeon
