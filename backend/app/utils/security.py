from jose import jwt, JWTError
from datetime import datetime, timedelta
from config import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from sqlalchemy.orm import Session
from db import get_db
from models.user import User


oath2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/twitter/login')

class TokenData:
    user_twitter_username: Optional[str] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(seconds=settings.JWT_ACCESS_TOKEN_EXPIRE_SECONDS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_jwt_token(token: str) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials."
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_twitter_username: str = payload.get("sub")
        if user_twitter_username is None:
            raise credentials_exception
        token_data = TokenData()
        token_data.user_twitter_username = user_twitter_username
        return token_data
    except JWTError:
        raise credentials_exception


def get_current_user(token: str = Depends(oath2_scheme), db: Session = Depends(get_db)) -> User:
    token_data = decode_jwt_token(token)
    user = db.query(User).filter(User.twitter_username == token_data.user_twitter_username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found."
        )
    return user
