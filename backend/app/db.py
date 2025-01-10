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
    if settings.ENVIRONMENT == "development":
        engine = sqlalchemy.create_engine(settings.LOCAL_DATABASE_URL)
        print("Local DB")
    else:
        print("Cloud DB")
        connector = Connector()

        def getconn() -> pg8000.dbapi.Connection:
            conn: pg8000.dbapi.Connection = connector.connect(
                os.environ["INSTANCE_CONNECTION_NAME"],
                "pg8000",
                user=os.environ["DB_USER"],
                password=os.environ["DB_PASS"],
                db=os.environ["DB_NAME"],
            )
            return conn

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
