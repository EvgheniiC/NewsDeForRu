"""Send a test message through configured SMTP (diagnostics for production).

Usage::

    cd backend
    source .venv/bin/activate
    PYTHONPATH=. python -m app.scripts.test_smtp --to your@email.com
"""

from __future__ import annotations

import argparse
import sys

from app.services.email_delivery import log_smtp_startup_status, smtp_config_status, try_send_transactional_email


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Send a test email via SMTP settings from .env")
    parser.add_argument("--to", required=True, help="Recipient email address")
    args: argparse.Namespace = parser.parse_args(argv)

    status = smtp_config_status()
    print(f"SMTP_HOST set: {status.host_set}")
    print(f"SMTP_FROM_EMAIL set: {status.from_set}")
    print(f"SMTP_USER set: {status.user_set}")
    print(f"SMTP_PASSWORD set: {status.password_set}")
    print(f"Ready to send: {status.ready}")
    if not status.ready:
        print(f"Missing: {status.missing_reason}", file=sys.stderr)
        return 1

    log_smtp_startup_status()
    ok: bool = try_send_transactional_email(
        to_address=str(args.to).strip(),
        subject="newsForGermanyRU SMTP test",
        body_text=(
            "This is a test message from newsForGermanyRU backend.\n"
            "If you received it, SMTP is configured correctly.\n"
        ),
        log_context="test_smtp_script",
    )
    if ok:
        print(f"Test email sent to {args.to}")
        return 0
    print("Send failed — check API logs above or journalctl -u news-api", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
