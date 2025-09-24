import time
import signal
import sys
#import RPi.GPIO as GPIO
import gpiozero
from datetime import datetime, timedelta

from sensors import initialize_sensors, read_sensors_over_interval
from database import update_datalog, log_error
#from display import initialize_display, update_display
from web_server import should_upload, upload_to_server

from config import (
    DEVELOPMENT_MODE,
    SHUTDOWN_SIGNAL_PIN,
    MAIN_LOOP_INTERVAL,
    AVERAGING_PERIOD,
    READING_INTERVAL
)

def signal_early_shutdown():
    """Signal Witty Pi for early shutdown (production only)"""
    if not DEVELOPMENT_MODE:
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(SHUTDOWN_SIGNAL_PIN, GPIO.OUT)
            GPIO.output(SHUTDOWN_SIGNAL_PIN, GPIO.HIGH)  # Start high
            time.sleep(0.1)  # Brief delay
            GPIO.output(SHUTDOWN_SIGNAL_PIN, GPIO.LOW)   # Pull low to trigger shutdown
            print("Shutdown signal sent to Witty Pi")
            log_error("Early shutdown signal sent to Witty Pi")
        except Exception as e:
            print(f"Failed to signal shutdown: {e}")
            log_error(f"Failed to signal shutdown: {e}")
    else:
        print("Development mode - skipping shutdown signal")

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

def take_readings():
    """Core weather station functionality"""
    try:
        # Initialize sensors
        print("Initializing sensors...")
        sensors = initialize_sensors()
        
        if not sensors:
            error_msg = "Failed to initialize sensors"
            print(error_msg)
            log_error(error_msg)
            return None
        
        # Take averaged sensor readings
        print(f"Taking readings over {AVERAGING_PERIOD} seconds...")
        sensor_data = read_sensors_over_interval(
            sensors, 
            period=AVERAGING_PERIOD, 
            interval=READING_INTERVAL
        )
        
        if sensor_data:
            print(f"Readings complete: {sensor_data}")
            
            # Log data to CSV
            result = update_datalog(sensor_data)
            print(f"Data logged: {result}")
            
            # Check for upload
            if should_upload():
                print("Upload needed - connecting to network...")
                upload_result = upload_to_server()
                print(f"Upload result: {upload_result}")
            else:
                print("No upload needed")
                
        else:
            error_msg = "Failed to get sensor readings"
            print(error_msg)
            log_error(error_msg)
        
        return sensor_data
        
    except Exception as e:
        error_msg = f"Error in take_readings: {str(e)}"
        print(error_msg)
        log_error(error_msg)
        return None

def main():
    """Single execution for Witty Pi (production mode)"""
    print("=" * 50)
    print("Weather Station - Production Mode")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        # Take readings and log data
        sensor_data = take_readings()
        
        if sensor_data:
            print("Weather station cycle completed successfully")
        else:
            print("Weather station cycle completed with errors")
        
        # Signal early shutdown to Witty Pi
        print("Signaling completion to Witty Pi...")
        signal_early_shutdown()
        
        # Script will continue running until Witty Pi cuts power
        print("Waiting for Witty Pi shutdown...")
        
    except Exception as e:
        error_msg = f"Critical error in main: {str(e)}"
        print(error_msg)
        log_error(error_msg)
        signal_early_shutdown()  # Try to shutdown even on error

def main_loop():
    """Continuous loop for development testing"""
    print("=" * 50)
    print("Weather Station - Development Mode")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Reading interval: {MAIN_LOOP_INTERVAL/60} minutes")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    cycle_count = 0
    
    while True:
        try:
            cycle_count += 1
            print(f"\n--- Cycle {cycle_count} at {datetime.now().strftime('%H:%M:%S')} ---")
            
            # Take readings
            sensor_data = take_readings()
            
            if sensor_data:
                print(f"Cycle {cycle_count} completed successfully")
            else:
                print(f"Cycle {cycle_count} completed with errors")
            
            # Sleep until next reading
            print(f"Sleeping for {MAIN_LOOP_INTERVAL/60} minutes...")
            time.sleep(MAIN_LOOP_INTERVAL)
            
        except KeyboardInterrupt:
            print("\nShutdown requested by user")
            log_error("Development loop stopped by user")
            break
            
        except Exception as e:
            error_msg = f"Error in main loop cycle {cycle_count}: {str(e)}"
            print(error_msg)
            log_error(error_msg)
            print("Waiting 60 seconds before retry...")
            time.sleep(60)

def cleanup_gpio():
    """Clean up GPIO on exit"""
    try:
        GPIO.cleanup()
    except:
        pass


##### Old Version
'''
def main_old():
    sensors = initialize_sensors()
    sensor_data = read_sensors_over_interval(sensors)
    result = update_datalog(sensor_data)

    display = initialize_display
    update_display(display, sensor_data)

    if should_upload():
        upload_result = upload_to_server()

def main_loop_old():
    """Main weather station loop"""
    # initialize hardware
    try:
        sensors = initialize_sensors()
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
'''

if __name__ == "__main__":
    try:
        if DEVELOPMENT_MODE:
            main_loop()
        else:
            main()
    finally:
        cleanup_gpio()
        print("Weather station shutdown complete")