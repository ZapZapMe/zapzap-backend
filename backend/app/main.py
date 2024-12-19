# from backend.app.models import user
from fastapi import FastAPI
from config import settings
from routes import users, auths
from db import Base, engine

Base.metadata.create_all(bind=engine)
app = FastAPI(title="ZapZap Backend")
 
app.include_router(users.router)
app.include_router(auths.router)

@app.get("/")
def root():
    return {"message": "ZapZap backend is running!"}

@app.get("/config-check")
def config_check():
    return{
        "env": settings.ENVIRONMENT,
        "greet": settings.GREETING,
    }
