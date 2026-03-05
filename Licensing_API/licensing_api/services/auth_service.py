import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import psycopg2

from licensing_api.core.auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    hash_api_key,
    hash_api_secret,
    verify_password,
    verify_refresh_token,
    generate_api_key,
    get_key_prefix,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)


class AuthError(Exception):
    pass


class UserNotFoundError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


class UserAlreadyExistsError(AuthError):
    pass


class InvalidTokenError(AuthError):
    pass


class TokenExpiredError(AuthError):
    pass


class APIKeyNotFoundError(AuthError):
    pass


class APIKeyError(AuthError):
    pass


def _get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        database=os.getenv("DB_NAME", "licenses_db"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "@@MOHAMMED12@@")
    )


def register_user(email: str, password: str, role: str = "user") -> Dict[str, Any]:
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                raise UserAlreadyExistsError("User with this email already exists")

            password_hash = hash_password(password)
            cur.execute(
                """
                INSERT INTO users (email, password_hash, role, is_active)
                VALUES (%s, %s, %s, %s)
                RETURNING user_id, email, role, is_active, created_at
                """,
                (email, password_hash, role, True)
            )
            row = cur.fetchone()
            conn.commit()

            user_id, email, role, is_active, created_at = row
            return {
                "user_id": user_id,
                "email": email,
                "role": role,
                "is_active": is_active,
                "created_at": created_at,
            }


def login(email: str, password: str) -> Dict[str, Any]:
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, email, password_hash, role, is_active FROM users WHERE email = %s",
                (email,)
            )
            row = cur.fetchone()

            if not row:
                raise InvalidCredentialsError("Invalid email or password")

            user_id, email, password_hash, role, is_active = row

            if not is_active:
                raise InvalidCredentialsError("Account is inactive")

            if not verify_password(password, password_hash):
                raise InvalidCredentialsError("Invalid email or password")

            access_token = create_access_token({"sub": str(user_id), "email": email, "role": role})
            refresh_token = create_refresh_token({"sub": str(user_id), "email": email})

            token_hash = hash_token(refresh_token)
            expires_at = datetime.utcnow() + timedelta(days=7)

            cur.execute(
                "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES (%s, %s, %s)",
                (user_id, token_hash, expires_at)
            )
            conn.commit()

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            }


def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    payload = verify_refresh_token(refresh_token)
    if not payload:
        raise InvalidTokenError("Invalid refresh token")

    user_id = int(payload.get("sub"))
    email = payload.get("email")
    role = payload.get("role")

    token_hash = hash_token(refresh_token)

    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT token_id FROM refresh_tokens WHERE user_id = %s AND token_hash = %s AND expires_at > %s",
                (user_id, token_hash, datetime.utcnow())
            )
            if not cur.fetchone():
                raise InvalidTokenError("Refresh token not found or expired")

            cur.execute(
                "DELETE FROM refresh_tokens WHERE user_id = %s AND token_hash = %s",
                (user_id, token_hash)
            )

            access_token = create_access_token({"sub": str(user_id), "email": email, "role": role})
            new_refresh_token = create_refresh_token({"sub": str(user_id), "email": email})

            new_token_hash = hash_token(new_refresh_token)
            expires_at = datetime.utcnow() + timedelta(days=7)

            cur.execute(
                "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES (%s, %s, %s)",
                (user_id, new_token_hash, expires_at)
            )
            conn.commit()

            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            }


def logout(user_id: int, refresh_token: str) -> None:
    token_hash = hash_token(refresh_token)
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM refresh_tokens WHERE user_id = %s AND token_hash = %s",
                (user_id, token_hash)
            )
            conn.commit()


def revoke_all_user_tokens(user_id: int) -> None:
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM refresh_tokens WHERE user_id = %s", (user_id,))
            conn.commit()


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, email, role, is_active, created_at FROM users WHERE user_id = %s",
                (user_id,)
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "user_id": row[0],
                "email": row[1],
                "role": row[2],
                "is_active": row[3],
                "created_at": row[4],
            }


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, email, role, is_active, created_at FROM users WHERE email = %s",
                (email,)
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "user_id": row[0],
                "email": row[1],
                "role": row[2],
                "is_active": row[3],
                "created_at": row[4],
            }


