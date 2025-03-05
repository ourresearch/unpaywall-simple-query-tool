# Unpaywall Simple Query Tool

A simple API for the Unpaywall project. Currently provides a basic endpoint that returns a "don't panic" message.

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