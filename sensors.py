import time
from datetime import datetime
from config import AVERAGING_PERIOD, READING_INTERVAL, INVALID_READING

# Try to import smbus2 for hardware sensors
try:
    from smbus2 import SMBus
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    print("smbus2 not available, using mock sensors")

class SHT30:
    """SHT30 Temperature and Humidity Sensor"""
    def __init__(self, bus=1, address=0x44):
        self.bus = SMBus(bus)
        self.address = address
        self._temperature = None
        self._humidity = None
        self._read_data()
    
    def _read_data(self):
        """Read temperature and humidity from SHT30"""
        try:
            # Send measurement command (high repeatability)
            self.bus.write_i2c_block_data(self.address, 0x2C, [0x06])
            time.sleep(0.5)
            
            # Read 6 bytes of data
            data = self.bus.read_i2c_block_data(self.address, 0x00, 6)
            
            # Convert to temperature and humidity
            temp_raw = data[0] * 256 + data[1]
            humidity_raw = data[3] * 256 + data[4]
            
            self._temperature = -45 + (175 * temp_raw / 65535.0)
            self._humidity = 100 * humidity_raw / 65535.0
        except Exception as e:
            print(f"SHT30 read error: {e}")
            self._temperature = INVALID_READING
            self._humidity = INVALID_READING
    
    @property
    def temperature(self):
        """Get temperature in Celsius"""
        self._read_data()
        return self._temperature
    
    @property
    def relative_humidity(self):
        """Get relative humidity in %"""
        self._read_data()
        return self._humidity

