import os
import time
from typing import Dict, List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer

from licensing_api.core.auth import verify_access_token
from licensing_api.services import auth_service


API_KEY_NAME = "X-API-Key"
API_KEY_HEADER = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl="/auth/login")

ALLOWED_IPS: List[str] = []
if os.getenv("ALLOWED_IPS"):
    ALLOWED_IPS = [ip.strip() for ip in os.getenv("ALLOWED_IPS", "").split(",") if ip.strip()]


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._storage: Dict[str, list[float]] = {}

    def hit(self, key: str) -> None:
        now = time.time()
        window_start = now - self.window_seconds
        timestamps = self._storage.get(key, [])
        timestamps = [ts for ts in timestamps if ts >= window_start]

        if len(timestamps) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many validation requests. Please slow down.",
            )

        timestamps.append(now)
        self._storage[key] = timestamps


_validate_rate_limiter = RateLimiter(max_requests=30, window_seconds=60)


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_ip_whitelist(request: Request) -> None:
    if not ALLOWED_IPS:
        return
    
    client_ip = get_client_ip(request)
    if client_ip not in ALLOWED_IPS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="IP address not allowed",
        )


def get_admin_api_key(api_key: Optional[str] = Depends(API_KEY_HEADER)) -> None:
    expected_key = os.getenv("ADMIN_API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfigured: ADMIN_API_KEY not set.",
        )

    if not api_key or api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "API-Key"},
        )


def rate_limiter_validate_license(request: Request) -> None:
    client_host = get_client_ip(request)
    _validate_rate_limiter.hit(client_host)


def get_current_user(token: str = Depends(OAUTH2_SCHEME)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_access_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    return payload


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_role(allowed_roles: List[str]):
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return role_checker


def get_optional_user(token: Optional[str] = Depends(OAUTH2_SCHEME)) -> Optional[dict]:
    if not token:
        return None
    
    try:
        return verify_access_token(token)
    except Exception:
        return None
