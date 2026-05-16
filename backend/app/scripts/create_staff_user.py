"""Create a staff operator account (moderation / manual pipeline).

Usage::

    PYTHONPATH=backend uvicorn ...
    PYTHONPATH=. python -m app.scripts.create_staff_user --email ops@example.com --password ...

From the ``backend`` directory with PYTHONPATH=. or install the package editable.
"""

from __future__ import annotations

import argparse
import sys

from app.core.database import SessionLocal
from app.repositories.staff_repository import StaffRepository
from app.services.passwords import hash_password


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Create a staff operator user.")
    parser.add_argument("--email", required=True, help="Unique login email (normalized to lower case)")
    parser.add_argument("--password", required=True, help="Initial password")
    parser.add_argument(
        "--no-moderate",
        action="store_true",
        help="Disable moderation permissions for this user",
    )
    parser.add_argument(
        "--no-pipeline",
        action="store_true",
        help="Disable manual pipeline runs for this user",
    )
    ns: argparse.Namespace = parser.parse_args(argv)

    can_moderate: bool = not ns.no_moderate
    can_run_pipeline: bool = not ns.no_pipeline
    pw_hash: str = hash_password(ns.password)

    db = SessionLocal()
    try:
        repo = StaffRepository(db)
        norm_email: str = ns.email.strip().lower()
        if repo.get_by_email(norm_email) is not None:
            sys.stderr.write(f"User already exists: {norm_email}\n")
            return 1
        user = repo.create_staff_user(
            email=norm_email,
            password_hash=pw_hash,
            can_moderate=can_moderate,
            can_run_pipeline=can_run_pipeline,
        )
        sys.stdout.write(f"Created staff user id={user.id} email={user.email}\n")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
