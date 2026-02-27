"""Auth endpoints - placeholder for JWT/API key validation."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import APIKeyHeader, HTTPBearer

router = APIRouter()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer = HTTPBearer(auto_error=False)


async def get_current_user_id(
    api_key: str | None = Depends(api_key_header),
    _credentials=Depends(bearer),
) -> str:
    """Validate API key or Bearer token; return user_id. Placeholder."""
    if api_key:
        # TODO: Look up api_keys table, return user_id
        return "placeholder-user-id"
    if _credentials:
        # TODO: Validate JWT, return user_id
        return "placeholder-user-id"
    raise HTTPException(status_code=401, detail="API key or Bearer token required")
