from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    ENVIRONMENT: str = "production"  # development or production
    GREETING: str = "Hello, default greeting!"
    LOCAL_DATABASE_URL: str = "sqlite:///./zap-zap.sqlite3"

    # Required settings (no default value)
    TWITTER_OAUTH2_CLIENT_ID: str
    TWITTER_OAUTH2_CLIENT_SECRET: str
    TWITTER_REDIRECT_URI: str
    TWITTER_ACCOUNT_BEARER_TOKEN: str
    TWITTER_ACCESS_TOKEN: str
    TWITTER_ACCESS_TOKEN_SECRET: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600

    BREEZ_API_KEY: str
    BREEZ_MNEMONIC: str
    BREEZ_WORKING_DIR: str
    BREEZ_GREENLIGHT_INVITE: str

    # only valid on production so "Optional"
    DB_INSTANCE_CONNECTION_NAME: Optional[str] = None
    DB_USER: Optional[str] = None
    DB_PASS: Optional[str] = None
    DB_NAME: Optional[str] = None

    GREENLIGHT_CLIENT_CERTIFICATE: str
    GREENLIGHT_CLIENT_PRIVATE_KEY: str

    # Application settings
    LEADERBOARD_CALCULATION_WINDOW_DAYS: int = 30  # a value in .env would override this
    TWITTER_AVATAR_CACHE_TTL_DAYS: int = 30

    FRONTEND_URL: str = "http://localhost:5000/"

    class Config:
        env_file = "backend/app/.env"


settings = Settings()