def update_user(user_id: int, email: Optional[str] = None, role: Optional[str] = None, is_active: Optional[bool] = None) -> Dict[str, Any]:
    with _get_connection() as conn:
        with conn.cursor() as cur:
            updates = []
            values = []

            if email:
                updates.append("email = %s")
                values.append(email)
            if role:
                updates.append("role = %s")
                values.append(role)
            if is_active is not None:
                updates.append("is_active = %s")
                values.append(is_active)

            updates.append("updated_at = %s")
            values.append(datetime.utcnow())
            values.append(user_id)

            query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s RETURNING user_id, email, role, is_active, created_at"
            cur.execute(query, values)
            row = cur.fetchone()
            conn.commit()

            if not row:
                raise UserNotFoundError("User not found")

            return {
                "user_id": row[0],
                "email": row[1],
                "role": row[2],
                "is_active": row[3],
                "created_at": row[4],
            }


def list_users(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, email, role, is_active, created_at FROM users ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (limit, offset)
            )
            rows = cur.fetchall()
            return [
                {
                    "user_id": row[0],
                    "email": row[1],
                    "role": row[2],
                    "is_active": row[3],
                    "created_at": row[4],
                }
                for row in rows
            ]


def create_api_key(user_id: int, name: str, expires_at: Optional[datetime] = None) -> Dict[str, Any]:
    api_key, secret = generate_api_key()
    key_hash = hash_api_key(api_key)
    secret_hash = hash_api_secret(secret)

    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO api_keys (user_id, key_hash, secret_hash, name, expires_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING key_id, user_id, name, is_active, created_at, expires_at
                """,
                (user_id, key_hash, secret_hash, name, expires_at)
            )
            row = cur.fetchone()
            conn.commit()

            return {
                "key_id": row[0],
                "user_id": row[1],
                "api_key": api_key,
                "secret": secret,
                "name": row[2],
                "is_active": row[3],
                "created_at": row[4],
                "expires_at": row[5],
            }


def list_api_keys(user_id: int) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT key_id, user_id, key_hash, name, is_active, created_at, expires_at FROM api_keys WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,)
            )
            rows = cur.fetchall()
            result = []
            for row in rows:
                key_id, user_id, key_hash, name, is_active, created_at, expires_at = row
                result.append({
                    "key_id": key_id,
                    "user_id": user_id,
                    "key_prefix": get_key_prefix(key_hash),
                    "name": name,
                    "is_active": is_active,
                    "created_at": created_at,
                    "expires_at": expires_at,
                })
            return result


def get_api_key(key_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT key_id, user_id, key_hash, secret_hash, name, is_active, created_at, expires_at FROM api_keys WHERE key_id = %s AND user_id = %s",
                (key_id, user_id)
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "key_id": row[0],
                "user_id": row[1],
                "key_hash": row[2],
                "secret_hash": row[3],
                "name": row[4],
                "is_active": row[5],
                "created_at": row[6],
                "expires_at": row[7],
            }


def verify_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    key_hash = hash_api_key(api_key)
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT key_id, user_id, secret_hash, name, is_active, expires_at 
                FROM api_keys 
                WHERE key_hash = %s AND is_active = TRUE
                """,
                (key_hash,)
            )
            row = cur.fetchone()
            if not row:
                return None

            key_id, user_id, secret_hash, name, is_active, expires_at = row

            if expires_at and expires_at < datetime.utcnow():
                return None

            return {
                "key_id": key_id,
                "user_id": user_id,
                "secret_hash": secret_hash,
                "name": name,
            }


def delete_api_key(key_id: int, user_id: int) -> bool:
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM api_keys WHERE key_id = %s AND user_id = %s RETURNING key_id",
                (key_id, user_id)
            )
            result = cur.fetchone()
            conn.commit()
            return result is not None
