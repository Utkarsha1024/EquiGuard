import os
import sys

# Add the project root to sys.path to resolve 'audit_engine' and 'database' imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set GCP credentials from env var if not already set.
# Configure GOOGLE_APPLICATION_CREDENTIALS in your .env file.
_gcp_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
if _gcp_creds:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _gcp_creds

from fastapi import FastAPI
from backend.config import get_settings
from backend.routers import health, audit, google_ai

app = FastAPI(
    title="EquiGuard API",
    version="1.0",
    description="AI Bias Firewall — EEOC Compliance Audit Engine",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(health.router)
app.include_router(audit.router)
app.include_router(google_ai.router)

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings["host"],
        port=settings["port"],
        reload=(settings["env"] == "development"),
    )