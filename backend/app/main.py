# from backend.app.models import user
import logging
import time

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
    add_liquid_event_listener,
    connect_breez,
    create_invoice,
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


@app.on_event("startup")
def startup_event():
    connect_breez(restore_only=True)

    listener_id = add_liquid_event_listener()
    logging.info(f"[startup_event] Nodeless event listener added, ID: {listener_id}")
    print(f"[startup_event] Nodeless event listener added, ID: {listener_id}")

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
    return {"message": "ZapZap backend is running!"}


@app.get("/config-check")
def config_check():
    return {
        "env": settings.ENVIRONMENT,
        "greet": settings.GREETING,
    }


@app.get("/lightning/test-invoice")
def test_invoice():
    amount = 1100
    invoice, temp, temp1 = create_invoice(amount, "Test invoice")
    return {"invoice": invoice}


# @app.get("/lightning/test-balance")
# def test_balance():
#     return get_balance()
