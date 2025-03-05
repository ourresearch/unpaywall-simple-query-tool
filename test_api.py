#!/usr/bin/env python
"""
Script to test the Unpaywall API wrapper with the collected DOIs.
"""
import httpx
import json
import sys
import time
from typing import List, Dict, Any

# Number of DOIs to test
TEST_DOI_COUNT = 1000  # Changed from 20 to 1000 as requested

def load_dois(filename: str, limit: int = TEST_DOI_COUNT) -> List[str]:
    """Load DOIs from a file."""
    with open(filename, 'r') as f:
        dois = [line.strip() for line in f if line.strip()]
    return dois[:limit]

def test_api(dois: List[str]):
    """Test the Unpaywall API wrapper with the provided DOIs."""
    # Use production server
    api_url = "https://unpaywall-simple-query-tool-c76bcdcacd9a.herokuapp.com/v2/dois"
    
    try:
        start_time = time.time()
        
        # Make the request to our API
        payload = {"dois": dois}
        response = httpx.post(api_url, json=payload, timeout=60)  # Increased timeout for 1000 DOIs
        response.raise_for_status()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Parse the response
        data = response.json()
        
        # Save entire response to file
        response_filename = "api_response_1000_dois.json"
        with open(response_filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nFull response saved to {response_filename}")
        
        print(f"API call completed in {elapsed_time:.2f} seconds")
        print(f"Total DOIs: {data.get('total', 'N/A')}")
        print(f"Successful: {data.get('success', 'N/A')}")
        print(f"Errors: {data.get('errors', 'N/A')}")
        
        # Find and display error information
        if 'results' in data:
            error_results = []
            for doi, result in data['results'].items():
                if 'error' in result:
                    error_results.append({
                        'doi': doi,
                        'error': result.get('error'),
                        'message': result.get('message')
                    })
            
            if error_results:
                print("\nError details:")
                for i, err in enumerate(error_results, 1):
                    print(f"  {i}. DOI: {err['doi']}")
                    print(f"     Error type: {err['error']}")
                    print(f"     Message: {err['message']}")
                    print()
            else:
                print("\nNo errors found in the results.")
        
        # Display information about the errors_dict
        if 'errors_dict' in data:
            error_count = len(data['errors_dict'])
            print(f"\nErrors dictionary contains {error_count} DOIs with errors")
            
            if error_count > 0:
                print("\nSample error from errors_dict:")
                first_error_doi = next(iter(data['errors_dict']))
                print(f"  DOI: {first_error_doi}")
                print(f"  Error details: {json.dumps(data['errors_dict'][first_error_doi], indent=2)}")
        
        # Print a sample of a successful result
        successful_results = {doi: result for doi, result in data.get('results', {}).items() 
                              if 'error' not in result}
        if successful_results:
            first_doi = next(iter(successful_results))
            print("\nSample successful result:")
            print(json.dumps(successful_results[first_doi], indent=2)[:500] + "...\n")
        
    except Exception as e:
        print(f"Error testing API: {e}")
        sys.exit(1)

def main():
    """Main function to test the API."""
    # Load DOIs
    print(f"Loading the first {TEST_DOI_COUNT} DOIs from test_dois.txt...")
    dois = load_dois("test_dois.txt")
    print(f"Loaded {len(dois)} DOIs")
    
    # Test the API
    print(f"\nTesting API with {len(dois)} DOIs...")
    test_api(dois)

if __name__ == "__main__":
    main()
