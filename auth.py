import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Cookie, HTTPException, Response, status

from config import SESSION_COOKIE_NAME
from database import get_db, utc_now

PBKDF2_ITERATIONS = 260_000
SESSION_DAYS = 14


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except ValueError:
        return False


def create_user(username: str, password: str) -> dict[str, Any]:
    username = username.strip()
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="用户名至少需要 3 个字符")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="密码至少需要 6 个字符")

    with get_db() as db:
        try:
            cursor = db.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, _hash_password(password), utc_now()),
            )
        except Exception as exc:
            if "UNIQUE" in str(exc).upper():
                raise HTTPException(status_code=409, detail="用户名已存在") from exc
            raise

        return {"id": cursor.lastrowid, "username": username}


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE username = ?", (username.strip(),)).fetchone()
    if not user or not _verify_password(password, user["password_hash"]):
        return None
    return {"id": user["id"], "username": user["username"]}


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    with get_db() as db:
        db.execute(
            "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, user_id, utc_now(), expires_at.isoformat()),
        )
    return token


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_DAYS * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME)


def delete_session(token: str | None) -> None:
    if not token:
        return
    with get_db() as db:
        db.execute("DELETE FROM sessions WHERE token = ?", (token,))


def get_current_user(
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> dict[str, Any]:
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")

    with get_db() as db:
        user = db.execute(
            """
            SELECT users.id, users.username
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ?
            """,
            (session_token,),
        ).fetchone()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效")
    return user
