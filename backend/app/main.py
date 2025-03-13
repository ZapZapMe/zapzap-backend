import asyncio
import logging

from config import settings
from db import Base, engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auths, sse, tips, users
from routes.sse import cleanup_stale_connections
from services.lightning_service import connect_breez, init_breez_logging
from services.twitter_mention_monitor import mention_monitor
from services.twitter_service import verify_twitter_credentials

# Create all DB tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI without the lifespan context manager
app = FastAPI(title="ZapZap Backend")

cleanup_task = None
breez_retry_task = None
breez_connected = False


async def try_reconnect_breez():
    global breez_connected

    logging.info("Breez reconnection task started")

    while not breez_connected:
        logging.info("Attempting to reconnect to Breez...")
        try:
            success = connect_breez(restore_only=True)
            logging.info(f"Connection attempt result: {success}")

            if success:
                from services.lightning_service import sdk_services

                logging.info(f"SDK services after connect attempt: {sdk_services is not None}")

                if sdk_services is not None:
                    breez_connected = True
                    logging.info("Breez Connected Successfully!")
                else:
                    breez_connected = False
                    logging.error("Breez SDK service is None despite connection.")
        except Exception as e:
            logging.error(f"Error during Breez reconnection attempt: {e}")
            breez_connected = False
        if not breez_connected:
            logging.info("Retrying Breez connection in 5 seconds...")
            await asyncio.sleep(5)
    logging.info("Exiting Breez reconnect loop.")


@app.on_event("startup")
async def startup_event():
    global cleanup_task, breez_retry_task, breez_connected

    init_breez_logging()

    try:
        success = connect_breez(restore_only=True)
        if success:
            from services.lightning_service import sdk_services

            if sdk_services is not None:
                breez_connected = True
                logging.info("Breez connected on startup.")
        else:
            logging.error("Failed to connect Breez on startup, will start retry loop.")
    except Exception as e:
        logging.error(f"Error during Breez connection: {e}")

    if not breez_connected:
        breez_retry_task = asyncio.create_task(try_reconnect_breez())
    try:
        await verify_twitter_credentials()
        logging.info("Twitter credentials verified successfully")
    except Exception as e:
        logging.error(f"Twitter credentials verification failed: {str(e)}")
        logging.warning("Avatar updates may not work, but app will continue running")

    # Start Twitter mention monitoring
    asyncio.create_task(mention_monitor.start_monitoring())

    # Start SSE cleanup task
    cleanup_task = asyncio.create_task(cleanup_stale_connections())
    logging.info("SSE cleanup task started")


# Add shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    global cleanup_task, breez_retry_task
    # Cancel SSE cleanup task
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

    if breez_retry_task:
        breez_retry_task.cancel()
        try:
            await breez_retry_task
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
    return {"env": settings.ENVIRONMENT, "greet": settings.GREETING, "breez_connected": bool(sdk_services)}
