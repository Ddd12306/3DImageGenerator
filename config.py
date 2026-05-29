import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://www.right.codes/draw/v1")
MODEL = os.getenv("MODEL", "gpt-image-2")

TENCENT_SECRET_ID = os.getenv("TENCENT_SECRET_ID", "")
TENCENT_SECRET_KEY = os.getenv("TENCENT_SECRET_KEY", "")
TENCENT_REGION = os.getenv("TENCENT_REGION", "ap-guangzhou")
