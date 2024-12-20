from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from db import Base
from datetime import datetime


class Tips(Base):
    __tablename__ = "tips"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer, nullable=False)
    message = Column(String, nullable=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    tweet_id = Column(Integer, nullable=False)
    paid_out = Column(Boolean, default=False)

    receive_ln_invoice = Column(String, nullable=False, unique=True, index=True)
    receive_payment_hash = Column(String, nullable=False, unique=True, index=True)
    recieve_payment_status = Column(String, default="pending")

    
    send_payment_hash = Column(String, nullable=False, unique=True, index=True)
    send_payment_status = Column(String, default="pending")


    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_tips")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_tips")

