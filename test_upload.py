"""
Test script for the upload endpoint
"""
import requests

API_URL = "http://localhost:8000"

def test_upload():
    """Test uploading a log file to the API"""
    
    # Test with auth.log
    print("Testing upload with auth.log...")
    with open("test_logs/auth.log", "rb") as f:
        files = {"file": ("auth.log", f, "text/plain")}
        response = requests.post(f"{API_URL}/upload-file", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Success: {result['message']}")
            print(f"  Logs ingested: {result['logs_ingested']}")
            print(f"  Total logs: {result['total_logs']}")
        else:
            print(f"✗ Failed: {response.status_code}")
            print(f"  Error: {response.json()}")
    
    print()
    
    # Test with database.log
    print("Testing upload with database.log...")
    with open("test_logs/database.log", "rb") as f:
        files = {"file": ("database.log", f, "text/plain")}
        response = requests.post(f"{API_URL}/upload-file", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Success: {result['message']}")
            print(f"  Logs ingested: {result['logs_ingested']}")
            print(f"  Total logs: {result['total_logs']}")
        else:
            print(f"✗ Failed: {response.status_code}")
            print(f"  Error: {response.json()}")
    
    print()
    
    # Test source filtering
    print("Testing source filtering...")
    response = requests.get(f"{API_URL}/summary", params={"source": "auth.log"})
    if response.status_code == 200:
        summary = response.json()
        print(f"✓ Auth logs: {summary['total']}")
        print(f"  By level: {summary['by_level']}")
    
    response = requests.get(f"{API_URL}/summary", params={"source": "database.log"})
    if response.status_code == 200:
        summary = response.json()
        print(f"✓ Database logs: {summary['total']}")
        print(f"  By level: {summary['by_level']}")

if __name__ == "__main__":
    try:
        test_upload()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the backend is running:")
        print("   uvicorn src.api:app --reload")
