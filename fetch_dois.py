#!/usr/bin/env python
"""
Script to fetch DOIs from OpenAlex API and save them to a text file.
"""
import httpx
import time
import random
from typing import List, Dict, Any
import sys

# Constants
BASE_URL = "https://api.openalex.org/works"
OUTPUT_FILE = "test_dois.txt"
SLEEP_BETWEEN_REQUESTS = 1  # seconds to sleep between requests to be kind to the API
TARGET_DOI_COUNT = 2000

def fetch_works(cursor: str = "*", page_size: int = 100) -> Dict[str, Any]:
    """
    Fetch a page of works from OpenAlex API.
    
    Args:
        cursor: The cursor for pagination
        page_size: Number of results per page
        
    Returns:
        API response as dictionary
    """
    params = {
        "filter": "has_doi:true",
        "select": "doi",
        "per-page": str(page_size),
        "cursor": cursor
    }
    
    print(f"Fetching page with cursor {cursor}...")
    response = httpx.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def extract_dois(data: Dict[str, Any]) -> List[str]:
    """Extract DOIs from the API response."""
    dois = []
    for work in data.get("results", []):
        if "doi" in work and work["doi"]:
            # Remove the 'https://doi.org/' prefix if it exists
            doi = work["doi"]
            if doi.startswith("https://doi.org/"):
                doi = doi[16:]  # Remove the prefix
            dois.append(doi)
    return dois

def main():
    """Main function to fetch DOIs and save them to a file."""
    all_dois = set()  # Use a set to avoid duplicates
    cursor = "*"
    
    try:
        while len(all_dois) < TARGET_DOI_COUNT:
            data = fetch_works(cursor)
            page_dois = extract_dois(data)
            
            # Add DOIs to our set
            all_dois.update(page_dois)
            print(f"Total DOIs collected so far: {len(all_dois)}")
            
            # Get the next cursor for pagination
            if "meta" in data and "next_cursor" in data["meta"]:
                cursor = data["meta"]["next_cursor"]
                # Sleep between requests to be kind to the API
                time.sleep(SLEEP_BETWEEN_REQUESTS)
            else:
                print("No next cursor found. Ending collection.")
                break
            
            # Break if we've reached the target
            if len(all_dois) >= TARGET_DOI_COUNT:
                break
    
    except Exception as e:
        print(f"Error fetching data: {e}")
    
    # Convert set to list and take the first TARGET_DOI_COUNT items
    doi_list = list(all_dois)[:TARGET_DOI_COUNT]
    
    # Write the DOIs to a file, one per line
    with open(OUTPUT_FILE, "w") as f:
        for doi in doi_list:
            f.write(f"{doi}\n")
    
    print(f"Saved {len(doi_list)} DOIs to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
