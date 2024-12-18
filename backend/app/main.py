from fastapi import FastAPI
from .config import settings

app = FastAPI(title="ZapZap Backend")

@app.get("/")
def root():
    return {"message": "ZapZap backend is running!"}

@app.get("/config-check")
def config_check():
    return{
        "env": settings.ENVIRONMENT,
        "greet": settings.GREETING,
    }