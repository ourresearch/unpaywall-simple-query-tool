#!/usr/bin/env python
"""
Script to test the Unpaywall API wrapper with a small number of DOIs.
"""
import httpx
import json
import sys
import time

def main():
    # Read a small number of DOIs
    with open("small_test.txt", 'r') as f:
        dois = [line.strip() for line in f if line.strip()]
    
    print(f"Testing with {len(dois)} DOIs")
    
    # Make a local request to our API
    api_url = "http://localhost:8000/v2/dois"
    payload = {"dois": dois}
    
    try:
        response = httpx.post(api_url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Print all formats for easy inspection
        print("\nStandard JSON response (partial):")
        print(json.dumps(data.get("results", {}), indent=2)[:200] + "...\n")
        
        print("\nJSON Lines format:")
        print(data.get("jsonl", "No JSON lines data"))
        
        print("\nCSV format:")
        print(data.get("csv", "No CSV data"))
        
    except Exception as e:
        print(f"Error testing API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
