from sqlalchemy import Column, Integer, String, DateTime
from db import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    twitter_username = Column(String, unique=True, index=True, nullable=False)
    # add a timestamp when the user was created
    created_at = Column(DateTime, default=datetime.utcnow)