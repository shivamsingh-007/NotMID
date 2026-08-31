"""FastAPI authentication dependencies."""
from fastapi import Depends, Header, HTTPException

from app.auth.token import TokenPayload, validate_token


async def get_current_user(authorization: str = Header(None)) -> TokenPayload:
    """Extract and validate token from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = authorization.replace("Bearer ", "")
    payload = validate_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


async def require_admin(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    """Require admin role."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


async def require_clinician(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    """Require clinical role (doctor, nurse)."""
    if user.role not in ("doctor", "nurse"):
        raise HTTPException(status_code=403, detail="Clinical role required")
    return user
