# from backend.app.models import user
from datetime import time
import time
from fastapi import FastAPI
from config import settings
from routes import users, auths, tips
from db import Base, engine, SessionLocal
from services.lightning_service import connect_breez, pull_unpaid_invoices_since
from utils.sync_state import get_last_sync_state, set_last_sync_timestamp

Base.metadata.create_all(bind=engine)
app = FastAPI(title="ZapZap Backend")

@app.on_event("startup")
def startup_event():
    connect_breez(restore_only=True)

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
    return{
        "env": settings.ENVIRONMENT,
        "greet": settings.GREETING,
    }

@app.get("lightning/test-invoice")
def test_invoice():
    invoice = create_invoice(100, "Test invoice")
    return {"invoice": invoice}

@app.get("/lightning/test-balance")
def test_balance():
    return get_balance()

