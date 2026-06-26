from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta
from typing import Any

import streamlit as st

from services.config import get_config
from services.supabase_service import SupabaseConfigError, get_supabase_client

try:
    import extra_streamlit_components as stx
except Exception:  # Optional dependency; auth still works without remembered login.
    stx = None


AUTH_KEYS = {"user_id", "user_email", "access_token", "refresh_token"}
AUTH_COOKIE_NAME = "studyabroados_auth"
COOKIE_MANAGER_KEY = "_studyabroados_cookie_manager"
REMEMBER_DAYS = 30


def _read_attr(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def get_current_user() -> dict[str, str] | None:
    user_id = st.session_state.get("user_id")
    email = st.session_state.get("user_email")
    if not user_id or not email:
        return None
    return {"id": str(user_id), "email": str(email)}


def is_logged_in() -> bool:
    return get_current_user() is not None and bool(st.session_state.get("access_token"))


def login(email: str, password: str, remember: bool = True) -> tuple[bool, str]:
    email = email.strip().lower()
    if not email or "@" not in email:
        return False, "请输入有效邮箱。"
    if not password:
        return False, "请输入密码。"

    try:
        client = get_supabase_client(with_session=False)
        response = client.auth.sign_in_with_password({"email": email, "password": password})
    except SupabaseConfigError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, f"登录失败：{exc}"

    session = _read_attr(response, "session")
    user = _read_attr(response, "user")
    if not session or not user:
        return False, "登录失败：未获取到有效会话。"

    _store_auth_state(user, session, fallback_email=email)
    if remember:
        save_auth_cookie()
    else:
        clear_auth_cookie()
    return True, "登录成功。"


def signup(email: str, password: str, remember: bool = True) -> tuple[bool, str]:
    email = email.strip().lower()
    if not email or "@" not in email:
        return False, "请输入有效邮箱。"
    if len(password) < 8:
        return False, "密码至少需要 8 位。"

    try:
        client = get_supabase_client(with_session=False)
        response = client.auth.sign_up({"email": email, "password": password})
    except SupabaseConfigError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, f"注册失败：{exc}"

    session = _read_attr(response, "session")
    user = _read_attr(response, "user")
    if session and user:
        _store_auth_state(user, session, fallback_email=email)
        if remember:
            save_auth_cookie()
        return True, "注册并登录成功。"

    return True, "注册请求已提交。如果 Supabase 开启邮箱确认，请先查收邮件完成确认。"


def logout() -> None:
    try:
        if st.session_state.get("access_token"):
            get_supabase_client(with_session=True).auth.sign_out()
    except Exception:
        pass
    for key in AUTH_KEYS:
        st.session_state.pop(key, None)
    clear_auth_cookie()


def require_login() -> dict[str, str]:
    config = get_config()
    if not config.has_supabase_client_config:
        from services.ui import config_missing_message

        config_missing_message()
        st.stop()
        raise SystemExit

    restore_session_from_cookie()
    user = get_current_user()
    if not user or not st.session_state.get("access_token"):
        st.warning("请先使用邮箱和密码登录。")
        st.page_link("app.py", label="返回登录页")
        st.stop()
        raise SystemExit
    return user


def _store_auth_state(user: Any, session: Any, fallback_email: str = "") -> None:
    st.session_state["user_id"] = str(_read_attr(user, "id", ""))
    st.session_state["user_email"] = str(_read_attr(user, "email", fallback_email))
    st.session_state["access_token"] = str(_read_attr(session, "access_token", ""))
    st.session_state["refresh_token"] = str(_read_attr(session, "refresh_token", ""))


def _cookie_manager():
    if stx is None:
        return None
    if COOKIE_MANAGER_KEY not in st.session_state:
        st.session_state[COOKIE_MANAGER_KEY] = stx.CookieManager()
    return st.session_state[COOKIE_MANAGER_KEY]


def _encode_cookie_payload(payload: dict[str, str]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def _decode_cookie_payload(value: str) -> dict[str, str]:
    raw = base64.urlsafe_b64decode(value.encode("ascii"))
    data = json.loads(raw.decode("utf-8"))
    return data if isinstance(data, dict) else {}


def save_auth_cookie() -> None:
    manager = _cookie_manager()
    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")
    if not manager or not access_token or not refresh_token:
        return
    payload = {
        "user_id": str(st.session_state.get("user_id") or ""),
        "user_email": str(st.session_state.get("user_email") or ""),
        "access_token": str(access_token),
        "refresh_token": str(refresh_token),
    }
    manager.set(
        AUTH_COOKIE_NAME,
        _encode_cookie_payload(payload),
        expires_at=datetime.now() + timedelta(days=REMEMBER_DAYS),
    )


def clear_auth_cookie() -> None:
    manager = _cookie_manager()
    if not manager:
        return
    try:
        manager.delete(AUTH_COOKIE_NAME)
    except Exception:
        pass


def restore_session_from_cookie() -> bool:
    if is_logged_in():
        return True
    manager = _cookie_manager()
    if not manager:
        return False
    raw_cookie = manager.get(AUTH_COOKIE_NAME)
    if not raw_cookie:
        return False
    try:
        data = _decode_cookie_payload(str(raw_cookie))
        access_token = str(data.get("access_token") or "")
        refresh_token = str(data.get("refresh_token") or "")
        if not access_token or not refresh_token:
            return False

        client = get_supabase_client(with_session=False)
        response = client.auth.set_session(access_token, refresh_token)
        session = _read_attr(response, "session", response)
        user = _read_attr(response, "user")
        if not user:
            user_response = client.auth.get_user()
            user = _read_attr(user_response, "user")
        if not user:
            return False
        _store_auth_state(user, session, fallback_email=str(data.get("user_email") or ""))
        save_auth_cookie()
        return True
    except Exception:
        for key in AUTH_KEYS:
            st.session_state.pop(key, None)
        clear_auth_cookie()
        return False
