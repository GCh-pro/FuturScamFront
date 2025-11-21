"""
Quick test script for FuturScam API
Usage: python test_api.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test API health"""
    print("\n[TEST] Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_skillboy_health():
    """Test skill extractor health"""
    print("\n[TEST] Skillboy Health")
    response = requests.get(f"{BASE_URL}/skillboy/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_skill_extraction():
    """Test skill extraction"""
    print("\n[TEST] Skill Extraction")
    text = "We need a Senior Python developer with Django, FastAPI, PostgreSQL, Docker, Kubernetes, and AWS experience. REST API knowledge required."
    payload = {"text": text}
    
    response = requests.post(f"{BASE_URL}/skillboy", json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Extracted {result['count']} skills:")
    for skill in result['skills']:
        print(f"  - {skill}")

def test_create_rfp():
    """Test RFP creation"""
    print("\n[TEST] Create RFP")
    payload = {
        "role": "Senior Data Engineer",
        "company_name": "TechCorp",
        "company_city": "Paris",
        "job_description": "Looking for a data engineer with Python, Spark, and AWS knowledge",
        "skills": [
            {"name": "Python", "level": "Expert"},
            {"name": "Spark", "level": "Advanced"}
        ],
        "languages": [
            {"name": "English", "level": "Fluent"}
        ]
    }
    
    response = requests.post(f"{BASE_URL}/mongodb", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_get_all_rfps():
    """Test getting all RFPs"""
    print("\n[TEST] Get All RFPs")
    response = requests.get(f"{BASE_URL}/mongodb")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total RFPs: {data['count']}")
    if data['data']:
        print(f"First RFP: {data['data'][0]['role']} at {data['data'][0]['company_name']}")

if __name__ == "__main__":
    print("=" * 60)
    print("FuturScam API - Test Suite")
    print("=" * 60)
    print("\nNote: Make sure the API is running first!")
    print("Run: uvicorn main:app --reload")
    
    try:
        test_health()
        test_skillboy_health()
        test_skill_extraction()
        test_create_rfp()
        test_get_all_rfps()
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to API at", BASE_URL)
        print("Make sure the API is running: uvicorn main:app --reload")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
