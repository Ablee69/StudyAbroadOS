import streamlit as st

from services.auth import require_login
from services.repository import get_profile, init_db, update_profile
from services.ui import setup_page


setup_page("个人申请档案")
require_login()
init_db()
st.title("个人申请档案")

profile = get_profile()

with st.form("profile_form"):
    st.subheader("基础信息")
    col1, col2, col3 = st.columns(3)
    target_intake = col1.text_input("目标入学季", value=profile.get("target_intake") or "", placeholder="例如：2027 Fall")
    name = col2.text_input("姓名", value=profile.get("name") or "")
    undergraduate_major = col3.text_input("本科专业", value=profile.get("undergraduate_major") or "金融学")

    col4, col5, col6 = st.columns(3)
    grade = col4.text_input("年级", value=profile.get("grade") or "大三")
    current_gpa = col5.number_input("当前 GPA", min_value=0.0, max_value=100.0, value=float(profile.get("current_gpa") or 0), step=0.01)
    gpa_scale = col6.number_input("GPA 满分制", min_value=0.0, max_value=100.0, value=float(profile.get("gpa_scale") or 4.0), step=0.1)

    col7, col8, col9 = st.columns(3)
    toefl_current = col7.number_input("托福当前分数", min_value=0, max_value=120, value=int(profile.get("toefl_current") or 0), step=1)
    toefl_target = col8.number_input("托福目标分数", min_value=0, max_value=120, value=int(profile.get("toefl_target") or 0), step=1)
    gre_gmat_status = col9.text_input("GRE/GMAT 状态", value=profile.get("gre_gmat_status") or "", placeholder="未考 / 备考中 / 已出分")

    st.subheader("申请目标")
    col10, col11, col12 = st.columns(3)
    target_regions = col10.text_input("目标国家/地区", value=profile.get("target_regions") or "", placeholder="例如：美国、英国、香港")
    target_majors = col11.text_input("目标专业方向", value=profile.get("target_majors") or "", placeholder="例如：金融、商业分析、金融工程")
    budget_range = col12.text_input("预算范围", value=profile.get("budget_range") or "", placeholder="例如：总预算 40-60 万人民币")

    st.subheader("经历素材")
    internships = st.text_area("实习经历", value=profile.get("internships") or "", height=90)
    research_experience = st.text_area("科研/论文经历", value=profile.get("research_experience") or "", height=90)
    competitions_projects = st.text_area("比赛/项目经历", value=profile.get("competitions_projects") or "", height=90)
    tutoring_part_time = st.text_area("家教/兼职经历", value=profile.get("tutoring_part_time") or "", height=90)
    stock_investment = st.text_area("股票投资经历", value=profile.get("stock_investment") or "", height=90)

    st.subheader("职业目标与备注")
    career_goals = st.text_area("职业目标", value=profile.get("career_goals") or "", height=90)
    notes = st.text_area("备注", value=profile.get("notes") or "", height=90)

    submitted = st.form_submit_button("保存个人申请档案", type="primary")

if submitted:
    update_profile(
        {
            "target_intake": target_intake,
            "name": name,
            "undergraduate_major": undergraduate_major,
            "grade": grade,
            "current_gpa": current_gpa,
            "gpa_scale": gpa_scale,
            "toefl_current": toefl_current,
            "toefl_target": toefl_target,
            "gre_gmat_status": gre_gmat_status,
            "target_regions": target_regions,
            "target_majors": target_majors,
            "budget_range": budget_range,
            "internships": internships,
            "research_experience": research_experience,
            "competitions_projects": competitions_projects,
            "tutoring_part_time": tutoring_part_time,
            "stock_investment": stock_investment,
            "career_goals": career_goals,
            "notes": notes,
        }
    )
    st.success("个人申请档案已保存。")
    st.rerun()

with st.expander("查看当前档案摘要", expanded=False):
    latest = get_profile()
    st.write(
        {
            "姓名": latest.get("name"),
            "本科专业": latest.get("undergraduate_major"),
            "年级": latest.get("grade"),
            "当前 GPA": latest.get("current_gpa"),
            "托福当前/目标": f"{latest.get('toefl_current') or 0} / {latest.get('toefl_target') or 0}",
            "目标国家/地区": latest.get("target_regions"),
            "目标专业方向": latest.get("target_majors"),
            "预算范围": latest.get("budget_range"),
        }
    )
