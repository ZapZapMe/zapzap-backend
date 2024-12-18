import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    GREETING = os.getenv("GREETING", "Hello, default greeting!")

settings = Settings()
