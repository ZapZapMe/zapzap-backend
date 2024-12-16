from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship


Base = declarative_base()

# User model
class User(Base):
    __tablename__ = "tips-user"

    id = Column(Integer, primary_key=True, index=True)
    twitter_username = Column(String, unique=True, nullable=False)
    bolt12_address = Column(String, nullable=True)
    is_registered = Column(Boolean, default=False)
    access_token = Column(String, nullable=True)

    received_tips = relationship("Tip", back_populates="recipient_user", foreign_keys="Tip.receiver")

# Tips model should reference user table foreign key for receiver
class Tip(Base):
    __tablename__ = "tips"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String, nullable=False)
    receiver = Column(ForeignKey("tips-user.id"), nullable=False)  # FK to User
    amount = Column(Integer, nullable=False)  # all amounts in Sats
    message = Column(String, nullable=True)
    
    recipient_user = relationship("User", back_populates="received_tips", foreign_keys=[receiver])
