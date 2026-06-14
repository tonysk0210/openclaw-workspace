#!/usr/bin/env python3
"""Send an email via Gmail SMTP (SSL).

Credentials are read from the macOS Keychain (never stored in plaintext here):
  security add-generic-password -a "$GMAIL_USER" -s "clawton-gmail-smtp" -w "<APP_PASSWORD>"

Usage:
  send_mail.py --to a@b.com --subject "Hi" --body-file body.txt [--attach file1 file2 ...]
  send_mail.py --to a@b.com --subject "Hi" --body "inline text" [--attach ...]

Sender Gmail account is configured below or via --from.
"""
import argparse
import mimetypes
import smtplib
import ssl
import subprocess
import sys
from email.message import EmailMessage
from pathlib import Path

DEFAULT_FROM = "anthonyshangkuan@gmail.com"
KEYCHAIN_SERVICE = "clawton-gmail-smtp"


def get_app_password(account: str) -> str:
    try:
        out = subprocess.run(
            ["security", "find-generic-password", "-a", account,
             "-s", KEYCHAIN_SERVICE, "-w"],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except subprocess.CalledProcessError:
        sys.exit(f"ERROR: no Keychain entry for account={account} service={KEYCHAIN_SERVICE}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="sender", default=DEFAULT_FROM)
    ap.add_argument("--to", required=True, action="append", help="repeatable")
    ap.add_argument("--subject", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--body")
    g.add_argument("--body-file")
    ap.add_argument("--attach", nargs="*", default=[])
    args = ap.parse_args()

    body = args.body if args.body is not None else Path(args.body_file).read_text(encoding="utf-8")

    msg = EmailMessage()
    msg["From"] = args.sender
    msg["To"] = ", ".join(args.to)
    msg["Subject"] = args.subject
    msg.set_content(body)

    for f in args.attach:
        p = Path(f)
        ctype, _ = mimetypes.guess_type(p.name)
        maintype, subtype = (ctype.split("/", 1) if ctype else ("application", "octet-stream"))
        msg.add_attachment(p.read_bytes(), maintype=maintype, subtype=subtype, filename=p.name)

    password = get_app_password(args.sender)
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as s:
        s.login(args.sender, password)
        s.send_message(msg)
    print(f"SENT ok -> {', '.join(args.to)}")


if __name__ == "__main__":
    main()
