from models.user import User
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from schemas.user import UserCreate, UserOut
from utils.security import get_current_user
#from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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

