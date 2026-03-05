import os
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
PBKDF2_ITERATIONS = 100000

SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY", secrets.token_hex(32))


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), PBKDF2_ITERATIONS).hex()
    return f"$pbkdf2-sha256${salt}${password_hash}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if not hashed_password.startswith("$pbkdf2-sha256$"):
            return False
        parts = hashed_password.split("$")
        salt = parts[2]
        stored_hash = parts[3]
        computed_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode(), salt.encode(), PBKDF2_ITERATIONS).hex()
        return hmac.compare_digest(computed_hash, stored_hash)
    except Exception:
        return False


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def verify_refresh_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_api_key() -> tuple[str, str]:
    api_key = f"sk_{secrets.token_urlsafe(32)}"
    secret = secrets.token_urlsafe(32)
    return api_key, secret


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def hash_api_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def verify_api_key_signature(
    api_key: str,
    secret: str,
    timestamp: str,
    method: str,
    path: str,
    body: str = ""
) -> bool:
    secret_hash = hash_api_secret(secret)
    message = f"{timestamp}{method}{path}{body}"
    expected_signature = hmac.new(
        secret_hash.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return True


def get_key_prefix(api_key: str) -> str:
    return api_key[:12] + "..."
