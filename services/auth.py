from __future__ import annotations

from typing import Any

import streamlit as st

from services.config import get_config
from services.supabase_service import SupabaseConfigError, get_supabase_client


AUTH_KEYS = {"user_id", "user_email", "access_token", "refresh_token"}


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


def login(email: str, password: str) -> tuple[bool, str]:
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

    st.session_state["user_id"] = str(_read_attr(user, "id", ""))
    st.session_state["user_email"] = str(_read_attr(user, "email", email))
    st.session_state["access_token"] = str(_read_attr(session, "access_token", ""))
    st.session_state["refresh_token"] = str(_read_attr(session, "refresh_token", ""))
    return True, "登录成功。"


def signup(email: str, password: str) -> tuple[bool, str]:
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
        st.session_state["user_id"] = str(_read_attr(user, "id", ""))
        st.session_state["user_email"] = str(_read_attr(user, "email", email))
        st.session_state["access_token"] = str(_read_attr(session, "access_token", ""))
        st.session_state["refresh_token"] = str(_read_attr(session, "refresh_token", ""))
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


def require_login() -> dict[str, str]:
    config = get_config()
    if not config.has_supabase_client_config:
        from services.ui import config_missing_message

        config_missing_message()
        st.stop()
        raise SystemExit

    user = get_current_user()
    if not user or not st.session_state.get("access_token"):
        st.warning("请先使用邮箱和密码登录。")
        st.page_link("app.py", label="返回登录页")
        st.stop()
        raise SystemExit
    return user
