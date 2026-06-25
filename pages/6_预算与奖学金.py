import streamlit as st

from services.auth import require_login
from services.repository import (
    add_budget,
    budget_stats,
    calc_total_cost,
    delete_budget,
    get_budget,
    get_budgets,
    get_program_options,
    init_db,
    label_program,
    money,
    update_budget,
)
from services.ui import setup_page


setup_page("预算与奖学金")
require_login()
init_db()
st.title("预算与奖学金")


def budget_form(prefix: str, defaults: dict | None = None) -> dict:
    defaults = defaults or {}

    program_options = get_program_options()
    if not program_options.empty:
        with st.expander("可参考的项目库名称", expanded=False):
            for row in program_options.to_dict("records"):
                st.caption(label_program(row))

    program_ref = st.text_input("学校/项目", value=defaults.get("program_ref") or "", key=f"{prefix}_program_ref")

    col1, col2, col3 = st.columns(3)
    application_fee = col1.number_input("申请费", min_value=0.0, value=float(defaults.get("application_fee") or 0), step=10.0, key=f"{prefix}_application_fee")
    score_report_fee = col2.number_input("托福/GRE寄送费", min_value=0.0, value=float(defaults.get("score_report_fee") or 0), step=10.0, key=f"{prefix}_score_report_fee")
    visa_flight_estimate = col3.number_input("签证/机票预估", min_value=0.0, value=float(defaults.get("visa_flight_estimate") or 0), step=500.0, key=f"{prefix}_visa_flight")

    col4, col5, col6 = st.columns(3)
    tuition = col4.number_input("学费", min_value=0.0, value=float(defaults.get("tuition") or 0), step=1000.0, key=f"{prefix}_tuition")
    living_cost = col5.number_input("生活费", min_value=0.0, value=float(defaults.get("living_cost") or 0), step=1000.0, key=f"{prefix}_living_cost")
    scholarship_amount = col6.number_input("奖学金金额", min_value=0.0, value=float(defaults.get("scholarship_amount") or 0), step=1000.0, key=f"{prefix}_scholarship")

    notes = st.text_area("备注", value=defaults.get("notes") or "", height=90, key=f"{prefix}_notes")
    data = {
        "program_ref": program_ref.strip(),
        "application_fee": application_fee,
        "score_report_fee": score_report_fee,
        "tuition": tuition,
        "living_cost": living_cost,
        "visa_flight_estimate": visa_flight_estimate,
        "scholarship_amount": scholarship_amount,
        "notes": notes,
    }
    total_cost = calc_total_cost(data)
    st.metric("总成本", money(total_cost))
    st.metric("奖学金后成本", money(total_cost - scholarship_amount))
    return data


stats = budget_stats()
metric_cols = st.columns(3)
metric_cols[0].metric("总申请阶段成本", money(stats["application_stage_cost"]))
metric_cols[1].metric("项目总成本合计", money(stats["total_project_cost"]))
metric_cols[2].metric("奖学金后成本合计", money(stats["total_net_cost"]))

detail_cols = st.columns(2)
if stats["cheapest"]:
    detail_cols[0].success(f"最便宜的项目：{stats['cheapest']['program_ref']}，奖学金后 {money(stats['cheapest']['net_cost'])}")
else:
    detail_cols[0].info("暂无最便宜项目。")

if stats["highest"]:
    detail_cols[1].warning(f"成本最高的项目：{stats['highest']['program_ref']}，奖学金后 {money(stats['highest']['net_cost'])}")
else:
    detail_cols[1].info("暂无成本最高项目。")

budgets = get_budgets()
if budgets.empty:
    st.info("还没有预算记录。")
else:
    display = budgets[
        [
            "id",
            "program_ref",
            "application_fee",
            "score_report_fee",
            "tuition",
            "living_cost",
            "visa_flight_estimate",
            "scholarship_amount",
            "computed_total_cost",
            "net_cost",
            "notes",
        ]
    ].rename(
        columns={
            "id": "ID",
            "program_ref": "学校/项目",
            "application_fee": "申请费",
            "score_report_fee": "托福/GRE寄送费",
            "tuition": "学费",
            "living_cost": "生活费",
            "visa_flight_estimate": "签证/机票预估",
            "scholarship_amount": "奖学金金额",
            "computed_total_cost": "总成本",
            "net_cost": "奖学金后成本",
            "notes": "备注",
        }
    )
    st.dataframe(display, use_container_width=True, hide_index=True)

st.divider()

tab_add, tab_edit = st.tabs(["新增预算", "编辑/删除预算"])

with tab_add:
    with st.form("add_budget_form"):
        new_budget = budget_form("add")
        add_submitted = st.form_submit_button("保存新预算", type="primary")
    if add_submitted:
        if not new_budget["program_ref"]:
            st.error("学校/项目不能为空。")
        else:
            add_budget(new_budget)
            st.success("预算已保存。")
            st.rerun()

with tab_edit:
    budgets = get_budgets()
    if budgets.empty:
        st.info("暂无可编辑预算。")
    else:
        labels = {
            f"{row.id} | {row.program_ref}": row.id
            for row in budgets.itertuples()
        }
        selected_label = st.selectbox("选择要编辑的预算", list(labels.keys()))
        selected_id = labels[selected_label]
        selected_budget = get_budget(selected_id) or {}
        with st.form("edit_budget_form"):
            updated_budget = budget_form("edit", selected_budget)
            confirm_delete = st.checkbox("确认删除该预算", key="confirm_delete_budget")
            col_save, col_delete = st.columns(2)
            update_submitted = col_save.form_submit_button("保存修改", type="primary")
            delete_submitted = col_delete.form_submit_button("删除预算")
        if update_submitted:
            if not updated_budget["program_ref"]:
                st.error("学校/项目不能为空。")
            else:
                update_budget(selected_id, updated_budget)
                st.success("预算修改已保存。")
                st.rerun()
        if delete_submitted:
            if confirm_delete:
                delete_budget(selected_id)
                st.success("预算已删除。")
                st.rerun()
            else:
                st.warning("请先勾选确认删除。")
