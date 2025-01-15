import logging

from db import get_db
from fastapi import APIRouter, Depends, HTTPException
from models.db import User
from schemas.user import (
    UserCreate,
    UserOut,
    UserUpdate,
)
from services.lightning_service import forward_pending_tips_for_user
from sqlalchemy.orm import Session
from utils.security import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut)
def update_user_profile(
    user_update: UserUpdate, db: Session = Depends(get_db)
):
    
    user = db.query(User).filter(User.twitter_username == "AyoRichie_98").first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found!")

    updated = False
    if user_update.wallet_address and user.wallet_address != user_update.wallet_address:
        user.wallet_address = user_update.wallet_address
        updated = True

    db.commit()
    db.refresh(user)

    if updated:
        logging.info(
            f"User @{user.twitter_username} updated their wallet address. Initiating forwarding of pending tips."
        )
        forward_pending_tips_for_user(user.id, db)
    return user


@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users


@router.post("/", response_model=UserCreate)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.twitter_username == user_data.twitter_username).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="User already exists")

    new_user = User(twitter_username=user_data.twitter_username)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
