from pydantic import BaseModel, Field, HTTPUrl, validator
from typing import List, Optional
from datetime import datetime


class TipCreate(BaseModel):
    amount: int = Field(...,gt=0, description="amount in sats")
    message: Optional[str] = Field(None, example="Great tweet!")
    receiver_username: str = Field(..., description="Optional comment for the tip.")
    tweet_url: HTTPUrl = Field(..., example="https://x.com/notgrubles/status/1869893445625557486")

    # @validator("receiver_username")
    # def validate_receiver_username(cls, v):
    #     if not v or not isinstance(v, str):
    #         raise ValueError("Receiver username must be a non-empty string!")
    #     return v

class TipSend(BaseModel):
    id: int
    amount: int
    message: Optional[str]
    sender_username: str
    timestamp: datetime
    tweet_url: HTTPUrl
    paid_out: bool
    payment_status: str
    sent_payment_status: Optional[str] = None

    class Config:
        orm_mode = True

