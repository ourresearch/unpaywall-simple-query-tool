import os
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import httpx
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
    
    @validator('dois')
    def validate_dois(cls, dois):
        if len(dois) > MAX_DOIS_PER_REQUEST:
            raise ValueError(f"Maximum number of DOIs per request is {MAX_DOIS_PER_REQUEST}")
        
        # Basic DOI format validation
        for doi in dois:
            if not doi.startswith("10."):
                raise ValueError(f"Invalid DOI format: {doi}")
        
        return dois

@app.get("/")
async def root():
    return {"msg": "don't panic"}

async def fetch_doi_data(doi: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Fetch data for a single DOI from the Unpaywall API."""
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
    for each one in parallel, returning the results.
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
    for result in results:
        if "doi" in result:
            doi = result["doi"]
            doi_results[doi] = result
    
    return {
        "results": doi_results,
        "total": len(results),
        "success": len([r for r in results if "error" not in r]),
        "errors": len([r for r in results if "error" in r])
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
