#!/bin/bash
cd /home/pregan/weather_station
/usr/bin/python3 main.py

: '
INTERVAL=900
cd /home/pregan/weather_station
while true; do
  # Reset the timer at the beginning of each loop
  SECONDS=0

  echo "Starting work at $(date)..."
  # Run Python script
  /usr/bin/python3 main.py

  # $SECONDS now holds the elapsed time of the script execution
  ELAPSED_TIME=$SECONDS
  echo "Python script finished in ${ELAPSED_TIME} seconds."

  # Calculate how long to sleep
  SLEEP_TIME=$((INTERVAL - ELAPSED_TIME))

  # If the script took longer than 15 minutes, do not sleep
  if [ "${SLEEP_TIME}" -gt 0 ]; then
    echo "Sleeping for ${SLEEP_TIME} seconds..."
    sleep "${SLEEP_TIME}"
  else
    echo "Script took longer than 15 minutes. Starting next loop immediately."
  fi
done
: '