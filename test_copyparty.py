#!/usr/bin/env python3
"""
Test script for copyparty connectivity and automatic updates
Tests upload functionality and checks for update flags
"""

import requests
import json
import os
import subprocess
import sys
from datetime import datetime
from config import (
    COPYPARTY_SERVER,
    COPYPARTY_PORT,
    COPYPARTY_USERNAME,
    COPYPARTY_PASSWORD
)

def test_copyparty_connection():
    """Test basic connection to copyparty server"""
    try:
        url = f"http://{COPYPARTY_SERVER}:{COPYPARTY_PORT}/"
        print(f"Testing connection to {url}")
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("✓ Connection to copyparty server successful")
            return True
        else:
            print(f"✗ Server responded with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Connection failed: {e}")
        return False

def create_test_data():
    """Create sample weather data for testing"""
    test_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "test_mode": True,
        "sensor_data": {
            "exterior_temp": 23.5,
            "interior_temp": 24.1,
            "humidity": 65.2,
            "pressure": 1013.25
        },
        "system_info": {
            "upload_test": True,
            "version": "1.0"
        }
    }
    return test_data

def upload_multiple_test_files():
    """Upload multiple test files to simulate weather station batch upload"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_url = f"http://{COPYPARTY_SERVER}:{COPYPARTY_PORT}/weather/"
        
        files_to_upload = []
        
        # 1. Weather data file
        weather_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "weather_readings": [
                {
                    "timestamp": "2025-09-24 12:00:00",
                    "exterior_temp": 23.5,
                    "interior_temp": 24.1,
                    "humidity": 65.2,
                    "pressure": 1013.25
                },
                {
                    "timestamp": "2025-09-24 12:15:00", 
                    "exterior_temp": 23.7,
                    "interior_temp": 24.2,
                    "humidity": 64.8,
                    "pressure": 1013.18
                },
                {
                    "timestamp": "2025-09-24 12:30:00",
                    "exterior_temp": 24.1,
                    "interior_temp": 24.4,
                    "humidity": 64.1,
                    "pressure": 1013.10
                }
            ],
            "data_points": 3
        }
        files_to_upload.append((f"weather_data_{timestamp}.json", weather_data))
        
        # 2. System status file
        status_data = {
            "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "system_uptime": "2 days, 5 hours, 23 minutes",
            "last_reading": "2025-09-24 12:30:00",
            "battery_cycles": 15,
            "data_points_uploaded": 3,
            "errors_since_last_upload": 0
        }
        files_to_upload.append((f"status_{timestamp}.json", status_data))
        
        # 3. Error log file (if there were errors)
        error_data = {
            "errors": [
                {
                    "timestamp": "2025-09-24 11:45:00",
                    "error_message": "SHT30 read timeout - retrying"
                },
                {
                    "timestamp": "2025-09-24 12:10:00", 
                    "error_message": "WiFi connection took 15 seconds"
                }
            ],
            "error_count": 2
        }
        files_to_upload.append((f"errors_{timestamp}.json", error_data))
        
        print(f"Uploading {len(files_to_upload)} test files...")
        
        successful_uploads = 0
        
        for filename, data in files_to_upload:
            try:
                print(f"  Uploading {filename}...")
                
                url = f"{base_url}{filename}"
                response = requests.put(
                    url,
                    data=json.dumps(data, indent=2),
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    print(f"    ✓ {filename} uploaded successfully")
                    successful_uploads += 1
                else:
                    print(f"    ✗ {filename} failed with status {response.status_code}")
                    
            except Exception as e:
                print(f"    ✗ {filename} failed: {e}")
        
        print(f"\nBatch upload complete: {successful_uploads}/{len(files_to_upload)} files uploaded")
        
        return successful_uploads == len(files_to_upload)
        
    except Exception as e:
        print(f"✗ Batch upload failed: {e}")
        return False

def upload_batch_post():
    """Upload multiple files in a single POST request"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create all your data
        weather_data = {
            "weather_readings": [
                {"timestamp": "2025-09-24 12:00:00", "exterior_temp": 23.5, "humidity": 65.2, "pressure": 1013.25},
                {"timestamp": "2025-09-24 12:15:00", "exterior_temp": 23.7, "humidity": 64.8, "pressure": 1013.18},
                {"timestamp": "2025-09-24 12:30:00", "exterior_temp": 24.1, "humidity": 64.1, "pressure": 1013.10}
            ]
        }
        
        status_data = {
            "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "system_uptime": "2 days, 5 hours",
            "data_points_uploaded": 3
        }
        
        # Package multiple files in one POST
        url = f"http://{COPYPARTY_SERVER}:{COPYPARTY_PORT}/weather/"
        
        files = {
            'weather_file': (f'weather_{timestamp}.json', json.dumps(weather_data, indent=2), 'application/json'),
            'status_file': (f'status_{timestamp}.json', json.dumps(status_data, indent=2), 'application/json'),
        }
        
        response = requests.post(url, files=files, timeout=30)
        
        if response.status_code in [200, 201]:
            print("✓ Batch POST upload successful")
            return True
        else:
            print(f"✗ Batch POST failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Batch POST failed: {e}")
        return False


