from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, validator


class TipCreate(BaseModel):
    recipient_twitter_username: str
    amount_sats: int
    comment: Optional[str] = None
    tweet_url: HttpUrl
    tipper_display_name: Optional[str] = "anonymous"


class TipOut(BaseModel):
    id: int
    amount_sats: int
    comment: Optional[str]
    bolt11_invoice: str
    recipient_twitter_username: str
    created_at: datetime
    tweet_url: str
    paid_in: bool
    paid_out: bool
    ln_payment_hash: Optional[str] = None
    forward_payment_hash: Optional[str] = None

    class Config:
        orm_mode = True

class TipUpdate(BaseModel):
    paid_in: bool
    paid_out: bool

class LeaderboardReceived(BaseModel):
    recipient_twitter_username: str
    total_amount_sats: int
    tip_count: int

class LeaderboardSent(BaseModel):
    tipper_display_name: str
    total_amount_sats: int
    tip_count: int
