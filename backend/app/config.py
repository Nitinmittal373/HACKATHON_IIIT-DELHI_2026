"""Settings loaded from the .env file in the repo root (never hard-code keys)."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
BACKEND = Path(__file__).resolve().parents[1]
# override=True: the key in .env must win over any old key left in the terminal / Windows environment
load_dotenv(ROOT / ".env", override=True)

TINYFISH_API_KEY = os.getenv("TINYFISH_API_KEY", "").strip().strip('"').strip("'")
os.environ["TINYFISH_API_KEY"] = TINYFISH_API_KEY   # the SDK reads this variable
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
AGENT_CONCURRENCY = int(os.getenv("AGENT_CONCURRENCY", "2"))
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")          # where TinyFish can reach our webhook
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "").strip()                # shared secret on the webhook URL
FRONTEND_ORIGINS = [o.strip() for o in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "6"))     # new investigations per IP

CACHE_DIR = BACKEND / "cache"
CACHE_DIR.mkdir(exist_ok=True)
DATA_DIR = BACKEND / "data"
DATA_DIR.mkdir(exist_ok=True)
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "neevcheck.db"))
