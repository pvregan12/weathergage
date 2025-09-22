import time
from datetime import datetime, timedelta
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

            # initialize SHT30 (interior temp, pressure)
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
            exterior_temp = round(sensors['sht30'].temperature, 3)
            humidity = round(sensors['sht30'].relative_humidity, 1)
        except Exception as e:
            print(f"SHT30 read error: {e}")
            exterior_temp = None
            humidity = None
        
        # read bmp388
        try:
            interior_temp = round(sensors['bmp388'].temperature, 3)
            pressure = round(sensors['bmp388'].pressure, 3)
        except Exception as e:
            print(f"BMP388 read error: {e}")
            interior_temp = None
            pressure = None
        
        # Replace None values with -9999
        if exterior_temp is None:
            exterior_temp = -9999.0
        if interior_temp is None:
            interior_temp = -9999.0
        if humidity is None:
            humidity = -9999.0
        if pressure is None:
            pressure = -9999.0
        
        sensor_data = {
            'timestamp': timestamp,
            'exterior_temp': exterior_temp,
            'interior_temp': interior_temp,
            'humidity': humidity,
            'pressure': pressure
        }
        return sensor_data
    except Exception as e:
        print(f"Sensor reading failed: {e}")
        return None
    

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
