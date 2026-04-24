import os
from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from backend.config import get_settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def require_api_key(api_key_header: str = Security(API_KEY_HEADER)):
    """
    Dependency injected into every protected endpoint.
    Reads the expected key from settings — never hardcoded.
    Returns 403 if the header is missing or wrong.
    """
    settings = get_settings()
    if not api_key_header or api_key_header != settings["api_key"]:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key. Pass your key in the X-API-Key header.",
        )
    return api_key_header
