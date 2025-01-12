from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    twitter_username: str
    wallet_address: Optional[str]
    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    wallet_address: Optional[str]


class UserOut(BaseModel):
    id: int
    twitter_username: str
    created_at: datetime
    wallet_address: Optional[str]
    is_admin: bool
    is_registered: bool

    class Config:
        orm_mode = True
