from dotenv import load_dotenv
import os
from pydantic_settings import BaseSettings
from pathlib import Path
from fastapi_mail import ConnectionConfig


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "templates"



load_dotenv(".env", override=True)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:faseeh123@localhost/recruiter_ai_db")
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

mail_config = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="Recruiter.AI",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER=TEMPLATE_DIR
)

TEMPLATE_DIR.mkdir(exist_ok=True)
