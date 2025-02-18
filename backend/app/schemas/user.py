from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import validator
from utils.validators import WalletAddressValidator


class UserCreate(BaseModel):
    twitter_username: str
    wallet_address: Optional[str] = None

    @validator('wallet_address')
    def validate_wallet_address(cls, v):
        if v is None:
            return v
        is_valid, error_msg = WalletAddressValidator.validate(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.strip()  # Just remove whitespace, preserve case

    @validator('twitter_username')
    def validate_twitter_username(cls, v):
        if not v:
            raise ValueError("Twitter username cannot be empty")
        return v.lower()  # Twitter usernames should be lowercase

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    wallet_address: Optional[str] = None

    @validator('wallet_address')
    def validate_wallet_address(cls, v):
        if v is None:
            return v
        is_valid, error_msg = WalletAddressValidator.validate(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.strip()  # Just remove whitespace, preserve case


class UserOut(BaseModel):
    id: int
    twitter_username: str
    created_at: datetime
    wallet_address: Optional[str]
    is_admin: bool
    is_registered: bool
    avatar_url: Optional[str] = None

    class Config:
        orm_mode = True

class UserLimitedOut(BaseModel):
    twitter_username: str
    wallet_address: str | None
    avatar_url: str | None
    twitter_link: str | None

    class Config:
        from_attributes = True