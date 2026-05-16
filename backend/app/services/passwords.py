"""Password hashing for staff operators (bcrypt)."""

from __future__ import annotations

import bcrypt


def hash_password(password: str) -> str:
    truncated: bytes = password.encode("utf-8")[:72]
    salt: bytes = bcrypt.gensalt()
    hashed: bytes = bcrypt.hashpw(truncated, salt)
    return hashed.decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    truncated: bytes = password.encode("utf-8")[:72]
    try:
        digest: bytes = password_hash.encode("ascii")
        return bcrypt.checkpw(truncated, digest)
    except (ValueError, OSError):
        return False
