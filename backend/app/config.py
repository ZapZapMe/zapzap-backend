from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    ENVIRONMENT: str = "production"  # development or production
    GREETING: str = "Hello, default greeting!"
    LOCAL_DATABASE_URL: str = "sqlite:///./zap-zap.sqlite3"

    # Required settings (no default value)
    TWITTER_CONSUMER_KEY: str
    TWITTER_CONSUMER_SECRET: str
    TWITTER_OAUTH2_CLIENT_ID: str
    TWITTER_OAUTH2_CLIENT_SECRET: str
    TWITTER_REDIRECT_URI: str
    TWITTER_ACCOUNT_BEARER_TOKEN: str
    
    # used if we are posting as this the project account holder (not as the logged in user)
    TWITTER_ACCESS_TOKEN: Optional[str] = None
    TWITTER_ACCESS_TOKEN_SECRET: Optional[str] = None

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_SECONDS: int = 2592000

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
    LEADERBOARD_CALCULATION_WINDOW_DAYS: int = 7  # a value in .env would override this
    TWITTER_AVATAR_CACHE_TTL_DAYS: int = 30
    BREEZ_LOGLEVEL: str = "INFO"
    FRONTEND_URL: str

    class Config:
        env_file = "backend/app/.env"


settings = Settings()
