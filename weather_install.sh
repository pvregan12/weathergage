#!/bin/bash
# install.sh - Weather Station Setup Script for Raspberry Pi

set -e  # Exit on any error

echo "=========================================="
echo "Weather Station Installation Script"
echo "=========================================="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

#### Update system packages
echo "Updating system packages..."
sudo apt update
sudo apt upgrade -y

#-------------- Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y python3-pip python3-dev python3-venv git i2c-tools build-essential

#-------------- Enable I2C for sensors
echo "Enabling I2C interface..."
sudo raspi-config nonint do_i2c 0

#-------------- Enable SPI (in case needed for future displays)
echo "Enabling SPI interface..."
sudo raspi-config nonint do_spi 0

#-------------- Setting up power management
echo "Configuring aggressive power management..."

# Disable Bluetooth permanently
echo "Disabling Bluetooth..."
sudo systemctl disable bluetooth
sudo systemctl disable hciuart

# Configure boot config for power savings
echo "Updating /boot/config.txt for power optimization..."

# Backup original config
sudo cp /boot/config.txt /boot/config.txt.backup

# Add power management settings to config.txt
cat << 'EOF' | sudo tee -a /boot/config.txt

# Weather Station Power Optimizations
# Disable audio (saves ~3mA)
dtparam=audio=off

# Disable Bluetooth hardware
dtoverlay=disable-bt

# Disable camera and display auto-detect (saves ~6mA)
camera_auto_detect=0
display_auto_detect=0

# Use legacy GL driver for HDMI disable capability
# Comment out the modern KMS driver
#dtoverlay=vc4-kms-v3d
max_framebuffers=2
EOF

# Add HDMI disable to rc.local for automatic power-off at boot
echo "Configuring automatic HDMI disable..."
sudo sed -i '/^exit 0/i # Disable HDMI for power savings\n/usr/bin/tvservice -o' /etc/rc.local

# Create deployment script for WiFi disable (don't run automatically)
cat > "$INSTALL_DIR/enable_deployment_mode.sh" << 'EOF'
#!/bin/bash
# Run this script when ready for final deployment
echo "Enabling deployment mode (disables WiFi on boot)..."

# Add WiFi disable to config.txt
if ! grep -q "dtoverlay=disable-wifi" /boot/config.txt; then
    echo "dtoverlay=disable-wifi" | sudo tee -a /boot/config.txt
fi

# Disable WiFi service
sudo systemctl disable wpa_supplicant

echo "Deployment mode enabled. WiFi will be disabled on next reboot."
echo "Weather station will use Python code to control WiFi for uploads only."
echo "Reboot to activate all power savings."
EOF

chmod +x "$INSTALL_DIR/enable_deployment_mode.sh"

echo "Power optimizations configured:"
echo "  - Bluetooth disabled (saves ~10-20mA)"
echo "  - Audio disabled (saves ~3mA)" 
echo "  - Camera/display auto-detect disabled (saves ~6mA)"
echo "  - Legacy GL driver enabled for HDMI control"
echo "  - HDMI will be disabled at boot (saves ~17mA)"
echo ""
echo "Total estimated power savings: ~36-46mA"
echo "Run enable_deployment_mode.sh when ready to disable WiFi for deployment"

#-------------- Create weather station directory
INSTALL_DIR="/home/pregan/weather_station"
echo "Setting up installation directory: $INSTALL_DIR"

#### Git repository setup
echo "Setting up weather station code repository..."

# Remove existing directory if it exists
#if [ -d "$INSTALL_DIR" ]; then
#    echo "Removing existing weather station directory..."
#    rm -rf "$INSTALL_DIR"
#fi

# Clone the repository
#echo "Cloning weather station repository..."
#git clone https://github.com/pvregan12/weathergage "$INSTALL_DIR"

#if [ $? -ne 0 ]; then
#    echo "Error: Failed to clone repository"
#    echo "Please check the repository URL and your internet connection"
#    exit 1
#fi

# Change to the repository directory
#cd "$INSTALL_DIR"

# Configure git for the pi user
#echo "Configuring git..."
#git config user.name "Weather Station Pi"
#git config user.email "weather@pi.local"

#echo "Repository cloned successfully to $INSTALL_DIR"

#if [ ! -d "$INSTALL_DIR" ]; then
#    mkdir -p "$INSTALL_DIR"
#fi

#-------------- Copy weather station files to installation directory
#echo "Copying weather station files..."
#cp *.py "$INSTALL_DIR/" 2>/dev/null || echo "No Python files found in current directory"
#cp requirements.txt "$INSTALL_DIR/" 2>/dev/null || echo "requirements.txt not found"

