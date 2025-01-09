import logging
from datetime import timedelta

from config import settings
from db import get_db
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from models.user import User
from schemas.auth import Token
from sqlalchemy.orm import Session
from utils.security import create_access_token
from utils.twitter_oauth import (
    exchange_code_for_token,
    get_authorization_url,
    get_twitter_user_info,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/twitter/login")
def twitter_login():
    url = get_authorization_url()
    logging.info("Redirecting user to Twitter for authentication")
    return {"authorization_url": url}


@router.get("/twitter/callback", response_model=Token)
async def twitter_callback(request: Request, db: Session = Depends(get_db)):
    code = request.query_params.get("code")
    # state = request.query_params.get("state")
    if not code:
        logging.info("Authentication failed: No code provided.")
        raise HTTPException(status_code=400, detail="Code not provided")

    # Exchange code for token (OAuth 2.0 flow)
    try:
        token_response = await exchange_code_for_token(code)
    except Exception as e:
        logging.error(f"Token exchange failed: {e}")
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")

    access_token = token_response.get("access_token")
    if not access_token:
        logging.error("No access token returned from the token exchange")
        raise HTTPException(status_code=400, detail="No access token returned")

    # Get user info
    user_info = await get_twitter_user_info(access_token)
    # twitter_id = user_info["data"]["id"]
    twitter_username = user_info["data"]["username"]

    user = db.query(User).filter(User.twitter_username == twitter_username).first()

    if not user:
        user = User(twitter_username=twitter_username)
        db.add(user)
        db.commit()
        db.refresh(user)  # Refresh the user object to reflect committed changes

    access_token_expires = timedelta(seconds=settings.JWT_ACCESS_TOKEN_EXPIRE_SECONDS)
    token = create_access_token(data={"sub": str(user.twitter_username)}, expires_delta=access_token_expires)
    frontend_url = "http://localhost:5000/"
    # or for local dev:
    # frontend_url = "http://localhost:3000"

    redirect_url = f"{frontend_url}?token={token}"
    return RedirectResponse(url=redirect_url)

    # return {
    #     "access_token": token,
    #     "token_type": "bearer",
    #     "user_id": user.id,
    #     "twitter_username": user.twitter_username
    # }
