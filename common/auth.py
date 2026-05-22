import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
import redis
from fastapi import Request

from common.settings import (
    JWT_ALGORITHM,
    JWT_EXPIRES_DAYS,
    JWT_SECRET,
    PASSWORD_RESET_EXPIRES_MINUTES,
    REDIS_URL,
)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode(
        "utf-8"
    )


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def get_redis_client() -> redis.Redis | None:
    try:
        return redis.Redis.from_url(REDIS_URL, decode_responses=True)
    except redis.RedisError:
        return None


def create_access_token(user_id: str, username: str) -> str:
    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(days=JWT_EXPIRES_DAYS)
    payload = {
        "sub": user_id,
        "username": username,
        "jti": str(uuid.uuid4()),
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_password_reset_token(user_id: str) -> str:
    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(minutes=PASSWORD_RESET_EXPIRES_MINUTES)
    payload = {
        "sub": user_id,
        "scope": "password_reset",
        "jti": str(uuid.uuid4()),
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def get_token_from_request(request: Request) -> str | None:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    return header.replace("Bearer ", "", 1).strip() or None


def blacklist_token(token: str) -> None:
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        return

    expires_at = payload.get("exp")
    jti = payload.get("jti")
    if not expires_at or not jti:
        return

    ttl_seconds = max(expires_at - int(datetime.now(UTC).timestamp()), 0)
    client = get_redis_client()
    if client is None or ttl_seconds == 0:
        return

    try:
        client.setex(f"jwt_blacklist:{jti}", ttl_seconds, "1")
    except redis.RedisError:
        return


def is_blacklisted(jti: str | None) -> bool:
    if not jti:
        return False
    client = get_redis_client()
    if client is None:
        return False
    try:
        return bool(client.exists(f"jwt_blacklist:{jti}"))
    except redis.RedisError:
        return False


def get_current_user(request: Request, session):
    token = get_token_from_request(request)
    if not token:
        return None

    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        return None

    if is_blacklisted(payload.get("jti")):
        return None

    from irails.apps.users.models import User

    user_id = payload.get("sub")
    if not user_id:
        return None
    return session.get(User, uuid.UUID(user_id))