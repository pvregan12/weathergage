# config.py - Weather Station Configuration

# Dev Mode
DEVELOPMENT_MODE = True

# Sensor Reading Settings
AVERAGING_PERIOD = 30        # seconds to average readings over X
READING_INTERVAL = 1         # seconds between individual readings X
MAIN_LOOP_INTERVAL = 15*60     # 15 minutes between sensor cycles (15 * 60) = 900 s

# GPIO Pin Assignments  
SHUTDOWN_SIGNAL_PIN = 29              # 

'''
DISPLAY_CS_PIN = 8           # E-ink display chip select
DISPLAY_DC_PIN = 22          # E-ink display data/command
DISPLAY_RST_PIN = 27         # E-ink display reset
DISPLAY_BUSY_PIN = 17        # E-ink display busy
'''
# File Paths
WEATHER_DATA_FILE = "weather_data.csv"
ERROR_LOG_FILE = "error_log.csv"
LAST_UPLOAD_FILE = "last_upload.txt"
LAST_CLEANUP_FILE = "last_cleanup.txt"

# Upload Settings
COPYPARTY_SERVER = "192.168.12.209"    # Your server IP
COPYPARTY_PORT = 3923
COPYPARTY_USERNAME = "weathergage"
COPYPARTY_PASSWORD = "climate_change"   # You'll set this
UPLOAD_INTERVAL_HOURS = 24

# WiFi Hotspot Settings (if you implement it later)
HOTSPOT_SSID = "WeatherStation_001"
HOTSPOT_PASSWORD = "weather12345"
HOTSPOT_IP = "192.168.4.1"

# Data Management
CLEANUP_INTERVAL_DAYS = 3650           # 10 years in days
INVALID_READING = -9999                # Sentinel value for bad readings

# Physical Constants (when you add pressure correction later)
ELEVATION_METERS = 34                 # Your elevation above sea level