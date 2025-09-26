#!/bin/bash
cd /home/pregan/weather_station
/usr/bin/python3 main.py

# Weather station work complete - shutdown system
echo "Weather station work completed at $(date)"
echo "Initiating safe system shutdown..."
sudo shutdown -h now