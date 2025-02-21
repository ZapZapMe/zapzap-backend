import asyncio

from config import settings
from db import Base, engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auths, sse, tips, users
from routes.sse import cleanup_stale_connections
from services.lightning_service import connect_breez

# Create all DB tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI without the lifespan context manager
app = FastAPI(title="ZapZap Backend")


# On startup, connect to Breez and start SSE cleanup
@app.on_event("startup")
async def startup_event():
    # Start Breez
    connect_breez(restore_only=True)

    # Start SSE cleanup task
    global cleanup_task
    cleanup_task = asyncio.create_task(cleanup_stale_connections())


# Add shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    # Cancel SSE cleanup task
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass


# Define allowed CORS origins
origins = [
    "https://zap-zap.me",
    "http://localhost:3000",
    "https://beta.zap-zap.me",
]

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # change this to origins to enable CORS
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
