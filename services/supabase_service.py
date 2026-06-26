from __future__ import annotations

import streamlit as st
from supabase import Client, create_client

from services.config import get_config


class SupabaseConfigError(RuntimeError):
    pass


def get_supabase_client(*, with_session: bool = True) -> Client:
    config = get_config()
    if not config.has_supabase_client_config:
        raise SupabaseConfigError("SUPABASE_URL 和 SUPABASE_KEY 未配置。")

    client = create_client(config.supabase_url, config.supabase_key)
    if with_session:
        access_token = st.session_state.get("access_token")
        refresh_token = st.session_state.get("refresh_token")
        if access_token and refresh_token:
            try:
                client.auth.set_session(access_token, refresh_token)
            except Exception as exc:
                st.error("登录状态校验失败：云端连接暂时不稳定。")
                st.caption(f"技术信息：{exc}")
                st.info("请刷新页面再试；如果仍然失败，请退出登录后重新登录。")
                st.stop()
    return client
