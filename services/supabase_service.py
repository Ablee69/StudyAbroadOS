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
            client.auth.set_session(access_token, refresh_token)
    return client

