import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    ENVIRONMENT = os.getenv("ENVIRONMENT")  # development or production
    GREETING = os.getenv("GREETING", "Hello, default greeting!")

    # necessary for development
    LOCAL_DATABASE_URL = os.getenv("LOCAL_DATABASE_URL", "sqlite:///./zap-zap.sqlite3")

    # necessary for production
    DB_INSTANCE_CONNECTION_NAME = os.getenv("DB_INSTANCE_CONNECTION_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS")
    DB_NAME = os.getenv("DB_NAME")

    TWITTER_CLIENT_ID = os.environ.get("TWITTER_CLIENT_ID")
    TWITTER_CLIENT_SECRET = os.environ.get("TWITTER_CLIENT_SECRET")
    TWITTER_REDIRECT_URI = os.environ.get("TWITTER_REDIRECT_URI")
    TWITTER_ACCOUNT_BEARER_TOKEN = os.environ.get("TWITTER_ACCOUNT_BEARER_TOKEN")
    TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN")
    TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_SECONDS = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_SECONDS", 3600))

    BREEZ_API_KEY = os.environ.get("BREEZ_API_KEY")
    BREEZ_MNEMONIC = os.environ.get("BREEZ_MNEMONIC")
    BREEZ_WORKING_DIR = os.environ.get("BREEZ_WORKING_DIR", "./")
    BREEZ_GREENLIGHT_INVITE = os.environ.get("BREEZ_GREENLIGHT_INVITE")


settings = Settings()
