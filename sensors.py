import time
from datetime import datetime
from config import AVERAGING_PERIOD, READING_INTERVAL, INVALID_READING
try:
    import adafruit_bmp3xx as bmp3xx
    import adafruit_sht31d as sht31d
    import adafruit_blinka as ab
    import board
    import busio
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    print("Hardware libraries not available, using mock sensors")

class MockSensor:
    """Mock sensor for testing without hardware"""
    def __init__(self, sensor_type):
        import random
        self.sensor_type = sensor_type
        self.base_temp = 22.0
        self.base_humidity = 60.0
        self.base_pressure = 1013.25
        
    
    @property
    def temperature(self):
        # Simulate slight temperature variation
        import random
        return self.base_temp + random.uniform(-2, 2)
    
    @property
    def relative_humidity(self):
        import random
        return self.base_humidity + random.uniform(-5, 5)
    
    @property
    def pressure(self):
        import random
        return self.base_pressure + random.uniform(-10, 10)

def safe_average(values):
    """Calculate average excluding INVALID_READING values, return INVALID_READING if no valid data"""
    valid_values = [val for val in values if val != INVALID_READING]
    return sum(valid_values) / len(valid_values) if valid_values else INVALID_READING

def initialize_sensors():
    """Initialize SHT30 and BMP388 sensors"""
    sensors = {}
    if HARDWARE_AVAILABLE:
        try:
            # initialize i2c bus
            i2c = busio.I2C(board.SCL, board.SDA)

            # initialize SHT30 (exterior temp, humidity)
            sensors['sht30'] = sht31d.SHT31D(i2c)
            print("SHT30 sensor initialized")

            # initialize SHT30 (enclosure temp, pressure)
            sensors['bmp388'] = bmp3xx.BMP3XX_I2C(i2c)
            print("bmp388 sensor initialized")

            return sensors
        
        except Exception as e:
            print(f"Hardware sensor intialization failed: {e}")
            print("Falling back to mock sensors")
            return initialize_mock_sensors()
    else:
        print("Failling back to mock sensors")
        return initialize_mock_sensors()
        
def initialize_mock_sensors():
    """Initialize mock sensors for testing"""
    sensors = {
        'sht30': MockSensor('sht30'),
        'bmp388': MockSensor('bmp388')
    }
    print("Mock sensors initialized")
    return sensors

def read_all_sensors(sensors):
    """Read data from all sensors and return as dictionary"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # read SHT30
        try:
            exterior_temp = sensors['sht30'].temperature
            humidity = sensors['sht30'].relative_humidity
        except Exception as e:
            print(f"SHT30 read error: {e}")
            exterior_temp = None
            humidity = None
        
        # read bmp388
        try:
            enclosure_temp = sensors['bmp388'].temperature
            pressure = sensors['bmp388'].pressure
        except Exception as e:
            print(f"BMP388 read error: {e}")
            enclosure_temp = None
            pressure = None
        
        # Replace None values with INVALID_READING
        if exterior_temp is None:
            exterior_temp = INVALID_READING
        if enclosure_temp is None:
            enclosure_temp = INVALID_READING
        if humidity is None:
            humidity = INVALID_READING
        if pressure is None:
            pressure = INVALID_READING
        
        sensor_data = {
            'timestamp': timestamp,
            'exterior_temp': exterior_temp,
            'enclosure_temp': enclosure_temp,
            'humidity': humidity,
            'pressure': pressure
        }
        return sensor_data
    except Exception as e:
        print(f"Sensor reading failed: {e}")
        return None
    
def read_sensors_over_interval(sensors, period=AVERAGING_PERIOD, interval=READING_INTERVAL):
    """
    Reads all sensors in sensors for `period` seconds, taking readings a `interval` second intervals
    """
    n_readings = int(period // interval)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ext_temps = []
    encl_temps = []
    hums = []
    presses = []
    for i in range(n_readings):

        # take reading
        readings = read_all_sensors(sensors)
        
        if readings is None:
            time.sleep(interval)
            continue

        ext_temps.append(readings['exterior_temp'])
        encl_temps.append(readings['enclosure_temp'])
        hums.append(readings['humidity'])
        presses.append(readings['pressure'])
        
        time.sleep(interval)
    
    ext_temps = [val for val in ext_temps if val != INVALID_READING]
    encl_temps = [val for val in encl_temps if val != INVALID_READING]
    hums = [val for val in hums if val != INVALID_READING]
    presses = [val for val in presses if val != INVALID_READING]
    
    avg_data = {
    'timestamp': timestamp,
    'exterior_temp': safe_average(ext_temps),
    'enclosure_temp': safe_average(encl_temps),
    'humidity': safe_average(hums),
    'pressure': safe_average(presses)
    }

    return avg_data  

def test_sensors():
    """Test function to verify sensor readings"""
    print("Testing sensor initialization...")
    sensors = initialize_sensors()
    
    print("\nTaking test readings...")
    for i in range(3):
        data = read_all_sensors(sensors)
        if data:
            print(f"Reading {i+1}: {data}")
        else:
            print(f"Reading {i+1}: FAILED")
        time.sleep(2)

if __name__ == "__main__":
    test_sensors()
