import logging
from datetime import timedelta
import tweepy
from config import settings
from db import get_db
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from models.db import User
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
    print("Twitter redirect URL", settings.TWITTER_REDIRECT_URI)
    callback_uri = settings.TWITTER_REDIRECT_URI
    """Step 1: Redirect user to Twitter for authorization."""
    auth = tweepy.OAuth1UserHandler(
        settings.TWITTER_CONSUMER_KEY,
        settings.TWITTER_CONSUMER_SECRET,
        callback=callback_uri,
    )

    try:
        redirect_url = auth.get_authorization_url()
        logging.info(f"Redirecting user to Twitter: {redirect_url}")
        print("redirect_url", redirect_url)
        return {"authorization_url": redirect_url}
    except tweepy.TweepyException as e:
        logging.error(f"Error getting authorization URL: {e}")
        return {"error": "Failed to get Twitter authorization URL"}


@router.get("/twitter/callback")
async def twitter_callback(request: Request, db: Session = Depends(get_db)):
    """Step 2: Exchange OAuth verifier for user tokens."""
    oauth_token = request.query_params.get("oauth_token")
    oauth_verifier = request.query_params.get("oauth_verifier")

    if not oauth_token or not oauth_verifier:
        logging.error("Missing oauth_token or oauth_verifier")
        raise HTTPException(status_code=400, detail="Missing required OAuth parameters")

    auth = tweepy.OAuth1UserHandler(
        settings.TWITTER_CONSUMER_KEY,
        settings.TWITTER_CONSUMER_SECRET,
        settings.TWITTER_REDIRECT_URI,
    )

    auth.request_token = {"oauth_token": oauth_token, "oauth_token_secret": oauth_verifier}

    try:
        access_token, access_token_secret = auth.get_access_token(oauth_verifier)
    except tweepy.TweepyException as e:
        logging.error(f"Failed to exchange token: {e}")
        raise HTTPException(status_code=400, detail="Failed to exchange token")

    # Fetch user info using the access token
    user_client = tweepy.Client(
        consumer_key=settings.TWITTER_CONSUMER_KEY,
        consumer_secret=settings.TWITTER_CONSUMER_SECRET,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )

    try:
        user_info = user_client.get_me(user_fields=["id", "username"])
        twitter_id = user_info.data.id
        twitter_username = user_info.data.username
    except Exception as e:
        logging.error(f"Failed to fetch user info: {e}")
        raise HTTPException(status_code=400, detail="Failed to fetch Twitter user info")

    # Store user tokens in database
    user = db.query(User).filter(User.twitter_username == twitter_username).first()

    if not user:
        user = User(twitter_username=twitter_username, is_registered=True)
        db.add(user)
    else:
        user.is_registered = True

    user.twitter_access_token = access_token
    user.twitter_access_secret = access_token_secret  # ✅ Store access_token_secret

    db.commit()
    db.refresh(user)

    # Generate JWT token for frontend authentication
    access_token_expires = timedelta(seconds=settings.JWT_ACCESS_TOKEN_EXPIRE_SECONDS)
    token = create_access_token(data={"sub": str(user.twitter_username)}, expires_delta=access_token_expires)

    return RedirectResponse(url=f"/?token={token}")

