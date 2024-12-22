from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Optional
from datetime import datetime


class TipCreate(BaseModel):
    recipient_twitter_username: str
    amount_sats: int
    comment: Optional[str] = None
    tweet_url: HttpUrl


class TipOut(BaseModel):
    temp_id: int
    amount_sats: int
    comment: Optional[str]
    bolt11_invoice: str
    recipient_twitter_username: str
    created_at: datetime
    tweet_url: str
    paid: bool
    ln_payment_hash: Optional[str] = None

    class Config:
        orm_mode = True

class TipUpdate(BaseModel):
    paid: bool
