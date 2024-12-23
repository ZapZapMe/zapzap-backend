from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from sqlalchemy.orm import Session
from db import get_db
import os
from models.user import User
from utils.security import create_access_token
import logging
from datetime import timedelta

# OAuth configuration
oauth = OAuth()
twitter = oauth.register(
    name="twitter",
    client_id=os.getenv("TWITTER_API_KEY"),
    client_secret=os.getenv("TWITTER_API_SECRET"),
    request_token_url="https://api.twitter.com/oauth/request_token",
    authorize_url="https://api.twitter.com/oauth/authenticate",
    access_token_url="https://api.twitter.com/oauth/access_token",
    client_kwargs={"token_placement": "header"},
)


@app.get("/")
async def home():
    return {"message": "Welcome to the Twitter OAuth Demo!"}


@app.get("/auth/login")
async def login(request: Request):
    # Redirect user to Twitter for authorization
    redirect_uri = os.getenv("TWITTER_CALLBACK_URL")
    return await twitter.authorize_redirect(request, redirect_uri)


@app.get("/auth/callback")
async def auth_callback(request: Request, db : Session = Depends(get_db)):
    # Handle callback and fetch user info
    try:
        token = await twitter.authorize_access_token(request)
        user_info = await twitter.get("account/verify_credentials.json", token=token)
        profile = user_info.json()
        twitter_username  = profile.get("screen")
        # twitter_user_id = profile.get("id_str")
        if not twitter_username or twitter_user_id:
            raise HTTPException(status_code=400, detail="Failed to retrieve twitter username or ID")

        user = db.query(User).filter(User.twitter_username == twitter_username).first()
        if not user:
            user = User(
                twitter_username = twitter_username,
                # twitter_user_id = twitter_user_id
            )
            db.add(user)
            db.commit()
            db.refresh()
            logging.info(f"Created new user: @{twitter_username}")
        else:
            logging.info(f"Retrieved existing user: @{twitter_username}")

        access_token_expires = timedelta(seconds=)

    
        
        # return {
        #     "username": profile.get("screen_name"),
        #     "user_id": profile.get("id_str"),
        # }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {e}")
