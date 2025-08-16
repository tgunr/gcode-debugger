#!/usr/bin/env python3
"""
Test script to discover available API endpoints
"""

import requests
import json

def test_endpoints():
    """Test various API endpoints to find the correct one"""
    host = 'bbctrl.local'
    port = 80
    base_url = f'http://{host}:{port}'
    
    headers = {
        'User-Agent': 'GCodeDebugger/1.0',
        'Accept': 'application/json, text/plain, */*'
    }
    
    # Test common endpoints
    endpoints = [
        '/api/state',
        '/api/status', 
        '/api/gcode',
        '/api/command',
        '/api/mdi',
        '/gcode',
        '/command',
        '/mdi'
    ]
    
    print("Testing API endpoints...")
    
    for endpoint in endpoints:
        url = f'{base_url}{endpoint}'
        try:
            # Try GET first
            response = requests.get(url, headers=headers, timeout=5)
            print(f"GET {endpoint}: {response.status_code}")
            if response.status_code == 200:
                print(f"  Content-Type: {response.headers.get('Content-Type', 'unknown')}")
                if len(response.text) < 200:
                    print(f"  Response: {response.text[:200]}")
                else:
                    print(f"  Response: {response.text[:200]}...")
            elif response.status_code != 404:
                print(f"  Error: {response.text[:100]}")
                
        except Exception as e:
            print(f"GET {endpoint}: Error - {e}")
    
    # Test with a simple G-code command as query parameter
    test_command = "G90"
    print(f"\nTesting with G-code command: {test_command}")
    
    for endpoint in ['/api/gcode', '/gcode', '/api/command', '/command']:
        url = f'{base_url}{endpoint}?{test_command}'
        try:
            response = requests.get(url, headers=headers, timeout=5)
            print(f"GET {endpoint}?{test_command}: {response.status_code}")
            if response.status_code == 200:
                print(f"  Response: {response.text[:100]}")
            elif response.status_code != 404:
                print(f"  Error: {response.text[:100]}")
        except Exception as e:
            print(f"GET {endpoint}?{test_command}: Error - {e}")

if __name__ == "__main__":
    test_endpoints()