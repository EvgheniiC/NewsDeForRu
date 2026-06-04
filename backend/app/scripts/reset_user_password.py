"""Set a new password for an existing app user (does not change role or editorial flags).

Usage::

    PYTHONPATH=. python -m app.scripts.reset_user_password --email user@example.com --password 'NEW'
"""

from __future__ import annotations

import argparse
import sys

from app.core.database import SessionLocal
from app.repositories.user_repository import UserRepository
from app.services.passwords import hash_password


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Reset password for an existing app user.")
    parser.add_argument("--email", required=True, help="Account email (normalized to lower case)")
    parser.add_argument("--password", required=True, help="New password")
    ns: argparse.Namespace = parser.parse_args(argv)

    norm_email: str = ns.email.strip().lower()
    pw_hash: str = hash_password(ns.password)

    db = SessionLocal()
    try:
        repo = UserRepository(db)
        user = repo.get_by_email(norm_email)
        if user is None:
            sys.stderr.write(f"No user found: {norm_email}\n")
            return 1
        repo.update_password(user, password_hash=pw_hash)
        sys.stdout.write(f"Password updated for user id={user.id} email={user.email}\n")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
