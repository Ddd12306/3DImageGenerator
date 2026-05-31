import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://www.right.codes/draw/v1")
MODEL = os.getenv("MODEL", "gpt-image-2")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "outputs"
DB_PATH = Path(os.getenv("DB_PATH", DATA_DIR / "app.db"))

SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "image_platform_session")
