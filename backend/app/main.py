from fastapi import FastAPI

app = FastAPI(title="ZapZap Backend")

@app.get("/")
def root():
    return {"message": "ZapZap backend is running!"}