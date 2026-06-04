"""Create or upgrade an app user with editorial privileges (moderation / pipeline).

Usage::

    PYTHONPATH=. python -m app.scripts.create_staff_user --email ops@example.com --password ...

Grant privileges to an existing reader account (password unchanged)::

    PYTHONPATH=. python -m app.scripts.create_staff_user --email reader@example.com --grant-only
"""

from __future__ import annotations

import argparse
import sys

from app.core.database import SessionLocal
from app.repositories.user_repository import UserRepository
from app.services.passwords import hash_password


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Create or promote an app user with editorial rights.")
    parser.add_argument("--email", required=True, help="Unique login email (normalized to lower case)")
    parser.add_argument("--password", help="Password (required unless --grant-only)")
    parser.add_argument(
        "--grant-only",
        action="store_true",
        help="Only set can_moderate / can_run_pipeline on an existing account",
    )
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
    norm_email: str = ns.email.strip().lower()

    if not ns.grant_only and (ns.password is None or ns.password == ""):
        sys.stderr.write("--password is required unless --grant-only\n")
        return 1

    db = SessionLocal()
    try:
        repo = UserRepository(db)
        existing = repo.get_by_email(norm_email)
        if existing is None:
            if ns.grant_only:
                sys.stderr.write(f"No user found: {norm_email}\n")
                return 1
            pw_hash: str = hash_password(ns.password)
            user = repo.create_staff_user(
                email=norm_email,
                password_hash=pw_hash,
                can_moderate=can_moderate,
                can_run_pipeline=can_run_pipeline,
            )
            sys.stdout.write(
                f"Created editorial user id={user.id} email={user.email} "
                f"can_moderate={user.can_moderate} can_run_pipeline={user.can_run_pipeline}\n"
            )
            return 0

        if ns.grant_only:
            user = repo.grant_staff_privileges(
                existing,
                can_moderate=can_moderate,
                can_run_pipeline=can_run_pipeline,
            )
        else:
            existing.password_hash = hash_password(ns.password)
            user = repo.grant_staff_privileges(
                existing,
                can_moderate=can_moderate,
                can_run_pipeline=can_run_pipeline,
            )
        sys.stdout.write(
            f"Updated user id={user.id} email={user.email} "
            f"can_moderate={user.can_moderate} can_run_pipeline={user.can_run_pipeline}\n"
        )
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
