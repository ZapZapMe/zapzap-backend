import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    GREETING = os.getenv("GREETING", "Hello, default greeting!")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    TWITTER_CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
    TWITTER_CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")
    TWITTER_REDIRECT_URI = os.getenv("TWITTER_REDIRECT_URI")

settings = Settings()

# https://developer.x.com/en/docs/authentication/guides/v2-authentication-mapping