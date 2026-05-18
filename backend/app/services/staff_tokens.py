"""Access JWT and opaque refresh tokens for staff APIs."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException


def normalize_refresh_plain(raw: str) -> bytes:
    return raw.strip().encode("utf-8")


def refresh_token_hash_hex(raw_plain: str) -> str:
    return hashlib.sha256(normalize_refresh_plain(raw_plain)).hexdigest()


def new_refresh_plain() -> str:
    """URL-safe opaque token stored only as SHA-256 hex in DB."""
    return secrets.token_urlsafe(48)


def issue_access_token(
    *,
    user_id: int,
    secret: str,
    algorithm: str,
    expires_delta: timedelta,
    audience: str,
) -> tuple[str, datetime]:
    now: datetime = datetime.now(tz=UTC)
    exp: datetime = now + expires_delta
    payload: dict[str, object] = {
        "sub": str(user_id),
        "typ": "access",
        "aud": audience,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    token: str = jwt.encode(payload, secret, algorithm=algorithm)
    return token, exp


def decode_access_token(
    token: str,
    *,
    secret: str,
    algorithm: str,
    expected_audience: str,
) -> int:
    def aud_to_str(raw: object, default: str) -> str:
        if raw is None:
            return default
        if isinstance(raw, str):
            return raw
        if isinstance(raw, list) and len(raw) == 1 and isinstance(raw[0], str):
            return raw[0]
        raise LookupError("invalid aud")

    try:
        payload: dict[str, object] = jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
            options={"require": ["exp", "sub"], "verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
    if payload.get("typ") != "access":
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    try:
        aud_norm: str = aud_to_str(payload.get("aud"), "staff")
    except LookupError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if aud_norm != expected_audience:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    sub_raw: object = payload.get("sub")
    if isinstance(sub_raw, int):
        return sub_raw
    if isinstance(sub_raw, str) and sub_raw.isdigit():
        return int(sub_raw)
    raise HTTPException(status_code=401, detail="Invalid or expired token")
