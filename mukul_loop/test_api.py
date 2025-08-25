#!/usr/bin/env python3
"""
Test script for the Store Monitoring API
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_api():
    print("Testing Store Monitoring API...")
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✓ Server is running: {response.json()}")
    except Exception as e:
        print(f"✗ Server connection failed: {e}")
        return
    
    # Test 2: Get store summary for a sample store
    try:
        response = requests.get(f"{BASE_URL}/store_summary/123")
        if response.status_code == 200:
            summary = response.json()
            print(f"✓ Store summary retrieved: {summary}")
        else:
            print(f"✗ Store summary failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Store summary error: {e}")
    
    # Test 3: Trigger a report
    try:
        response = requests.post(f"{BASE_URL}/trigger_report")
        if response.status_code == 200:
            result = response.json()
            report_id = result["report_id"]
            print(f"✓ Report triggered: {report_id}")
            
            # Test 4: Poll for completion
            print("Polling for report completion...")
            max_attempts = 10
            attempts = 0
            
            while attempts < max_attempts:
                status_response = requests.get(f"{BASE_URL}/get_report/{report_id}")
                
                if status_response.headers.get("content-type") == "text/csv":
                    print("✓ Report completed! CSV file received.")
                    # Save the CSV
                    with open(f"test_report_{report_id[:8]}.csv", "wb") as f:
                        f.write(status_response.content)
                    print(f"✓ CSV saved as test_report_{report_id[:8]}.csv")
                    break
                elif status_response.json()["status"] == "Running":
                    print(f"  Still running... (attempt {attempts + 1}/{max_attempts})")
                    time.sleep(5)
                else:
                    print(f"✗ Report failed: {status_response.json()}")
                    break
                
                attempts += 1
            
            if attempts >= max_attempts:
                print("✗ Report generation timed out")
                
        else:
            print(f"✗ Report trigger failed: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Report trigger error: {e}")
    
    # Test 5: List all reports
    try:
        response = requests.get(f"{BASE_URL}/reports")
        if response.status_code == 200:
            reports = response.json()
            print(f"✓ Reports list: {reports}")
        else:
            print(f"✗ Reports list failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Reports list error: {e}")

if __name__ == "__main__":
    test_api()
