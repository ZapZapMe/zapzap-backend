import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    ENVIRONMENT = os.getenv("ENVIRONMENT")  # development or production
    GREETING = os.getenv("GREETING", "Hello, default greeting!")

    LOCAL_DATABASE_URL = os.getenv("LOCAL_DATABASE_URL", "sqlite:///./test.db")

    # postgres_database
    db_user = os.environ["DB_USER"]
    db_pass = os.environ["DB_PASS"]
    db_name = os.environ["DB_NAME"]
    db_port = os.environ["DB_PORT"]
    db_host = os.environ["DB_HOST"]

    POSTGRES_DATABASE_URL = (
        f"postgresql+pg8000://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    )
    if os.getenv("ENVIRONMENT") == "development":
        DATABASE_URL = os.getenv("LOCAL_DATABASE_URL")
    else:
        DATABASE_URL = POSTGRES_DATABASE_URL

    TWITTER_CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
    TWITTER_CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")
    TWITTER_REDIRECT_URI = os.getenv("TWITTER_REDIRECT_URI")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_SECONDS", 3600))

    BREEZ_API_KEY = os.getenv("BREEZ_API_KEY")
    BREEZ_INVITE_CODE = os.getenv("BREEZ_INVITE_CODE", "")
    BREEZ_WORKING_DIR = os.getenv("BREEZ_WORKING_DIR", "./breez_data")
    BREEZ_MNEMONIC = os.getenv("BREEZ_MNEMONIC")


settings = Settings()
