import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Webhook configuration for Coach channel
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_COACH_WEBHOOK_URL")

# Your profile URL or username
PROFILE_URL = os.getenv("PROFILE_URL")

# Free Google Gemini API Key for AI Coach
GEMINI_API_KEY = os.getenv("GEMINI_COACH_API_KEY")

# Number of recent videos to analyze for daily audit
VIDEOS_TO_AUDIT = int(os.getenv("VIDEOS_TO_AUDIT", "5"))

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
HISTORY_FILE = DATA_DIR / "history.json"
MAX_HISTORY_ENTRIES = 1000
