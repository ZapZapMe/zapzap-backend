from config import settings
from db import (
    Base,
    engine,
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import (
    auths,
    sse,
    tips,
    users,
)
from services.lightning_service import connect_breez

# Create all DB tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI without the lifespan context manager
app = FastAPI(title="ZapZap Backend")


# On startup, connect to Breez
@app.on_event("startup")
def startup_event():
    connect_breez(restore_only=True)


# Define allowed CORS origins
origins = [
    "https://zap-zap.me",
    "http://localhost:5000",
    "http://localhost:3000",
    "https://beta.zap-zap.me",
    "https://prod.zap-zap.me/",
]

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origins], # change this to origins to enable CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your routes
app.include_router(users.router)
app.include_router(auths.router)
app.include_router(tips.router)
app.include_router(sse.router)


@app.get("/")
def root():
    return {"message": "Ross Ulbricht is free!"}


@app.get("/config-check")
def config_check():
    return {
        "env": settings.ENVIRONMENT,
        "greet": settings.GREETING,
    }
