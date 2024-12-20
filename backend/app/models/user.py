from sqlalchemy import Column, Integer, String, DateTime, Boolean
from db import Base
from datetime import datetime
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    twitter_username = Column(String, unique=True, index=True, nullable=False)
    # add a timestamp when the user was created
    created_at = Column(DateTime, default=datetime.utcnow)
    bolt12_address = Column(String, nullable=True, index=True)
    is_admin = Column(Boolean, default=False)

    # add a relationship to the Tip model
    sent_tips = relationship("Tip", foreign_keys="Tip.sender_id", back_populates="sender")
    received_tips = relationship("Tip", foreign_keys="Tip.receiver_id", back_populates="receiver")
