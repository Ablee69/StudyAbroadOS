from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_SECRETS_PATH = BASE_DIR / ".streamlit" / "secrets.toml"


@dataclass(frozen=True)
class AppConfig:
    supabase_url: str
    supabase_key: str
    database_url: str

    @property
    def has_supabase_client_config(self) -> bool:
        return _looks_real(self.supabase_url) and _looks_real(self.supabase_key)

    @property
    def has_database_url(self) -> bool:
        return _looks_real(self.database_url)


def _read_secret(name: str) -> str:
    candidates: list[str] = []
    env_value = os.getenv(name, "").strip()
    if env_value:
        candidates.append(env_value)
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    if value:
        candidates.append(str(value).strip())
    local_value = _read_local_secret(name)
    if local_value:
        candidates.append(local_value)

    for candidate in candidates:
        if _looks_real(candidate):
            return candidate
    return candidates[0] if candidates else ""


def _read_local_secret(name: str) -> str:
    if not LOCAL_SECRETS_PATH.exists():
        return ""
    try:
        with LOCAL_SECRETS_PATH.open("rb") as file:
            data = tomllib.load(file)
    except Exception:
        return ""
    value = data.get(name, "")
    return str(value).strip() if value else ""


def _looks_real(value: str) -> bool:
    if not value:
        return False
    placeholders = {
        "your-project-ref",
        "your-supabase-anon-key",
        "your-password",
    }
    return not any(token in value for token in placeholders)


def save_local_secrets(supabase_url: str, supabase_key: str, database_url: str = "") -> None:
    LOCAL_SECRETS_PATH.parent.mkdir(exist_ok=True)
    content = "\n".join(
        [
            "# Local StudyAbroadOS secrets. Do not commit this file.",
            f'SUPABASE_URL = "{_toml_escape(supabase_url.strip())}"',
            f'SUPABASE_KEY = "{_toml_escape(supabase_key.strip())}"',
            f'DATABASE_URL = "{_toml_escape(database_url.strip())}"',
            "",
        ]
    )
    LOCAL_SECRETS_PATH.write_text(content, encoding="utf-8")


def _toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def get_config() -> AppConfig:
    return AppConfig(
        supabase_url=_normalize_supabase_url(_read_secret("SUPABASE_URL")),
        supabase_key=_read_secret("SUPABASE_KEY"),
        database_url=_read_secret("DATABASE_URL"),
    )


def masked(value: str) -> str:
    if not value:
        return "未配置"
    if len(value) <= 10:
        return "***"
    return f"{value[:6]}...{value[-4:]}"


def _normalize_supabase_url(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme and parsed.netloc.endswith(".supabase.co"):
        return urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
    return value.rstrip("/")