#-------------- Create virtual environment
echo "Creating Python virtual environment..."
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate

#-------------- Install Python packages
if [ -f "requirements.txt" ]; then
    echo "Installing Python packages from requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "Installing basic Python packages..."
    pip install --upgrade pip
    pip install requests adafruit-circuitpython-sht31d adafruit-circuitpython-bmp3xx
fi

#-------------- Set up Witty Pi integration
WITTY_DIR="/home/pregan/wittypi"
echo "Setting up Witty Pi integration..."

if [ -d "$WITTY_DIR" ]; then
    echo "Witty Pi directory found - setting up afterStartup.sh integration"
    
    # Create afterStartup.sh script
    cat > "$WITTY_DIR/afterStartup.sh" << 'EOF'
#!/bin/bash
# Weather Station startup script for Witty Pi
cd /home/pregan/weather_station
source venv/bin/activate
python3 main.py

# Weather station work complete - shutdown system
echo "Weather station work completed at $(date)"
echo "Initiating safe system shutdown..."
sudo shutdown -h now
EOF
    
    chmod +x "$WITTY_DIR/afterStartup.sh"
    echo "afterStartup.sh created and configured"
    
else
    echo "Warning: Witty Pi directory not found at $WITTY_DIR"
    echo "Please install Witty Pi software first, then manually copy afterStartup.sh"
fi

#-------------- Create data files
# skipping because database.py creates these with correct headers
#echo "Setting up data files..."
#touch weather_data.csv
#touch error_log.csv
#touch last_upload.txt

#-------------- Set proper permissions
echo "Setting file permissions..."
chown -R pi:pi "$INSTALL_DIR"
chmod +x main.py

#-------------- Create config file if it doesn't exist
if [ ! -f "config.py" ]; then
    echo "Creating default config.py..."
    cat > config.py << 'EOF'
# config.py - Weather Station Configuration

# Development vs Production mode
DEVELOPMENT_MODE = False  # Set to True for testing with continuous loop

# Sensor Reading Settings
AVERAGING_PERIOD = 30        # seconds to average readings over
READING_INTERVAL = 1         # seconds between individual readings
MAIN_LOOP_INTERVAL = 900     # 15 minutes between sensor cycles (dev mode only)

# GPIO Pin Assignments  
SHUTDOWN_SIGNAL_PIN = 21     # GPIO 21 (physical pin 40) for Witty Pi VIN monitoring

# File Paths
WEATHER_DATA_FILE = "weather_data.csv"
ERROR_LOG_FILE = "error_log.csv"
LAST_UPLOAD_FILE = "last_upload.txt"

# Upload Settings (configure these for your setup)
COPYPARTY_SERVER = "192.168.1.100"    # Your server IP
COPYPARTY_PORT = 8000
COPYPARTY_USERNAME = "weathergage"
COPYPARTY_PASSWORD = "your_password"   # Change this
UPLOAD_INTERVAL_HOURS = 24

# Data Management
INVALID_READING = -9999                # Sentinel value for bad readings
EOF
fi

#-------------- Test I2C bus
echo "Testing I2C bus..."
if command -v i2cdetect &> /dev/null; then
    echo "I2C devices detected:"
    i2cdetect -y 1 2>/dev/null || echo "No I2C devices found (this is normal if sensors aren't connected yet)"
fi

#-------------- Deactivate virtual environment
deactivate 2>/dev/null || true

echo ""
echo "=========================================="
echo "Weather Station installation complete!"
echo "=========================================="
echo ""
echo "Installation directory: $INSTALL_DIR"
echo ""
echo "Next steps:"
echo "1. Install Witty Pi 4 Mini software (if not already done)"
echo "2. Configure your settings in $INSTALL_DIR/config.py"
echo "3. Connect your sensors (SHT30 and BMP388 to I2C bus)"
echo "4. Test with: cd $INSTALL_DIR && source venv/bin/activate && python3 main.py"
echo ""
if [ ! -d "$WITTY_DIR" ]; then
    echo "5. After installing Witty Pi software, copy afterStartup.sh:"
    echo "   sudo cp $INSTALL_DIR/afterStartup.sh $WITTY_DIR/"
    echo ""
fi
echo "For development/testing, set DEVELOPMENT_MODE = True in config.py"
echo "For production deployment, set DEVELOPMENT_MODE = False in config.py"
echo ""
echo "Installation log complete. Reboot recommended to ensure all interfaces are enabled."