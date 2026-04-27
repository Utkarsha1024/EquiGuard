import os
from dotenv import load_dotenv

# Load .env at import time — does NOT override env vars already set
# (e.g. by the test harness or Docker). This guarantees CI tests
# can inject EQUIGUARD_API_KEY via os.environ before importing this module.
load_dotenv()

def get_settings():
    """
    Reads config from environment variables (populated by .env via dotenv).
    Calls load_dotenv(override=True) on each invocation so that changes to
    .env are picked up in long-running Docker containers without a rebuild,
    while still respecting any env vars already set in the process (CI wins
    because those are set before this module is imported).
    """
    # Re-read .env so Docker hot-reloads pick up changes (e.g. WEBHOOK_URL).
    # override=False here means env vars already in the process win, which is
    # what we want in CI where the test sets EQUIGUARD_API_KEY directly.
    load_dotenv(override=False)

    api_key = os.getenv("EQUIGUARD_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "EQUIGUARD_API_KEY is not set. "
            "Copy .env.example → .env and set a strong secret key."
        )
    return {
        "api_key":         api_key,
        "env":             os.getenv("ENV", "development"),
        "db_url":          os.getenv("DATABASE_URL", "sqlite:///equiguard.db"),
        "host":            os.getenv("HOST", "127.0.0.1"),
        "port":            int(os.getenv("PORT", 8000)),
        "gemini_api_key":  os.getenv("GEMINI_API_KEY", "").strip(),
        "webhook_url":     os.getenv("WEBHOOK_URL", "").strip(),
        "webhook_enabled": os.getenv("WEBHOOK_ENABLED", "false").lower() == "true",
    }