class BMP388:
    """BMP388 Pressure and Temperature Sensor"""
    def __init__(self, bus=1, address=0x77):
        self.bus = SMBus(bus)
        self.address = address
        self._temperature = None
        self._pressure = None
        self._read_calibration()
        self._configure()
    
    def _read_calibration(self):
        """Read calibration coefficients"""
        import struct
        try:
            # Read calibration data from registers 0x31-0x45
            cal_data = self.bus.read_i2c_block_data(self.address, 0x31, 21)
            
            # Parse calibration coefficients
            self.T1 = struct.unpack('<H', bytes(cal_data[0:2]))[0] / 0.00390625
            self.T2 = struct.unpack('<H', bytes(cal_data[2:4]))[0] / 1073741824.0
            self.T3 = struct.unpack('b', bytes([cal_data[4]]))[0] / 281474976710656.0
            
            self.P1 = (struct.unpack('<h', bytes(cal_data[5:7]))[0] - 16384) / 1048576.0
            self.P2 = (struct.unpack('<h', bytes(cal_data[7:9]))[0] - 16384) / 536870912.0
            self.P3 = struct.unpack('b', bytes([cal_data[9]]))[0] / 4294967296.0
            self.P4 = struct.unpack('b', bytes([cal_data[10]]))[0] / 137438953472.0
            self.P5 = struct.unpack('<H', bytes(cal_data[11:13]))[0] / 0.125
            self.P6 = struct.unpack('<H', bytes(cal_data[13:15]))[0] / 64.0
            self.P7 = struct.unpack('b', bytes([cal_data[15]]))[0] / 256.0
            self.P8 = struct.unpack('b', bytes([cal_data[16]]))[0] / 32768.0
            self.P9 = struct.unpack('<h', bytes(cal_data[17:19]))[0] / 281474976710656.0
            self.P10 = struct.unpack('b', bytes([cal_data[19]]))[0] / 281474976710656.0
            self.P11 = struct.unpack('b', bytes([cal_data[20]]))[0] / 36893488147419103232.0
        except Exception as e:
            print(f"BMP388 calibration read error: {e}")
            raise
    
    def _configure(self):
        """Configure sensor for normal operation"""
        try:
            # Set oversampling and power mode
            self.bus.write_byte_data(self.address, 0x1B, 0x33)  # Enable pressure and temp, normal mode
            self.bus.write_byte_data(self.address, 0x1C, 0x00)  # ODR and filter settings
            time.sleep(0.1)
        except Exception as e:
            print(f"BMP388 configuration error: {e}")
            raise
    
    def _read_data(self):
        """Read temperature and pressure"""
        try:
            # Read raw data from registers 0x04-0x09
            data = self.bus.read_i2c_block_data(self.address, 0x04, 6)
            
            # Combine bytes
            adc_p = data[0] | (data[1] << 8) | (data[2] << 16)
            adc_t = data[3] | (data[4] << 8) | (data[5] << 16)
            
            # Compensate temperature
            partial_data1 = adc_t - self.T1
            partial_data2 = partial_data1 * self.T2
            self._temperature = partial_data2 + (partial_data1 * partial_data1) * self.T3
            
            # Compensate pressure
            partial_data1 = self.P6 * self._temperature
            partial_data2 = self.P7 * (self._temperature * self._temperature)
            partial_data3 = self.P8 * (self._temperature * self._temperature * self._temperature)
            partial_out1 = self.P5 + partial_data1 + partial_data2 + partial_data3
            
            partial_data1 = self.P2 * self._temperature
            partial_data2 = self.P3 * (self._temperature * self._temperature)
            partial_data3 = self.P4 * (self._temperature * self._temperature * self._temperature)
            partial_out2 = adc_p * (self.P1 + partial_data1 + partial_data2 + partial_data3)
            
            partial_data1 = adc_p * adc_p
            partial_data2 = self.P9 + self.P10 * self._temperature
            partial_data3 = partial_data1 * partial_data2
            partial_data4 = partial_data3 + (adc_p * adc_p * adc_p) * self.P11
            
            self._pressure = partial_out1 + partial_out2 + partial_data4
            self._pressure = self._pressure / 100.0  # Convert to hPa
        except Exception as e:
            print(f"BMP388 read error: {e}")
            self._temperature = INVALID_READING
            self._pressure = INVALID_READING
    
    @property
    def temperature(self):
        """Get temperature in Celsius"""
        self._read_data()
        return self._temperature
    
    @property
    def pressure(self):
        """Get pressure in hPa"""
        self._read_data()
        return self._pressure

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
            # Initialize SHT30 (exterior temp, humidity)
            sensors['sht30'] = SHT30(bus=1, address=0x44)
            print("SHT30 sensor initialized")

            # Initialize BMP388 (enclosure temp, pressure)
            sensors['bmp388'] = BMP388(bus=1, address=0x77)
            print("BMP388 sensor initialized")

            return sensors
        
        except Exception as e:
            print(f"Hardware sensor initialization failed: {e}")
            import traceback
            traceback.print_exc()
            print("Falling back to mock sensors")
            return initialize_mock_sensors()
    else:
        print("Falling back to mock sensors")
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

        # Read SHT30
        try:
            exterior_temp = sensors['sht30'].temperature
            humidity = sensors['sht30'].relative_humidity
        except Exception as e:
            print(f"SHT30 read error: {e}")
            exterior_temp = INVALID_READING
            humidity = INVALID_READING
        
        # Read BMP388
        try:
            enclosure_temp = sensors['bmp388'].temperature
            pressure = sensors['bmp388'].pressure
        except Exception as e:
            print(f"BMP388 read error: {e}")
            enclosure_temp = INVALID_READING
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
    Reads all sensors in sensors for `period` seconds, taking readings at `interval` second intervals
    """
    n_readings = int(period // interval)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ext_temps = []
    encl_temps = []
    hums = []
    presses = []
    
    for i in range(n_readings):
        # Take reading
        readings = read_all_sensors(sensors)
        
        if readings is None:
            time.sleep(interval)
            continue

        ext_temps.append(readings['exterior_temp'])
        encl_temps.append(readings['enclosure_temp'])
        hums.append(readings['humidity'])
        presses.append(readings['pressure'])
        
        time.sleep(interval)
    
    # Filter out invalid readings
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
        data = read_sensors_over_interval(sensors)
        if data:
            print(f"Reading {i+1}: {data}")
        else:
            print(f"Reading {i+1}: FAILED")
        time.sleep(2)

if __name__ == "__main__":
    test_sensors()