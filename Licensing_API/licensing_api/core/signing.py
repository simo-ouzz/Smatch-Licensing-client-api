import hashlib
import hmac
import time
from typing import Optional

from fastapi import Depends, HTTPException, Request, status

from licensing_api.core.security import API_KEY_HEADER
from licensing_api.services import auth_service


SIGNATURE_HEADER = "X-Signature"
TIMESTAMP_HEADER = "X-Timestamp"
MAX_TIMESTAMP_DIFF = 300


def get_request_body_hash(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def verify_request_signature(
    api_key: Optional[str] = Depends(API_KEY_HEADER),
    signature: Optional[str] = Depends(lambda request: request.headers.get(SIGNATURE_HEADER)),
    timestamp: Optional[str] = Depends(lambda request: request.headers.get(TIMESTAMP_HEADER)),
) -> dict:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "API-Key"},
        )

    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing signature",
        )

    if not timestamp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing timestamp",
        )

    try:
        request_time = int(timestamp)
        if abs(time.time() - request_time) > MAX_TIMESTAMP_DIFF:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Request timestamp expired",
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid timestamp format",
        )

    key_data = auth_service.verify_api_key(api_key)
    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "API-Key"},
        )

    secret_hash = key_data["secret_hash"]
    
    return {
        "user_id": key_data["user_id"],
        "key_id": key_data["key_id"],
        "key_name": key_data.get("name"),
    }


def create_request_signature(
    api_secret: str,
    method: str,
    path: str,
    body: str = "",
    timestamp: Optional[int] = None,
) -> tuple[str, int]:
    if timestamp is None:
        timestamp = int(time.time())
    
    body_hash = get_request_body_hash(body.encode()) if body else ""
    message = f"{timestamp}{method}{path}{body_hash}"
    
    signature = hmac.new(
        api_secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return signature, timestamp


def verify_request_signature_sync(
    api_secret: str,
    method: str,
    path: str,
    body: str,
    signature: str,
    timestamp: str,
) -> bool:
    try:
        request_time = int(timestamp)
        if abs(time.time() - request_time) > MAX_TIMESTAMP_DIFF:
            return False
    except ValueError:
        return False

    expected_signature, _ = create_request_signature(
        api_secret=api_secret,
        method=method,
        path=path,
        body=body,
        timestamp=request_time,
    )

    return hmac.compare_digest(signature, expected_signature)
