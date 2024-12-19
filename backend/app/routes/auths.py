from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from db import get_db
from config import Settings
from models.user import User
from utils.twitter_oauth import get_authorization_url, get_twitter_user_info, exchange_code_for_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/twitter/login")
def twitter_login():
    url = get_authorization_url()
    return {"authorization_url": url}


@router.get("/twitter/callback")
async def twitter_callback(request: Request, db: Session = Depends(get_db)):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    if not code:
        raise HTTPException(status_code=400, detail="Code not provided")

    # Exchange code for token (OAuth 2.0 flow)
    token_response = await exchange_code_for_token(code)
    print("Token response: ", token_response)
    access_token = token_response.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token returned")

    # Get user info
    user_info = await get_twitter_user_info(access_token)
    twitter_id = user_info["data"]["id"]
    twitter_username = user_info["data"]["username"]

    existing_user = db.query(User).filter(User.twitter_username == twitter_username).first()
    if not existing_user:
        new_user = User(twitter_username=twitter_username)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    return existing_user
