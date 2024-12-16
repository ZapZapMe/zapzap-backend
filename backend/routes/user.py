from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.crud import get_user_by_username, create_user, update_bolt12_address
from app.db.database import SessionLocal

router = APIRouter()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic models for request validation
class UserCreate(BaseModel):
    twitter_username: str


class UpdateBolt12(BaseModel):
    bolt12_address: str


# Register a new user
@router.post("/register")
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, user.twitter_username)
    if db_user:
        raise HTTPException(status_code=400, detail="User already exists.")
    new_user = create_user(db, user.twitter_username)
    return {"message": f"User {new_user.twitter_username} registered successfully!"}


# Update Bolt12 address
@router.put("/update-bolt12/{username}")
async def update_bolt12(
    username: str, update: UpdateBolt12, db: Session = Depends(get_db)
):
    updated_user = update_bolt12_address(db, username, update.bolt12_address)
    if not updated_user:
        raise HTTPException(
            status_code=404, detail="User not found, or Bolt12 not updated."
        )
    return {"message": f"Bolt12 address updated for {username}"}


# Get user profile
@router.get("/profile/{username}")
async def get_profile(username: str, db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {
        "username": user.twitter_username,
        "bolt12_address": user.bolt12_address,
    }


# Get tips received by a user
@router.get("/tips/{username}")
async def get_tips(username: str, db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {
        "username": user.twitter_username,
        "tips": [
            {"id": tip.id, "amount": tip.amount, "message": tip.message}
            for tip in user.received_tips
        ],
    }
