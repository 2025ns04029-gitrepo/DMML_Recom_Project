from fastapi import FastAPI

app = FastAPI(title="Titanic Recommendation Demo")


@app.get("/")
def health():
    return {
        "status": "running",
        "project": "Titanic Recommendation Pipeline",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}