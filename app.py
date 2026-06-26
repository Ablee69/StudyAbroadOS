import streamlit as st

from services.auth import get_current_user, login, signup
from services.config import get_config, save_local_secrets
from services.repository import dashboard_stats, init_db, money
from services.ui import card, config_missing_message, setup_page


setup_page("首页 / 登录")
init_db()

st.title("StudyAbroadOS")
st.caption("云端个人工作台：留学申请规划、项目库、时间线、文书素材、预算与导出。")

config = get_config()
if not config.has_supabase_client_config:
    config_missing_message()
    st.subheader("在这里粘贴 Supabase 配置")
    with st.form("supabase_setup_form"):
        supabase_url = st.text_input("SUPABASE_URL", placeholder="https://xxxxxxxxxxxx.supabase.co")
        supabase_key = st.text_input("SUPABASE_KEY", type="password", placeholder="anon public key 或 publishable key")
        database_url = st.text_input("DATABASE_URL（可先留空）", type="password", placeholder="后面部署或直连数据库时再填")
        setup_submitted = st.form_submit_button("保存配置", type="primary", use_container_width=True)
    if setup_submitted:
        if not supabase_url.startswith("https://") or ".supabase.co" not in supabase_url:
            st.error("SUPABASE_URL 看起来不对，应该类似 https://xxxxxxxxxxxx.supabase.co")
        elif len(supabase_key.strip()) < 20:
            st.error("SUPABASE_KEY 看起来太短，请确认复制的是 anon public key 或 publishable key。")
        else:
            save_local_secrets(supabase_url, supabase_key, database_url)
            st.success("配置已保存。请刷新页面，如果仍提示未配置，就重启 Streamlit。")
            st.rerun()
    st.stop()

user = get_current_user()

if user:
    st.success(f"已登录：{user['email']}")
    stats = dashboard_stats()
    profile = stats["profile"]

    cols = st.columns(4)
    with cols[0]:
        card("目标入学季", profile.get("target_intake") or "未填写")
    with cols[1]:
        card("当前 GPA", f"{profile.get('current_gpa') or 0:g} / {profile.get('gpa_scale') or 4:g}")
    with cols[2]:
        card("托福当前 / 目标", f"{int(profile.get('toefl_current') or 0)} / {int(profile.get('toefl_target') or 0)}")
    with cols[3]:
        card("预算预估", money(stats["estimated_budget"]))

    st.markdown('<div class="study-section"></div>', unsafe_allow_html=True)
    st.subheader("快速进入")
    nav_cols = st.columns(4)
    nav_cols[0].page_link("pages/2_个人申请档案.py", label="个人申请档案", use_container_width=True)
    nav_cols[1].page_link("pages/3_选校与项目库.py", label="选校与项目库", use_container_width=True)
    nav_cols[2].page_link("pages/4_申请时间线.py", label="申请时间线", use_container_width=True)
    nav_cols[3].page_link("pages/7_导出中心.py", label="导出中心", use_container_width=True)

    st.info("所有数据都会按当前登录用户隔离保存到 Supabase。")
else:
    st.subheader("邮箱密码登录")
    login_tab, signup_tab = st.tabs(["登录", "创建账号"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("邮箱", placeholder="you@example.com")
            password = st.text_input("密码", type="password")
            remember = st.checkbox("在这台设备保持登录", value=True)
            submitted = st.form_submit_button("登录", type="primary", use_container_width=True)
        if submitted:
            ok, message = login(email, password, remember=remember)
            if ok:
                st.success(message)
                st.info("登录状态已保存。请点击下面按钮进入系统；以后刷新页面一般不需要重新登录。")
                if st.button("进入系统", type="primary", use_container_width=True):
                    st.rerun()
            else:
                st.error(message)

    with signup_tab:
        st.caption("如果你只想手动创建用户，也可以在 Supabase Dashboard 的 Authentication 里添加用户。")
        with st.form("signup_form"):
            signup_email = st.text_input("注册邮箱", placeholder="you@example.com")
            signup_password = st.text_input("注册密码", type="password", help="至少 8 位")
            signup_remember = st.checkbox("在这台设备保持登录", value=True, key="signup_remember")
            signup_submitted = st.form_submit_button("创建账号", use_container_width=True)
        if signup_submitted:
            ok, message = signup(signup_email, signup_password, remember=signup_remember)
            if ok:
                st.success(message)
                if get_current_user():
                    st.info("登录状态已保存。请点击下面按钮进入系统。")
                    if st.button("进入系统", type="primary", use_container_width=True, key="signup_enter_app"):
                        st.rerun()
            else:
                st.error(message)
