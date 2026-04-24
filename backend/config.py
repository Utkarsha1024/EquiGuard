import os
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

@lru_cache()
def get_settings():
    """
    Reads config from environment variables (populated by .env via dotenv).
    Using lru_cache so it's only read once — not on every request.
    """
    api_key = os.getenv("EQUIGUARD_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "EQUIGUARD_API_KEY is not set. "
            "Copy .env.example → .env and set a strong secret key."
        )
    return {
        "api_key":    api_key,
        "env":        os.getenv("ENV", "development"),
        "db_url":     os.getenv("DATABASE_URL", "sqlite:///equiguard.db"),
        "host":       os.getenv("HOST", "127.0.0.1"),
        "port":       int(os.getenv("PORT", 8000)),
        "gcp_project_id": os.getenv("GCP_PROJECT_ID", "").strip(),
        "gcp_location":   os.getenv("GCP_LOCATION", "us-central1").strip(),
        "gemini_api_key": os.getenv("GEMINI_API_KEY", "").strip(),
        "webhook_url":     os.getenv("WEBHOOK_URL", "").strip(),
        "webhook_enabled": os.getenv("WEBHOOK_ENABLED", "false").lower() == "true",
    }