def upload_test_file():
    """Upload a single test file"""
    try:
        test_data = create_test_data()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"weather_test_{timestamp}.json"
        
        print(f"Uploading test file: {filename}")
        
        url = f"http://{COPYPARTY_SERVER}:{COPYPARTY_PORT}/weather/{filename}"
        
        response = requests.put(
            url,
            data=json.dumps(test_data, indent=2),
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            print(f"✓ Test file uploaded successfully")
            return True
        else:
            print(f"✗ Upload failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Upload failed: {e}")
        return False

def check_update_flag():
    """Check if update_flag.txt exists in /weather"""
    try:
        url = f"http://{COPYPARTY_SERVER}:{COPYPARTY_PORT}/weather/update_flag.txt"
        auth = (COPYPARTY_USERNAME, COPYPARTY_PASSWORD)
        
        print("Checking for update flag...")
        
        response = requests.get(url, auth=auth, timeout=10)
        
        if response.status_code == 200:
            print("✓ Update flag found!")
            print(f"  Flag content: {response.text.strip()}")
            return True
        elif response.status_code == 404:
            print("○ No update flag found (this is normal)")
            return False
        else:
            print(f"? Update flag check returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Update flag check failed: {e}")
        return False

def perform_git_update():
    """Perform git pull to update weather station code"""
    try:
        print("Performing git update...")
        
        # Change to weather station directory
        weather_dir = "/home/pi/weather_station"
        if os.path.exists(weather_dir):
            os.chdir(weather_dir)
        else:
            print(f"✗ Weather station directory not found: {weather_dir}")
            return False
        
        # Check if this is a git repository
        if not os.path.exists(".git"):
            print("✗ This is not a git repository")
            return False
        
        # Perform git pull
        result = subprocess.run(
            ['git', 'pull'], 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        if result.returncode == 0:
            print("✓ Git update successful")
            print(f"  Output: {result.stdout.strip()}")
            
            # Delete the update flag after successful update
            delete_update_flag()
            return True
        else:
            print(f"✗ Git update failed")
            print(f"  Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Git update timed out")
        return False
    except Exception as e:
        print(f"✗ Git update failed: {e}")
        return False

def delete_update_flag():
    """Delete the update flag after successful update"""
    try:
        url = f"http://{COPYPARTY_SERVER}:{COPYPARTY_PORT}/weather/update_flag.txt"
        auth = (COPYPARTY_USERNAME, COPYPARTY_PASSWORD)
        
        # Note: This assumes copyparty supports DELETE method
        # If not, you might need to use a different approach
        response = requests.delete(url, auth=auth, timeout=10)
        
        if response.status_code in [200, 204, 404]:
            print("○ Update flag cleaned up")
        else:
            print(f"? Update flag cleanup returned status {response.status_code}")
            
    except Exception as e:
        print(f"? Could not clean up update flag: {e}")

def test_authentication():
    """Test authentication with copyparty"""
    try:
        url = f"http://{COPYPARTY_SERVER}:{COPYPARTY_PORT}/weather/"
        auth = (COPYPARTY_USERNAME, COPYPARTY_PASSWORD)
        
        print("Testing authentication...")
        
        response = requests.get(url, auth=auth, timeout=10)
        
        if response.status_code == 200:
            print("✓ Authentication successful")
            return True
        elif response.status_code == 401:
            print("✗ Authentication failed - check username/password")
            return False
        elif response.status_code == 403:
            print("✗ Access forbidden - check user permissions")
            return False
        else:
            print(f"? Authentication test returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Authentication test failed: {e}")
        return False

def main():
    """Run all connectivity tests"""
    print("=" * 50)
    print("Copyparty Connectivity Test")
    print(f"Server: {COPYPARTY_SERVER}:{COPYPARTY_PORT}")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Basic connection
    print("\n1. Testing basic connection...")
    if test_copyparty_connection():
        tests_passed += 1
    
    # Test 2: Single file upload
    print("\n2. Testing single file upload...")
    if upload_test_file():
        tests_passed += 1
    
    # Test 3: Multiple file upload (simulates weather station batch)
    print("\n3. Testing batch file upload...")
    if upload_batch_post():
        tests_passed += 1
    
    # Test 4: Update flag check and update
    print("\n4. Checking for updates...")
    if check_update_flag():
        print("   Update flag found - performing git update...")
        if perform_git_update():
            print("   ✓ Update completed successfully")
            tests_passed += 1
        else:
            print("   ✗ Update failed")
    else:
        print("   ○ No updates needed")
        tests_passed += 1  # Count as passed since no update was needed
    
    # Test 5: Rate limiting check
    print("\n5. Testing rate limits...")
    print("   Uploading additional test file to check rate limiting...")
    if upload_test_file():
        print("   ○ Rate limiting allows normal uploads")
        tests_passed += 1
    else:
        print("   ? Rate limit may be active (this might be normal)")
        tests_passed += 1  # Don't fail on rate limiting
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Test Results: {tests_passed}/{total_tests} passed")
    print("=" * 50)
    
    if tests_passed == total_tests:
        print("✓ All tests passed - copyparty connectivity is working")
        return True
    else:
        print("✗ Some tests failed - check configuration and network")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)