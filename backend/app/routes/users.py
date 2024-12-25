from models.user import User
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
import logging
from schemas.user import UserCreate, UserOut, UserUpdate
from utils.security import get_current_user
from services.lightning_service import forward_payment_to_receiver

router = APIRouter(prefix="/users", tags=["users"])

@router.put("/me", response_model=UserOut)
def update_user_profile( current_user: str, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.twitter_username == current_user).first()
    print("User:", user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found!")
    
    updated = False
    if user_update.bolt12_address and user.bolt12_address != user_update.bolt12_address:
        user.bolt12_address = user_update.bolt12_address
        updated = True

    db.commit()
    db.refresh(user)

    if updated:
        logging.info(f"User @{user.twitter_username} updated their BOLT12 address. Initiating forwarding of pending tips.")
        forward_payment_to_receiver(user.id)
    return user

@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
    

@router.post("/", response_model=UserOut)
def create_user(user_data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing_user = db.query(User).filter(User.twitter_username == user_data.twitter_username).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="User already exists")

    new_user = User(twitter_username=user_data.twitter_username)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

