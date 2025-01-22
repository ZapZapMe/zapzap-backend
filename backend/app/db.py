import os

import pg8000
import sqlalchemy
from config import settings
from google.cloud.sql.connector import Connector
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
)

Base = declarative_base()


def get_engine() -> sqlalchemy.engine.base.Engine:
    # If we're in development, use local SQLite
    if settings.ENVIRONMENT == "development":
        engine = sqlalchemy.create_engine(settings.LOCAL_DATABASE_URL)
        print("Connecting using Sqlite DB")
    else:
        db_host = os.environ.get("DB_HOST")
        if db_host == "cloudsql-proxy":  # if we are running inside Docker Compose
            print("DB_HOST is set; connecting via host/port instead of Cloud SQL connector.")
            engine = sqlalchemy.create_engine(
                f"postgresql+pg8000://{settings.DB_USER}:{settings.DB_PASS}@{db_host}:5432/{settings.DB_NAME}"
            )
        else:
            print("No DB_HOST set; using Cloud SQL connector as usual.")
            connector = Connector()

            def getconn():
                return connector.connect(
                    settings.DB_INSTANCE_CONNECTION_NAME,
                    "pg8000",
                    user=settings.DB_USER,
                    password=settings.DB_PASS,
                    db=settings.DB_NAME,
                )

            engine = sqlalchemy.create_engine(
                "postgresql+pg8000://",
                creator=getconn,
            )
    return engine


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
