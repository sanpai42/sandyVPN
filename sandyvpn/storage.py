"""Encrypted credential storage for SandyVPN."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

CRED_DIR = Path.home() / ".local" / "share" / "sandyvpn"
KEY_FILE = CRED_DIR / ".key"
CRED_FILE = CRED_DIR / "credentials.enc"


@dataclass
class Profile:
    config_name: str
    username: str


@dataclass
class Credentials:
    config_name: str
    username: str
    password: str


def _ensure_cred_dir() -> None:
    CRED_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(CRED_DIR, 0o700)


def _get_fernet() -> Fernet:
    _ensure_cred_dir()
    if KEY_FILE.exists():
        key = KEY_FILE.read_bytes()
    else:
        key = Fernet.generate_key()
        KEY_FILE.write_bytes(key)
        KEY_FILE.chmod(0o600)
    return Fernet(key)


def _read_payload() -> dict | None:
    if not CRED_FILE.exists():
        return None
    try:
        return json.loads(_get_fernet().decrypt(CRED_FILE.read_bytes()).decode())
    except (InvalidToken, json.JSONDecodeError, UnicodeDecodeError):
        return None


def save_credentials(creds: Credentials) -> None:
    payload = json.dumps(
        {
            "config_name": creds.config_name,
            "username": creds.username,
            "password": creds.password,
        }
    ).encode()
    _ensure_cred_dir()
    CRED_FILE.write_bytes(_get_fernet().encrypt(payload))
    CRED_FILE.chmod(0o600)


def load_profile() -> Profile | None:
    payload = _read_payload()
    if payload is None:
        return None
    config_name = payload.get("config_name", "")
    username = payload.get("username", "")
    if not config_name and not username:
        return None
    return Profile(config_name=config_name, username=username)


def credentials_exist() -> bool:
    payload = _read_payload()
    if payload is None:
        return False
    return bool(payload.get("config_name") or payload.get("username") or payload.get("password"))


def has_stored_password() -> bool:
    payload = _read_payload()
    return bool(payload and payload.get("password"))


def unlock_password() -> str | None:
    """Decrypt and return the stored password. Caller should discard after use."""
    payload = _read_payload()
    if payload is None:
        return None
    password = payload.get("password", "")
    return password or None


def clear_credentials() -> None:
    if CRED_FILE.exists():
        CRED_FILE.unlink()
