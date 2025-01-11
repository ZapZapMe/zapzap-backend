# from backend.app.models import user
import logging
import time

import breez_sdk
from breez_sdk import ConnectRequest, EnvironmentType, EventListener, NodeConfig, default_config, mnemonic_to_seed
from config import settings
from db import (
    Base,
    SessionLocal,
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
    # add_greenlight_event_listener,
    connect_breez,
    pull_unpaid_invoices_since,
)
from utils.sync_state import (
    get_last_sync_state,
    set_last_sync_timestamp,
)

Base.metadata.create_all(bind=engine)
app = FastAPI(title="ZapZap Backend")

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


# class SdkLogger(Logger):
#     def log(log_entry: LogEntry):
#         logging.debug("Received log [", log_entry.level, "]: ", log_entry.line)


# def set_logger(logger: SdkLogger):
#     try:
#         breez_sdk_liquid.set_logger(logger)
#     except Exception as error:
#         logging.error(error)
#         raise


# class SdkLogger(Logger):
#     def log(self, log_entry: LogEntry):
#         log_level = log_entry.level
#         log_line = log_entry.line

#         print(f"[SDK {log_level} and {log_line}]")


# def initialize_logger():
#     try:
#         breez_sdk_liquid.set_logger(SdkLogger())
#         print("Breez SDK Logger initiated.")
#     except Exception as e:
#         print("Failed to initialize logger", e)
#         raise


@app.on_event("startup")
def startup_event():
    connect_breez(restore_only=True)

    # logging.basicConfig(level=logging.DEBUG)
    # logger = SdkLogger()
    # set_logger(logger)

    # listener_id = add_greenlight_event_listener()
    # logging.info(f"[startup_event] Greenlight event listener added, ID: {listener_id}")
    # print(f"[startup_event] Greenlight event listener added, ID: {listener_id}")

    with SessionLocal() as db:
        last_ts = get_last_sync_state(db)

    pull_unpaid_invoices_since(last_ts)

    new_ts = int(time.time())
    with SessionLocal() as db:
        set_last_sync_timestamp(db, new_ts)


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
