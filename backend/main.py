from fastapi import FastAPI

# from app.db.database import init_db, database
# from app.routes import user

app = FastAPI()

# # Initialize the database tables
# @app.on_event("startup")
# async def startup():
#     init_db()
#     await database.connect()

# @app.on_event("shutdown")
# async def shutdown():
#     await database.disconnect()


@app.get("/")
async def root():
    return {"Message": "Welcome to Tips API"}
