from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from db import Base
from datetime import datetime


class Tip(Base):
    __tablename__ = "tips"

    id = Column(Integer, primary_key=True, index=True)
    tipper_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    recipient_twitter_username = Column(String, nullable=False, index=True)
    tweet_url = Column(String, nullable=False)

    bolt11_invoice = Column(String, nullable=False, index=True)
    ln_payment_hash = Column(String, nullable=True, index=True)

    comment = Column(String, nullable=True)
    amount_sats = Column(Integer, nullable=False)

    paid = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    tipper_user = relationship("User", backref="tips", lazy="joined")

