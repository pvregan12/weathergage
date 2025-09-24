import time
import signal
import sys
from datetime import datetime, timedelta
from config import MAIN_LOOP_INTERVAL, BUTTON_PIN, CLEANUP_INTERVAL_DAYS
from sensors import read_sensors_over_interval, initialize_sensors
from database import update_datalog, log_error, cleanup_old_data
from display import initialize_display, update_display
from web_server import should_upload, upload_to_server
import gpiozero

def main():
    sensors = initialize_sensors()
    sensor_data = read_sensors_over_interval(sensors)
    result = update_datalog(sensor_data)

    display = initialize_display
    update_display(display, sensor_data)

    if should_upload():
        upload_result = upload_to_server()

def main_loop():
    """Main weather station loop"""
    # initialize hardware
    try:
        sensors = initialize_sensors()
        #button = gpiozero.Button(BUTTON_PIN)
        last_cleanup = datetime.now()

        log_error("Weather station started")

        while True:
            try:
                # take sensor readings
                sensor_data = read_sensors_over_interval(sensors)

                if sensor_data:
                    # log to csv
                    result = update_datalog(sensor_data)
                    print(f"Data logged: {result}")

                else:
                    log_error("Failed to read sensors")

                # check for data upload (daily)
                if should_upload():
                    print("Starting data upload")
                    upload_result = upload_to_server()
                    print(f"Upload result: {upload_result}")


                display = initialize_display()
                update_display(display, sensor_data)
                # periodic cleanup (10 years)
                #if (datetime.now() - last_cleanup).total_seconds() > CLEANUP_INTERVAL_DAYS*24*3600:
                #    cleanup_result = cleanup_old_data()
                #    print(f"Cleanup: {cleanup_result}")
                #    last_cleanup = datetime.now()
                
                # check for button press (wifi activation)
                #if button.is_pressed:
                #    handle_wifi_button()
                
                # sleep until next reading
                print(f"Sleeping for {MAIN_LOOP_INTERVAL/60} minutes...")
                time.sleep(MAIN_LOOP_INTERVAL)

            except KeyboardInterrupt:
                print("Shutting down weather station...")
                break
            except Exception as e:
                error_msg = f"Main loop error: {str(e)}"
                log_error(error_msg)
                print(error_msg)
                time.sleep(60) # wait before retrying
    except Exception as e:
        print(f"Failed to initialize: {str(e)}")
        sys.exit(1)

def should_cleanup():
    """Check if it's time for data cleanup (every 10 years)"""
    try:
        last_cleanup = get_last_cleanup_time()
        time_since_cleanup = datetime.now() - last_cleanup
        
        # Check if 10 years have passed (10 * 365 * 24 * 3600 seconds)
        return time_since_cleanup.total_seconds() >= (10 * 365 * 24 * 3600)
        
    except Exception as e:
        log_error(f"Error checking cleanup schedule: {str(e)}")
        return False

def get_last_cleanup_time():
    """Read last cleanup timestamp from file"""
    try:
        with open('last_cleanup.txt', 'r') as f:
            timestamp_str = f.read().strip()
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except (FileNotFoundError, ValueError):
        # no previous cleanup, start from now
        return datetime.now()
    
def save_last_cleanup_time(timestamp):
    """Save cleanup timestamp to file"""
    try:
        with open('last_cleanup.txt', 'w') as f:
            f.write(timestamp.strftime("%Y-%m-%d %H:%M:%S"))
    except Exception as e:
        log_error(f"Failed to save last cleanup time")

def handle_wifi_button():
    """Handle WiFi hotspot button press"""
    # TODO: implement WiFi hotspot activation
    print("button pressed - to be implemented later")
    pass

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    print("Received shutdown signal")
    log_error("Weather station shutdown")
    sys.exit(0)

#### 
# In your main loop - modified for TPL5110
""""
def main_loop_with_tpl5110():
    # 1. Take sensor reading immediately on wake-up
    sensor_data = read_all_sensors()
    update_datalog(sensor_data)
    
    # 2. Check if upload/cleanup needed (based on timestamps, not counters)
    if should_upload():
        upload_to_server()
    
    #if should_cleanup():  # Check timestamp file
    #    cleanup_result = cleanup_old_data()
    #    save_last_cleanup_time(datetime.now())
    #    log_error(f"Scheduled cleanup completed: {cleanup_result}")
    
    # 3. Signal TPL5110 that we're done
    signal_tpl5110_done()
    
    # 4. Pi shuts down, TPL5110 waits 15 minutes, then powers Pi back on

def signal_tpl5110_done():
    #Send DONE signal to TPL5110
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DONE_PIN, GPIO.OUT)
    GPIO.output(DONE_PIN, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(DONE_PIN, GPIO.LOW)
"""
if __name__ == "__main__":
    main()