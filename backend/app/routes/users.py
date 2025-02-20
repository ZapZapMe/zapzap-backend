import logging

from db import get_db
from fastapi import APIRouter, Depends, HTTPException
from models.db import User
from schemas.user import UserCreate, UserLimitedOut, UserOut, UserUpdate
from services.lightning_service import forward_pending_tips_for_user
from services.twitter_service import get_avatars_for_usernames
from sqlalchemy import func
from sqlalchemy.orm import Session
from utils.security import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_users_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result_dic = get_avatars_for_usernames([current_user.twitter_username], db)
    avatar_url = result_dic.get(current_user.twitter_username, None)
    current_user.avatar_url = avatar_url
    return current_user


@router.put("/me", response_model=UserOut)
def update_user_profile(
    user_update: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.twitter_username == current_user.twitter_username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found!")

    updated = False
    if user_update.wallet_address is not None:  # Allow explicitly setting to None
        # Validation is already handled by Pydantic model
        if user.wallet_address != user_update.wallet_address:
            user.wallet_address = user_update.wallet_address
            updated = True

    db.commit()
    db.refresh(user)

    if updated and user.wallet_address:
        logging.info(
            f"User @{user.twitter_username} updated their wallet address. Initiating forwarding of pending tips."
        )
        forward_pending_tips_for_user(user.id, db)
    return user


@router.post("/", response_model=UserCreate)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Username is already lowercase from Pydantic validation
    existing_user = db.query(User).filter(User.twitter_username == user_data.twitter_username).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="User already exists")

    new_user = User(twitter_username=user_data.twitter_username, wallet_address=user_data.wallet_address)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/{username}", response_model=UserLimitedOut)
def get_user_by_username(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.twitter_username) == username.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Use the user's actual Twitter username from the database for consistency
    result_dic = get_avatars_for_usernames([user.twitter_username], db)
    avatar_url = result_dic.get(user.twitter_username, None)

    user_data = {
        "twitter_username": user.twitter_username,
        "wallet_address": user.wallet_address,
        "avatar_url": avatar_url,
        "twitter_link": f"https://x.com/{user.twitter_username}",
    }

    return user_data
