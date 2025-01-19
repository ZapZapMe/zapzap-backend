from contextlib import asynccontextmanager

from config import settings
from db import (
    Base,
    engine,
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import (
    auths,
    tips,
    users,
)
from services.lightning_service import (
    connect_breez,
)

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_breez(restore_only=True)
    yield
    print("ZapZap Backend is shutting down...")


app = FastAPI(title="ZapZap Backend", lifespan=lifespan)


origins = [
    "https://zap-zap.me",
    "https://www.zap-zap.me",
    "http://localhost:5000",  # Added for local development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow these origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(users.router)
app.include_router(auths.router)
app.include_router(tips.router)


@app.get("/")
def root():
    return {"message": "ZapZap backend is running with Greenlight!"}


@app.get("/config-check")
def config_check():
    return {
        "env": settings.ENVIRONMENT,
        "greet": settings.GREETING,
    }
