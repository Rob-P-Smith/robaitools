#!/bin/bash
#
# Install WSDD for Windows 10/11 Network Discovery
# This makes your Linux Samba server appear in Windows "Network" section
# LAN-ONLY: Uses multicast discovery on local network only
#

echo "Installing WSDD (Web Services Dynamic Discovery)..."
echo "This enables automatic discovery in Windows 10/11 Network browsing"
echo "LAN-ONLY: Multicast announcements stay within local network"
echo ""

# Update package list
echo "Updating package list..."
sudo apt-get update

# Install WSDD
echo "Installing wsdd..."
sudo apt-get install -y wsdd

# Enable and start the service
echo "Enabling wsdd service..."
sudo systemctl enable wsdd
sudo systemctl start wsdd

# Check status
echo ""
echo "Checking wsdd status..."
sudo systemctl status wsdd --no-pager

echo ""
echo "✓ WSDD installation complete!"
echo ""
echo "Your server (ROBUNTU) should now appear in:"
echo "  - Windows File Explorer → Network"
echo "  - \\\\192.168.10.50\\Sharedrive (direct access still works)"
echo ""
echo "Security: WSDD uses LAN-only multicast (UDP 3702)"
echo "No internet exposure - same security as existing Samba setup"
echo ""
echo "Note: It may take a few minutes for Windows to discover the server."
echo "If it doesn't appear immediately, restart Windows or wait 5-10 minutes."
