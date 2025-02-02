from datetime import datetime
from typing import (
    Optional,
)

from pydantic import (
    BaseModel,
    HttpUrl,
)


class TipCreate(BaseModel):
    # tip_recipient: int
    amount_sats: int
    comment: Optional[str] = None
    tweet_url: HttpUrl
    tip_sender: Optional[str] = "anonymous"


class TipOut(BaseModel):
    id: int
    tip_sender: Optional[str]
    amount_sats: int
    comment: Optional[str]
    created_at: datetime
    tweet_id: int
    paid_in: bool
    paid_out: bool
    ln_payment_hash: Optional[str] = None
    forward_payment_hash: Optional[str] = None
    bolt11_invoice: Optional[str] = None

    class Config:
        orm_mode = True


class TipUpdate(BaseModel):
    paid_in: bool
    paid_out: bool


class LeaderboardReceived(BaseModel):
    tip_recipient: str
    total_amount_sats: int
    tip_count: int
    avatar_url: Optional[HttpUrl] = None


class LeaderboardSent(BaseModel):
    tip_sender: str
    total_amount_sats: int
    tip_count: int
    avatar_url: Optional[HttpUrl] = None


class TipSummary(BaseModel):
    tip_sender: Optional[str]
    amount_sats: int
    created_at: datetime
    tweet_id: int
    recipient: str
    avatar_url: Optional[str] = None

    class Config:
        orm_mode = True


class TipInvoice(BaseModel):
    tip_recipient: str
    amount_sats: int
    bolt11_invoice: str
