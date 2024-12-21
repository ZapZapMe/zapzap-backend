from sqlalchemy import Column, Integer, DateTime
from db import Base
from datetime import datetime


class SyncState(Base):
    __tablename__ = "sync_state"

    id = Column(Integer, primary_key=True, index=True)
    last_timestamp = Column(DateTime, nullable=False, default="2009-01-03 00:00:00")