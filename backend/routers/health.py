from fastapi import APIRouter
from backend.config import get_settings

router = APIRouter(tags=["Health"])

@router.get("/")
def read_root():
    """Public health check — no auth required."""
    settings = get_settings()
    return {
        "status":  "Active",
        "env":     settings["env"],
        "message": "EquiGuard Firewall is running and ready for data.",
    }

@router.get("/health")
def health_check():
    """Lightweight liveness probe for Docker / load balancers."""
    return {"status": "ok"}
