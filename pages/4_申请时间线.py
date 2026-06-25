from datetime import date

import streamlit as st

from services.auth import require_login
from services.repository import (
    add_task,
    delete_task,
    get_completed_tasks,
    get_overdue_tasks,
    get_recent_tasks,
    get_task,
    get_tasks,
    init_db,
    update_task,
)
from services.ui import setup_page


setup_page("申请时间线")
require_login()
init_db()
st.title("申请时间线")

TASK_TYPES = ["托福", "GRE", "选校", "文书", "CV", "推荐信", "网申", "奖学金", "签证"]
PRIORITY_OPTIONS = ["高", "中", "低"]
STATUS_OPTIONS = ["未开始", "进行中", "已完成", "暂缓"]


def option_index(options: list[str], value: str | None, default: int = 0) -> int:
    if value in options:
        return options.index(value)
    return default


def date_value(value: str | None) -> date:
    if not value:
        return date.today()
    try:
        return date.fromisoformat(value)
    except ValueError:
        return date.today()


def task_form(prefix: str, defaults: dict | None = None) -> dict:
    defaults = defaults or {}
    col1, col2 = st.columns(2)
    task_name = col1.text_input("任务名称", value=defaults.get("task_name") or "", key=f"{prefix}_task_name")
    related_program = col2.text_input("所属学校/项目", value=defaults.get("related_program") or "", key=f"{prefix}_related")

    col3, col4, col5, col6 = st.columns(4)
    task_type = col3.selectbox(
        "任务类型",
        TASK_TYPES,
        index=option_index(TASK_TYPES, defaults.get("task_type")),
        key=f"{prefix}_type",
    )
    deadline = col4.date_input("截止日期", value=date_value(defaults.get("deadline")), key=f"{prefix}_deadline")
    priority = col5.selectbox(
        "优先级",
        PRIORITY_OPTIONS,
        index=option_index(PRIORITY_OPTIONS, defaults.get("priority"), default=1),
        key=f"{prefix}_priority",
    )
    status = col6.selectbox(
        "当前状态",
        STATUS_OPTIONS,
        index=option_index(STATUS_OPTIONS, defaults.get("status")),
        key=f"{prefix}_status",
    )
    notes = st.text_area("备注", value=defaults.get("notes") or "", height=90, key=f"{prefix}_notes")
    return {
        "task_name": task_name.strip(),
        "related_program": related_program,
        "task_type": task_type,
        "deadline": deadline.isoformat(),
        "priority": priority,
        "status": status,
        "notes": notes,
    }


def show_tasks(df, empty_text: str) -> None:
    if df.empty:
        st.info(empty_text)
        return
    st.dataframe(
        df[["id", "deadline", "task_name", "related_program", "task_type", "priority", "status", "notes"]].rename(
            columns={
                "id": "ID",
                "deadline": "截止日期",
                "task_name": "任务名称",
                "related_program": "所属学校/项目",
                "task_type": "任务类型",
                "priority": "优先级",
                "status": "当前状态",
                "notes": "备注",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


recent_tasks = get_recent_tasks(30)
overdue_tasks = get_overdue_tasks()
completed_tasks = get_completed_tasks()

metric_cols = st.columns(3)
metric_cols[0].metric("未来 30 天任务", len(recent_tasks))
metric_cols[1].metric("逾期未完成任务", len(overdue_tasks))
metric_cols[2].metric("已完成任务", len(completed_tasks))

st.divider()

tab_recent, tab_overdue, tab_completed, tab_all = st.tabs(["未来 30 天", "逾期任务", "已完成任务", "全部任务"])
with tab_recent:
    show_tasks(recent_tasks, "未来 30 天暂无任务。")
with tab_overdue:
    show_tasks(overdue_tasks, "暂无逾期未完成任务。")
with tab_completed:
    show_tasks(completed_tasks, "暂无已完成任务。")
with tab_all:
    show_tasks(get_tasks(), "暂无任务。")

st.divider()

tab_add, tab_edit = st.tabs(["新增任务", "编辑/删除任务"])

with tab_add:
    with st.form("add_task_form"):
        new_task = task_form("add")
        add_submitted = st.form_submit_button("保存新任务", type="primary")
    if add_submitted:
        if not new_task["task_name"]:
            st.error("任务名称不能为空。")
        else:
            add_task(new_task)
            st.success("任务已保存。")
            st.rerun()

with tab_edit:
    tasks = get_tasks()
    if tasks.empty:
        st.info("暂无可编辑任务。")
    else:
        labels = {
            f"{row.id} | {row.deadline} | {row.task_name}": row.id
            for row in tasks.itertuples()
        }
        selected_label = st.selectbox("选择要编辑的任务", list(labels.keys()))
        selected_id = labels[selected_label]
        selected_task = get_task(selected_id) or {}
        with st.form("edit_task_form"):
            updated_task = task_form("edit", selected_task)
            confirm_delete = st.checkbox("确认删除该任务", key="confirm_delete_task")
            col_save, col_delete = st.columns(2)
            update_submitted = col_save.form_submit_button("保存修改", type="primary")
            delete_submitted = col_delete.form_submit_button("删除任务")
        if update_submitted:
            if not updated_task["task_name"]:
                st.error("任务名称不能为空。")
            else:
                update_task(selected_id, updated_task)
                st.success("任务修改已保存。")
                st.rerun()
        if delete_submitted:
            if confirm_delete:
                delete_task(selected_id)
                st.success("任务已删除。")
                st.rerun()
            else:
                st.warning("请先勾选确认删除。")
