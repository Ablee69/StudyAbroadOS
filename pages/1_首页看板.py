import streamlit as st

from services.auth import require_login
from services.repository import dashboard_stats, init_db, money
from services.ui import card, setup_page


setup_page("首页看板")
require_login()
init_db()
st.title("首页看板")

stats = dashboard_stats()
profile = stats["profile"]

top_cols = st.columns(4)
with top_cols[0]:
    card("目标入学季", profile.get("target_intake") or "未填写")
with top_cols[1]:
    card("当前 GPA", f"{profile.get('current_gpa') or 0:g} / {profile.get('gpa_scale') or 4:g}")
with top_cols[2]:
    card("当前托福分数", str(int(profile.get("toefl_current") or 0)))
with top_cols[3]:
    card("托福目标分数", str(int(profile.get("toefl_target") or 0)))

bottom_cols = st.columns(2)
with bottom_cols[0]:
    card("已加入选校库的项目数量", str(stats["program_count"]))
with bottom_cols[1]:
    card("总申请预算预估", money(stats["estimated_budget"]))

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("未来 30 天申请任务")
    recent_tasks = stats["recent_tasks"]
    if recent_tasks.empty:
        st.info("未来 30 天还没有申请任务。")
    else:
        st.dataframe(
            recent_tasks[
                ["deadline", "task_name", "related_program", "task_type", "priority", "status"]
            ].rename(
                columns={
                    "deadline": "截止日期",
                    "task_name": "任务名称",
                    "related_program": "所属学校/项目",
                    "task_type": "任务类型",
                    "priority": "优先级",
                    "status": "当前状态",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

with right:
    st.subheader("临近截止日期的项目")
    upcoming_programs = stats["upcoming_programs"]
    if upcoming_programs.empty:
        st.info("未来 60 天暂无临近截止日期的项目。")
    else:
        st.dataframe(
            upcoming_programs.rename(
                columns={
                    "id": "ID",
                    "region": "国家/地区",
                    "school_name": "学校名称",
                    "program_name": "项目名称",
                    "deadline": "截止日期",
                    "category": "申请分类",
                    "status": "当前状态",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

st.divider()
st.caption("预算预估来自“预算与奖学金”页面录入的数据，显示为奖学金后的总成本合计。")
