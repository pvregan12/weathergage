# display.py
from PIL import Image, ImageDraw, ImageFont
import adafruit_epd.ssd1675 as ssd1675
import board
import digitalio
import busio

def initialize_display():
    """Initialize 2.13" monochrome e-ink display"""
    try:
        # SPI setup
        spi = board.SPI()
        ecs = digitalio.DigitalInOut(board.D8)   # Chip select
        dc = digitalio.DigitalInOut(board.D22)   # Data/command
        rst = digitalio.DigitalInOut(board.D27)  # Reset
        busy = digitalio.DigitalInOut(board.D17) # Busy
        
        # Initialize display
        display = ssd1675.SSD1675(
            spi, cs=ecs, dc=dc, sram_cs=None, rst=rst, busy=busy
        )
        
        print("E-ink display initialized")
        return display
        
    except Exception as e:
        print(f"Display initialization failed: {e}")
        return None

def update_display(display, sensor_data):
    """Update display with weather data"""
    if display is None:
        return
    
    try:
        # Create blank image
        image = Image.new("RGB", (display.width, display.height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Weather station title
        draw.text((5, 5), "Weather Station", fill=0)
        draw.text((5, 25), f"Ext: {sensor_data['exterior_temp']}°C", fill=0)
        draw.text((5, 45), f"Enc: {sensor_data['enclosure_temp']}°C", fill=0) 
        draw.text((5, 65), f"Hum: {sensor_data['humidity']}%", fill=0)
        draw.text((5, 85), f"Press: {sensor_data['pressure']} hPa", fill=0)
        draw.text((5, 105), f"{sensor_data['timestamp'][:16]}", fill=0)
        
        # Update the display (power consumption happens here)
        display.image(image)
        display.display()
        
        print("Display updated")
        
    except Exception as e:
        print(f"Display update failed: {e}")