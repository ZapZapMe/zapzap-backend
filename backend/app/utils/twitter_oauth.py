from urllib.parse import urlencode

import httpx
from config import settings

AUTHORIZE_URL = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
USERINFO_URL = "https://api.twitter.com/2/users/me"

SCOPES = ["tweet.read", "tweet.write", "users.read"]


def get_authorization_url():
    params = {
        "response_type": "code",
        "client_id": settings.TWITTER_OAUTH2_CLIENT_ID,
        "redirect_uri": settings.TWITTER_REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": "random_state_string",  # In production, generate a secure random state
        "code_challenge": "challenge",
        "code_challenge_method": "plain",
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code_for_token(code: str):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.TWITTER_REDIRECT_URI,
        "client_id": settings.TWITTER_OAUTH2_CLIENT_ID,
        "code_verifier": "challenge",
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(
            TOKEN_URL, data=data, auth=(settings.TWITTER_OAUTH2_CLIENT_ID, settings.TWITTER_OAUTH2_CLIENT_SECRET)
        )
        r.raise_for_status()
        return r.json()


async def get_twitter_user_info(access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"user.fields": "id,username"}
    async with httpx.AsyncClient() as client:
        r = await client.get(USERINFO_URL, headers=headers, params=params)
        r.raise_for_status()
        return r.json()
