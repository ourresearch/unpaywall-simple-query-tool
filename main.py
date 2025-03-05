import os
import asyncio
import json
from collections import defaultdict
import csv
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator
import httpx
from io import StringIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
UNPAYWALL_EMAIL = os.getenv("UNPAYWALL_EMAIL", "team@ourresearch.org")
UNPAYWALL_API_BASE_URL = "https://api.unpaywall.org"
MAX_DOIS_PER_REQUEST = 1000
MAX_CONCURRENT_REQUESTS = 100  # Maximum number of concurrent requests
REQUEST_TIMEOUT = 25  # Maximum time in seconds for a single request

app = FastAPI(title="Unpaywall Simple Query Tool")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DoiRequest(BaseModel):
    dois: List[str] = Field(..., description="List of DOIs to query")
    
    @field_validator('dois')
    @classmethod
    def validate_dois_count(cls, value):
        if len(value) > MAX_DOIS_PER_REQUEST:
            raise ValueError(f"Maximum number of DOIs per request is {MAX_DOIS_PER_REQUEST}")
        return value

@app.get("/")
async def root():
    return {"msg": "don't panic"}

def csv_dict_from_response_dict(data):
    if not data:
        return None

    response = defaultdict(str)
    response["doi"] = data.get("doi", None)
    response["doi_url"] = data.get("doi_url", None)
    response["is_oa"] = data.get("is_oa", None)
    response["oa_status"] = data.get("oa_status", None)
    response["genre"] = data.get("genre", None)
    response["is_paratext"] = data.get("is_paratext", None)
    response["journal_name"] = data.get("journal_name", None)
    response["journal_issns"] = data.get("journal_issns", None)
    response["journal_issn_l"] = data.get("journal_issn_l", None)
    response["journal_is_oa"] = data.get("journal_is_oa", None)
    response["journal_is_in_doaj"] = data.get("journal_is_in_doaj", None)
    response["publisher"] = data.get("publisher", None)
    response["published_date"] = data.get("published_date", None)
    response["data_standard"] = data.get("data_standard", None)

    best_location_data = data.get("best_oa_location", None)
    if not best_location_data:
        best_location_data = defaultdict(str)
    response["best_oa_url"] = best_location_data.get("url", "")
    response["best_oa_url_is_pdf"] = best_location_data.get("url_for_pdf", "") != ""
    response["best_oa_evidence"] = best_location_data.get("evidence", None)
    response["best_oa_host"] = best_location_data.get("host_type", None)
    response["best_oa_version"] = best_location_data.get("version", None)
    response["best_oa_license"] = best_location_data.get("license", None)

    return response

async def fetch_doi_data(doi: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Fetch data for a single DOI from the Unpaywall API."""
    # Validate DOI format
    if not doi.startswith("10."):
        return {
            "doi": doi,
            "error": "Invalid DOI format",
            "message": "DOI must start with '10.'"
        }
    
    url = f"{UNPAYWALL_API_BASE_URL}/{doi}"
    params = {
        "email": UNPAYWALL_EMAIL
    }
    
    try:
        response = await client.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        # Handle HTTP errors (4xx, 5xx)
        return {
            "doi": doi,
            "error": f"HTTP error: {e.response.status_code}",
            "message": str(e)
        }
    except httpx.RequestError as e:
        # Handle request errors (connection, timeout, etc.)
        return {
            "doi": doi,
            "error": "Request error",
            "message": str(e)
        }
    except Exception as e:
        # Handle any other unexpected errors
        return {
            "doi": doi,
            "error": "Unexpected error",
            "message": str(e)
        }

@app.post("/v2/dois")
async def process_dois(request: DoiRequest) -> Dict[str, Any]:
    """
    Process a batch of DOIs and return data from the Unpaywall API.
    
    This endpoint accepts a list of DOIs (maximum 1000) and queries the Unpaywall API 
    for each one in parallel, returning the results in multiple formats:
    - JSON dictionary (standard format)
    - JSON lines
    - CSV with selected fields
    """
    # Create a semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    async def fetch_with_semaphore(doi: str, client: httpx.AsyncClient) -> Dict[str, Any]:
        async with semaphore:
            return await fetch_doi_data(doi, client)
    
    # Create list of tasks for each DOI
    async with httpx.AsyncClient() as client:
        tasks = [fetch_with_semaphore(doi, client) for doi in request.dois]
        results = await asyncio.gather(*tasks)
    
    # Organize results by DOI
    doi_results = {}
    error_results = {}  # Dictionary to store errors
    
    # Prepare for JSON lines format
    jsonl_results = []
    
    # Prepare for CSV format
    csv_data = []
    csv_fieldnames = []
    
    for result in results:
        if "doi" in result:
            doi = result["doi"]
            doi_results[doi] = result
            
            # Add to JSON lines format (only for successful results)
            if "error" not in result:
                jsonl_results.append(result)
                
                # Add to CSV format
                csv_result = csv_dict_from_response_dict(result)
                if csv_result:
                    # Set fieldnames once based on the first valid result
                    if not csv_fieldnames and csv_result:
                        csv_fieldnames = list(csv_result.keys())
                    csv_data.append(csv_result)
            
            # If this is an error result, add to the error_results dictionary
            if "error" in result:
                error_results[doi] = {
                    "error": result.get("error"),
                    "message": result.get("message")
                }
    
    # Generate JSON lines format
    jsonl_output = ""
    for item in jsonl_results:
        jsonl_output += json.dumps(item) + "\n"
    
    # Generate CSV format
    csv_output = ""
    if csv_data:
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=csv_fieldnames)
        writer.writeheader()
        for row in csv_data:
            writer.writerow(row)
        csv_output = output.getvalue()
    
    return {
        "results": doi_results,
        "errors_dict": error_results,
        "total": len(results),
        "success": len([r for r in results if "error" not in r]),
        "errors": len([r for r in results if "error" in r]),
        # Add the new formats
        "jsonl": jsonl_output,
        "csv": csv_output
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
