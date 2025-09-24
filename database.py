import os
from datetime import datetime, timedelta

def update_datalog(sensor_data:dict):
    """
    function that takes in a dict of sensor data and writes it to a file named 'weather_data.csv' in the working directory.
    assumes keys are timestamp, exterioro_temp, enclosure_temp, humidity, pressure
    """ 
    try:
        # get directory name and file name
        wkdirectory = os.getcwd()
        data_path = os.path.join(wkdirectory, "weather_data.csv")

        keys = ['timestamp', 'exterior_temp', 'enclosure_temp', 'humidity', 'pressure']
        new_line = ",".join(str(sensor_data[key]) for key in keys)
        if os.path.isfile(data_path):
            # csv file already exists in this location. just append to end of file
            with open(data_path, 'a') as f:
                f.write(f"{new_line}\n")
            return "data appended to existing file"
        else:
            # csv file does not exist in this location, create one and add headers and data
            with open(data_path, 'w') as f:
                f.write(f"timestamp,exterior_temp,enclosure_temp,humidity,pressure\n")
                f.write(f"{new_line}\n")
            return "new file created with data"
    except KeyError as e:
        error_msg = f"Missing sensor data key: {str(e)}"
        log_error(error_msg)
        return f"Error: {error_msg}"
        
    except OSError as e:
        if "No space left" in str(e) or "Disk full" in str(e):
            free_result = free_disk_space()
            try:
                # get directory name and file name
                wkdirectory = os.getcwd()
                data_path = os.path.join(wkdirectory, "weather_data.csv")

                keys = ['timestamp', 'exterior_temp', 'enclosure_temp', 'humidity', 'pressure']
                new_line = ",".join(str(sensor_data[key]) for key in keys)
                with open(data_path, 'a') as f:
                    f.write(f"{new_line}\n")
                return "data written after freeing space: {free_result}"
            except OSError:
                return "Error: still no disk space after cleanup"
        else:
            return f"Error: write failed: {str(e)}"
    except Exception as e:
        return f"Error: unexpected error: {str(e)}"
        
def free_disk_space():
    """
    Remove old data to free disk space
    Removes 5 weather data lines for every 1 error log line
    """
    removed_count = 0
    for i in range(5):
        result = remove_oldest_line("weather_data.csv")
        if "successfully" in result:
            removed_count += 1
        elif "no data lines" in result:
            break
    error_result = remove_oldest_line("error_log.csv")

    log_error(f"Disk cleanup performed: removed {removed_count} records")
    return f"freed space: removed {removed_count} weather records"

