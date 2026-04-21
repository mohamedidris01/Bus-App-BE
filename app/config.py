import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://busapp:busapp_secret@localhost/busapp_db"
    )
    secret_key: str = os.getenv("SECRET_KEY", "CHANGE_ME_TO_A_LONG_RANDOM_STRING")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

settings = Settings()