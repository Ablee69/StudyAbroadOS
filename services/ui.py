from __future__ import annotations

import streamlit as st


def inject_responsive_css() -> None:
    st.markdown(
        """
        <style>
        .main .block-container {
            padding-top: 1.25rem;
            padding-bottom: 2.5rem;
            max-width: 1180px;
        }
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        div[data-testid="stDataFrame"] {
            overflow-x: auto;
        }
        .study-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 16px;
            min-height: 92px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        .study-card-label {
            color: #64748b;
            font-size: 0.88rem;
            margin-bottom: 6px;
        }
        .study-card-value {
            color: #0f172a;
            font-size: 1.35rem;
            font-weight: 700;
            line-height: 1.25;
            overflow-wrap: anywhere;
        }
        .study-section {
            border-top: 1px solid #e5e7eb;
            padding-top: 1rem;
            margin-top: 1.25rem;
        }
        @media (max-width: 760px) {
            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            [data-testid="stMetric"] {
                padding: 12px;
            }
            .study-card {
                min-height: auto;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def setup_page(title: str, *, icon: str = "🎓") -> None:
    st.set_page_config(page_title=f"StudyAbroadOS - {title}", page_icon=icon, layout="wide")
    inject_responsive_css()
    render_sidebar()


def render_sidebar() -> None:
    from services.auth import get_current_user, logout
    from services.config import get_config, masked

    config = get_config()
    user = get_current_user()

    with st.sidebar:
        st.title("StudyAbroadOS")
        if user:
            st.caption("当前登录")
            st.write(user["email"])
            if st.button("退出登录", use_container_width=True):
                logout()
                st.rerun()
        else:
            st.caption("请先登录后使用系统")

        st.divider()
        st.page_link("app.py", label="首页 / 登录")
        st.page_link("pages/1_首页看板.py", label="首页看板")
        st.page_link("pages/2_个人申请档案.py", label="个人申请档案")
        st.page_link("pages/3_选校与项目库.py", label="选校与项目库")
        st.page_link("pages/4_申请时间线.py", label="申请时间线")
        st.page_link("pages/5_文书素材库.py", label="文书素材库")
        st.page_link("pages/6_预算与奖学金.py", label="预算与奖学金")
        st.page_link("pages/7_导出中心.py", label="导出中心")

        st.divider()
        st.caption("云端配置")
        st.caption(f"SUPABASE_URL：{masked(config.supabase_url)}")
        st.caption(f"SUPABASE_KEY：{masked(config.supabase_key)}")
        st.caption(f"DATABASE_URL：{masked(config.database_url)}")


def card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="study-card">
            <div class="study-card-label">{label}</div>
            <div class="study-card-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def config_missing_message() -> None:
    st.error("还没有配置 Supabase 连接信息，暂时不能登录或读写云端数据。")
    st.markdown(
        """
        本地开发时请复制 `.streamlit/secrets.toml.example` 为 `.streamlit/secrets.toml`，
        然后填入 `SUPABASE_URL`、`SUPABASE_KEY` 和 `DATABASE_URL`。
        部署到 Streamlit Community Cloud 时，请在应用的 Secrets 设置里填写同名配置。
        """
    )
