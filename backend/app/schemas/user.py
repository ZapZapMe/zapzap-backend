from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    twitter_username: str
    bolt12_address: Optional[str]

class UserUpdate(BaseModel):
    bolt12_address: Optional[str]

class UserOut(BaseModel):
    id: int
    twitter_username: str
    created_at: datetime
    bolt12_address: Optional[str]

    class Config:
        orm_mode = True
    