from fastapi import FastAPI

app = FastAPI(title="Unpaywall Simple Query Tool")

@app.get("/")
async def root():
    return {"msg": "don't panic"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
