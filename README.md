# Unpaywall Simple Query Tool

This is a simple wrapper around the Unpaywall API for people who don't want to use the REST interface. It only has one endpoint: `POST v2/dois` 

When you call that endpoint, you include a JSON body which contains one key 'dois' which contains a list of DOIs. 

```json
{
    "dois": [
        "10.1371/journal.pone.0022647",
        "10.1371/journal.pone.0031296"
    ]
}
```

The endpoint then checks each DOI against the Unpaywall API and returns the results.

For each DOI, it sends this request:

```
https://api.unpaywall.org/<DOI>?email=team@ourresearch.org
```

It can run a maximum of 1,000 DOIs at a time.

Because this is running on Heroku, it times out after 30 seconds. So we have to make API calls in parallel. The function maintains a thread pool, calling up to 100 requests at a time. 

## Local Development

### Prerequisites
- Python 3.7+
- pip (Python package installer)

### Setup
1. Clone the repository
```bash
git clone https://github.com/yourusername/unpaywall-simple-query-tool.git
cd unpaywall-simple-query-tool
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Run the application
```bash
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

## Endpoints

- `GET /`: Returns a simple message `{"msg": "don't panic"}`
- `POST /v2/dois`: Process a batch of DOIs and return data from the Unpaywall API
  - Request body: JSON with a single key `dois` containing an array of DOI strings
  - Maximum 1,000 DOIs per request
  - Returns a JSON response with:
    - `results`: Object containing the Unpaywall data for each DOI
    - `total`: Total number of DOIs processed
    - `success`: Number of successful DOI lookups
    - `errors`: Number of failed DOI lookups

### Example Request
```bash
curl -X POST https://unpaywall-simple-query-tool-c76bcdcacd9a.herokuapp.com/v2/dois \
  -H "Content-Type: application/json" \
  -d '{"dois": ["10.1371/journal.pone.0022647", "10.1371/journal.pone.0031296"]}'
```

## API Documentation

Once the server is running, you can access the auto-generated API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Heroku Deployment

1. Create a Heroku account if you don't have one
2. Install the Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
3. Login to Heroku
```bash
heroku login
```

4. Create a new Heroku app
```bash
heroku create your-app-name
```

5. Deploy to Heroku
```bash
git push heroku main
```

6. Open the deployed app
```bash
heroku open