def log_error(error_message:str):
    """
    writes error messages to a file in the same directory.
    if the write fails, doesn't take any action, fails silently
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # get directory name and file name
        wkdirectory = os.getcwd()
        error_path = os.path.join(wkdirectory, "error_log.csv")

        if os.path.isfile(error_path):
            # csv file already exists in this location. just append to end of file
            with open(error_path, 'a') as f:
                f.write(f"{timestamp},{error_message}\n")
            return "error message appended to existing file"
        else:
            # csv file does not exist in this location, create one and add headers and data
            with open(error_path, 'w') as f:
                f.write(f"timestamp,error_message\n")
                f.write(f"{timestamp},{error_message}\n")
            return "new file created with erro message"

    except OSError as e:
        return f"Failed to log error: {str(e)}"
    except Exception as e:
        return f"Failed to log error: {str(e)}"

def remove_oldest_line(file_path:str):
    if os.path.isfile(file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()
        if len(lines) > 1:
            del lines[1]

            with open(file_path, 'w') as f:
                f.writelines(lines)
            return "oldest line removed successfully"
        else:
            return "no data lines to remove"
    else:
        return "file does not exist"

def cleanup_old_data(days_to_keep: int = 3650):
    try:
        wkdirectory = os.getcwd()
        files = [os.path.join(wkdirectory, file) for file in ["weather_data.csv", "error_log.csv"]]
        current_timestamp = datetime.now()
        
        total_removed = 0
        
        for file in files:
            if not os.path.isfile(file):
                continue  # Skip if file doesn't exist
            
            try:
                with open(file, 'r') as f:
                    file_lines = f.readlines()
                
                if len(file_lines) <= 1:  # Only header or empty
                    continue
                
                lines_to_remove = 0
                for i in range(1, len(file_lines)):  # Skip header
                    line = file_lines[i]
                    try:
                        timestamp_str = line.split(",")[0]
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        time_difference = current_timestamp - timestamp
                        
                        if time_difference.days >= days_to_keep:  # Line is old
                            lines_to_remove += 1
                        else:  # Found first recent line
                            break
                            
                    except (ValueError, IndexError) as e:
                        # Malformed timestamp or line, skip this line
                        log_error(f"Malformed line in {file}: {line.strip()}")
                        continue
                
                # Remove the old lines
                for j in range(lines_to_remove):
                    result = remove_oldest_line(file)
                
                if lines_to_remove > 0:
                    total_removed += lines_to_remove
                    log_error(f"Cleanup: removed {lines_to_remove} old records from {os.path.basename(file)}")
                    
            except (PermissionError, OSError) as e:
                log_error(f"Cleanup failed for {file}: {str(e)}")
                continue
        
        return f"cleanup complete: removed {total_removed} total records"
        
    except Exception as e:
        error_msg = f"Cleanup function failed: {str(e)}"
        log_error(error_msg)
        return error_msg

def read_data_range(start_date=None, end_date=None, last_n_days=None):
    """
    Read weather data with optional filtering
    
    Args:
        start_date: datetime object or string "YYYY-MM-DD HH:MM:SS"
        end_date: datetime object or string "YYYY-MM-DD HH:MM:SS" 
        last_n_days: int, get last N days of data
        
    Returns:
        list of dictionaries with weather data, or error message string
    """
    try:
        wkdirectory = os.getcwd()
        data_path = os.path.join(wkdirectory, "weather_data.csv")
        
        if not os.path.isfile(data_path):
            return "No weather data file found"
        
        # Calculate date range if using last_n_days
        if last_n_days:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=last_n_days)
        
        # Convert string dates to datetime objects if needed
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        
        # Read and filter data
        filtered_data = []
        with open(data_path, 'r') as f:
            lines = f.readlines()
            
        # Skip header, process data lines
        for line in lines[1:]:
            try:
                parts = line.strip().split(',')
                timestamp_str = parts[0]
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                # Apply date filtering
                if start_date and timestamp < start_date:
                    continue
                if end_date and timestamp > end_date:
                    continue
                
                # Create data dictionary
                data_dict = {
                    'timestamp': timestamp_str,
                    'exterior_temp': parts[1],
                    'enclosure_temp': parts[2],
                    'humidity': parts[3],
                    'pressure': parts[4]
                }
                filtered_data.append(data_dict)
                
            except (ValueError, IndexError):
                # Skip malformed lines
                continue
        
        return filtered_data
        
    except Exception as e:
        return f"Error reading data: {str(e)}"

def read_error_logs(start_date=None, end_date=None, last_n_days=None):
    """
    Read error log data with optional filtering
    
    Args:
        start_date: datetime object or string "YYYY-MM-DD HH:MM:SS"
        end_date: datetime object or string "YYYY-MM-DD HH:MM:SS" 
        last_n_days: int, get last N days of errors
        
    Returns:
        list of dictionaries with error data, or error message string
    """
    try:
        wkdirectory = os.getcwd()
        error_path = os.path.join(wkdirectory, "error_log.csv")
        
        if not os.path.isfile(error_path):
            return "No error log file found"
        
        # Calculate date range if using last_n_days
        if last_n_days:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=last_n_days)
        
        # Convert string dates to datetime objects if needed
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        
        # Read and filter error data
        filtered_errors = []
        with open(error_path, 'r') as f:
            lines = f.readlines()
            
        # Skip header, process error lines
        for line in lines[1:]:
            try:
                # Split on first comma only (error messages might contain commas)
                timestamp_str, error_message = line.strip().split(',', 1)
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                # Apply date filtering
                if start_date and timestamp < start_date:
                    continue
                if end_date and timestamp > end_date:
                    continue
                
                # Create error dictionary
                error_dict = {
                    'timestamp': timestamp_str,
                    'error_message': error_message
                }
                filtered_errors.append(error_dict)
                
            except (ValueError, IndexError):
                # Skip malformed lines
                continue
        
        return filtered_errors
        
    except Exception as e:
        return f"Error reading error logs: {str(e)}"
    