import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    ENVIRONMENT = os.getenv("ENVIRONMENT")  # development or production
    GREETING = os.getenv("GREETING", "Hello, default greeting!")

    LOCAL_DATABASE_URL = os.getenv("LOCAL_DATABASE_URL", "sqlite:///./test.db")

    # postgres_database
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_name = os.getenv("DB_NAME")

    TWITTER_CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
    TWITTER_CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")
    TWITTER_REDIRECT_URI = os.getenv("TWITTER_REDIRECT_URI")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_SECONDS", 3600))

    BREEZ_API_KEY = os.getenv("BREEZ_API_KEY")
    BREEZ_MNEMONIC = os.getenv("BREEZ_MNEMONIC")
    BREEZ_DATA_PATH = os.getenv("BREEZ_DATA_PATH", "./")
    BREEZ_GREENLIGHT_INVITE = os.getenv("BREEZ_GREENLIGHT_INVITE")


settings = Settings()
