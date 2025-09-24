import os
import subprocess
import time
import requests
import json
from datetime import datetime, timedelta
from config import *
#from flask import Flask, jsonify, request, make_response
from database import log_error, read_data_range, read_error_logs

# upload config
#COPYPARTY_SERVER = "192.168.1.100" # replace with copyparty ip
#COPYPARTY_PORT = 3923 # replace with copyparty port
#UPLOAD_INTERVAL_HOURS = 24 # daily

def get_last_upload_time():
    """Read last upload timestamp from file"""
    try:
        with open(LAST_UPLOAD_FILE, 'r') as f:
            timestamp_str = f.read().strip()
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except (FileNotFoundError, ValueError):
        # no prev uploads, start from 7 days ago
        return datetime.now() - timedelta(days=7)

def save_last_upload_time(timestamp):
    """Save successfull upload timestamp"""
    with open(LAST_UPLOAD_FILE, 'w') as f:
        f.write(timestamp.strftime("%Y-%m-%d %H:%M:%S"))

def prepare_upload_data():
    """Gather all data since last upload"""
    last_upload = get_last_upload_time()
    current_time = datetime.now()

    weather_data = read_data_range(start_date=last_upload, end_date=current_time)

    error_data = read_error_logs(start_date=last_upload, end_date=current_time)

    # build current status
    status_data = {
        "upload_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "last_reading": get_last_reading(),
        "last_error": get_last_error(),
        "system_uptime": get_system_uptime(),
        "data_points_uploaded": len(weather_data) if isinstance(weather_data, list) else 0,
        "errors_uploaded": len(error_data) if isinstance(error_data, list) else 0
    }
    return {
        "weather_data": weather_data,
        "error_logs": error_data,
        "status": status_data
    }

def upload_to_server():
    """Upload all weather station data as one bundled file"""
    try:
        upload_data = prepare_upload_data()  # Use your existing function
        current_time = datetime.now()
        
        filename = f"weather_bundle_{current_time.strftime('%Y%m%d_%H%M%S')}.json"
        url = f"http://{COPYPARTY_SERVER}:{COPYPARTY_PORT}/weather//{filename}"
        
        response = requests.put(
            url,
            data=json.dumps(upload_data, indent=2),
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            save_last_upload_time(current_time)
            return f"Bundle upload successful: {len(upload_data.get('weather_data', []))} weather records"
        else:
            return f"Bundle upload failed: HTTP {response.status_code}"
            
    except Exception as e:
        error_msg = f"Bundle upload failed: {str(e)}"
        log_error(error_msg)
        return error_msg

def should_upload():
    """Check if it's time for next upload"""
    last_upload = get_last_upload_time()
    time_since_upload = datetime.now() - last_upload
    return time_since_upload.total_seconds() >= (UPLOAD_INTERVAL_HOURS * 3600)

def should_update():
    """Check if a flag file exists on copyparty, and if so, git pull."""
    url = f"http://{COPYPARTY_SERVER}:{COPYPARTY_PORT}/{UPDATE_FLAG}"
    
    try:
        response = requests.head(url, timeout=5)
        
        if response.status_code == 200:
            print("Update flag found. Initiating git pull...")
            
            # The script is in the repo, so we can run git pull directly.
            result = subprocess.run(
                ["git", "pull"],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            log_error(f"Git pull completed: {result.stdout.strip()}")
            print("Git pull successful.")
            print(f"Output:\n{result.stdout}")
            return f"Output:\n{result.stdout}" #True
        else:
            print("No update flag found. No action needed.")
            return "No update flag found. No action needed." # False
            
    except subprocess.CalledProcessError as e:
        print(f"Error during git pull: {e}")
        print(f"Error output:\n{e.stderr}")
        return f"Error output:\n{e.stderr}" # False
    except requests.exceptions.RequestException as e:
        print(f"Error checking for update flag: {e}") 
        return f"Error checking for update flag: {e}" # False
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}") 
        return f"An unexpected error occurred: {str(e)}" # False

# utils
def get_system_uptime():
    """get system uptime in human readable format"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])

        # convert to days, hours, minutes
        up_days = int(uptime_seconds // 86400)
        up_hours = int((uptime_seconds % 86400) // 3600)
        up_minutes = int((uptime_seconds % 3600) // 60)

        return f"{up_days} days, {up_hours} hours, {up_minutes}minutes"
    except Exception as e:
        return "Uptime unkown: {str(e)}"

def get_last_reading():
    """get the most recent weather reading"""
    try:
        data = read_data_range(last_n_days=1)
        if isinstance(data, list) and len(data) > 0:
            return data[-1]
        return None
    except:
        return None 

def get_last_error(window=7):
    """get the most recent error"""
    try:
        errors = read_error_logs(last_n_days=window)
        if isinstance(errors, list) and len(errors) > 0:
            last_error = errors[-1]
            return f"{last_error['timestep']}: {last_error['error_message']}"
        return "No errors in last {window} days"
    except Exception as e:
        return f"Error reading error log: {str(e)}"


###  fragments for local hotspot download
# hotspot config
"""
HOTSPOT_SSID = "WeatherStation_102"
HOTSPOT_PASSWORD = "testweather102"
HOTSPOT_IP = "192.168.4.1"
def start_wifi_hotspot():
    " start local wifi
    try:
        # configure hostapd and dnsmasq (placehold until have pi zero)
        # subprocess.run(['sudo', 'systemctl', 'start', 'hostapd'], check=True)
        # subprocess.run(['sudo', 'systemctl', 'start', 'dnsmasq'], check=True)

        # 
        return True
    except subprocess.CalledProcessError:
        return False
    pass

def stop_wifi_hotspot():
    try:
        # subprocess.run(['sudo', 'systemctl', 'stop', 'hostapd'], check=True)
        # subprocess.run(['sudo', 'systemctl', 'stop', 'dnsmasq'], check=True)
        return True
    except subprocess.CalledProcessError:
        return False
"""
