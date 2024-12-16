from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from dotenv import load_dotenv
import os

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
async def auth_callback(request: Request):
    # Handle callback and fetch user info
    try:
        token = await twitter.authorize_access_token(request)
        user_info = await twitter.get("account/verify_credentials.json", token=token)
        profile = user_info.json()
        return {
            "username": profile.get("screen_name"),
            "user_id": profile.get("id_str"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {e}")
