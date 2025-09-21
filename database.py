
import pandas as pd
import os

def update_datalog(sensor_data:dict):
    """
    function that takes in a dict of sensor data and writes it to a file named 'weather_data.csv' in the working directory.
    assumes timestamp name
    """
    try:
        # get directory name and file name
        wkdirectory = os.getcwd()
        data_path = os.path.join(wkdirectory, "weather_data.csv")

        keys = ['timestamp', 'exterior_temp', 'interior_temp', 'humidity', 'pressure']
        new_line = ",".join(str(sensor_data[key]) for key in keys)
        if os.path.isfile(data_path):
            # csv file already exists in this location. just append to end of file
            with open(data_path, 'a') as f:
                f.write(f"{new_line}\n")
            return "data appended to existing file"
        else:
            # csv file does not exist in this location, create one and add headers and data
            with open(data_path, 'w') as f:
                f.write(f"timestamp,exterior_temp,interior_temp,humidity,pressure\n")
                f.write(f"{new_line}\n")
            return "new file created with data"
    except KeyError as e:
        return f"Error: missing required sensor data key: {str(e)}"
    except OSError as e:
        if "No space left" in str(e) or "Disk full" in str(e):
            free_result = free_disk_space()
            try:
                # get directory name and file name
                wkdirectory = os.getcwd()
                data_path = os.path.join(wkdirectory, "weather_data.csv")

                keys = ['timestamp', 'exterior_temp', 'interior_temp', 'humidity', 'pressure']
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

    return f"freed space: removed {removed_count} weather records"

def log_error(error_message:str):
    pass

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
        


    
