import os
from fastapi import FastAPI

# from app.db.database import init_db, database
# from app.routes import user

app = FastAPI()

# Retrieve the database connection string from environment variables
# Example connection strings:
# 
# export DB_CONNECTION_STRING="postgresql://user:password@localhost/dbname"
# export DB_CONNECTION_STRING="sqlite:///./test.db"

db_connection_string = os.getenv("DB_CONNECTION_STRING")
if db_connection_string is None:
    print("DB_CONNECTION_STRING not set")
    exit(1)

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
    return {"Message": "Welcome to Tips API Service!"}
