from pydantic import BaseModel
from datetime import datetime

class UserCreate(BaseModel):
    twitter_username: str

class UserOut(BaseModel):
    id: int
    twitter_username: str
    created_at: datetime

    class Config:
        from_attributes = True
    