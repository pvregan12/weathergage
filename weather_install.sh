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

# Update system packages
echo "Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y python3-pip python3-dev python3-venv git i2c-tools build-essential

# Enable I2C for sensors
echo "Enabling I2C interface..."
sudo raspi-config nonint do_i2c 0

# Enable SPI (in case needed for future displays)
echo "Enabling SPI interface..."
sudo raspi-config nonint do_spi 0

# Create weather station directory
INSTALL_DIR="/home/pi/weather_station"
echo "Setting up installation directory: $INSTALL_DIR"

if [ ! -d "$INSTALL_DIR" ]; then
    mkdir -p "$INSTALL_DIR"
fi

# Copy weather station files to installation directory
echo "Copying weather station files..."
cp *.py "$INSTALL_DIR/" 2>/dev/null || echo "No Python files found in current directory"
cp requirements.txt "$INSTALL_DIR/" 2>/dev/null || echo "requirements.txt not found"

# Create virtual environment
echo "Creating Python virtual environment..."
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate

# Install Python packages
if [ -f "requirements.txt" ]; then
    echo "Installing Python packages from requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "Installing basic Python packages..."
    pip install --upgrade pip
    pip install requests adafruit-circuitpython-sht31d adafruit-circuitpython-bmp3xx
fi

# Set up Witty Pi integration
WITTY_DIR="/home/pi/wittypi"
echo "Setting up Witty Pi integration..."

if [ -d "$WITTY_DIR" ]; then
    echo "Witty Pi directory found - setting up afterStartup.sh integration"
    
    # Create afterStartup.sh script
    cat > "$WITTY_DIR/afterStartup.sh" << 'EOF'
#!/bin/bash
# Weather Station startup script for Witty Pi
cd /home/pi/weather_station
source venv/bin/activate
python3 main.py
EOF
    
    chmod +x "$WITTY_DIR/afterStartup.sh"
    echo "afterStartup.sh created and configured"
    
else
    echo "Warning: Witty Pi directory not found at $WITTY_DIR"
    echo "Please install Witty Pi software first, then manually copy afterStartup.sh"
    
    # Create afterStartup.sh in weather station directory for manual copying
    cat > "$INSTALL_DIR/afterStartup.sh" << 'EOF'
#!/bin/bash
# Weather Station startup script for Witty Pi
# Copy this file to /home/pi/wittypi/afterStartup.sh after installing Witty Pi software
cd /home/pi/weather_station
source venv/bin/activate
python3 main.py
EOF
    
    chmod +x "$INSTALL_DIR/afterStartup.sh"
    echo "afterStartup.sh created in $INSTALL_DIR for manual installation"
fi

# Create data files
echo "Setting up data files..."
touch weather_data.csv
touch error_log.csv
touch last_upload.txt

# Set proper permissions
echo "Setting file permissions..."
chown -R pi:pi "$INSTALL_DIR"
chmod +x main.py

# Create config file if it doesn't exist
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

# Test I2C bus
echo "Testing I2C bus..."
if command -v i2cdetect &> /dev/null; then
    echo "I2C devices detected:"
    i2cdetect -y 1 2>/dev/null || echo "No I2C devices found (this is normal if sensors aren't connected yet)"
fi

# Deactivate virtual environment
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