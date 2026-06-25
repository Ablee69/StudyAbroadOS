import streamlit as st

from services.auth import require_login
from services.repository import (
    add_material,
    build_material_summary,
    delete_material,
    get_material,
    get_materials,
    init_db,
    update_material,
)
from services.ui import setup_page


setup_page("文书素材库")
require_login()
init_db()
st.title("文书素材库")

EXPERIENCE_TYPES = ["课程", "论文", "实习", "股票投资", "家教", "比赛", "社团", "个人成长"]
USAGE_OPTIONS = ["PS", "CV", "面试", "推荐信"]


def option_index(options: list[str], value: str | None, default: int = 0) -> int:
    if value in options:
        return options.index(value)
    return default


def usage_defaults(value: str | None) -> list[str]:
    if not value:
        return []
    raw = [item.strip() for item in value.replace("，", ",").split(",")]
    return [item for item in raw if item in USAGE_OPTIONS]


def material_form(prefix: str, defaults: dict | None = None) -> dict:
    defaults = defaults or {}
    col1, col2, col3 = st.columns(3)
    experience_name = col1.text_input("经历名称", value=defaults.get("experience_name") or "", key=f"{prefix}_name")
    experience_type = col2.selectbox(
        "经历类型",
        EXPERIENCE_TYPES,
        index=option_index(EXPERIENCE_TYPES, defaults.get("experience_type")),
        key=f"{prefix}_type",
    )
    period = col3.text_input("时间", value=defaults.get("period") or "", placeholder="例如：2025.06-2025.08", key=f"{prefix}_period")

    background = st.text_area("背景", value=defaults.get("background") or "", height=90, key=f"{prefix}_background")
    action = st.text_area("具体行动", value=defaults.get("action") or "", height=110, key=f"{prefix}_action")
    result = st.text_area("结果", value=defaults.get("result") or "", height=90, key=f"{prefix}_result")
    abilities = st.text_input("体现能力", value=defaults.get("abilities") or "", placeholder="例如：数据分析、沟通、抗压、主动学习", key=f"{prefix}_abilities")
    usage = st.multiselect(
        "可以用于 PS/CV/面试/推荐信",
        USAGE_OPTIONS,
        default=usage_defaults(defaults.get("usage")),
        key=f"{prefix}_usage",
    )
    notes = st.text_area("备注", value=defaults.get("notes") or "", height=80, key=f"{prefix}_notes")

    return {
        "experience_name": experience_name.strip(),
        "experience_type": experience_type,
        "period": period,
        "background": background,
        "action": action,
        "result": result,
        "abilities": abilities,
        "usage": ", ".join(usage),
        "notes": notes,
    }


materials = get_materials()

if materials.empty:
    st.info("还没有文书素材。建议先从实习、课程项目、股票投资、家教或比赛经历开始录入。")
else:
    st.dataframe(
        materials[
            [
                "id",
                "experience_name",
                "experience_type",
                "period",
                "abilities",
                "usage",
                "background",
                "action",
                "result",
                "notes",
            ]
        ].rename(
            columns={
                "id": "ID",
                "experience_name": "经历名称",
                "experience_type": "经历类型",
                "period": "时间",
                "background": "背景",
                "action": "具体行动",
                "result": "结果",
                "abilities": "体现能力",
                "usage": "可用于",
                "notes": "备注",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

st.divider()

st.subheader("生成文书素材总结")
if materials.empty:
    st.caption("录入素材后可在这里生成整理版。")
else:
    labels = {
        f"{row.id} | {row.experience_name}": row.id
        for row in materials.itertuples()
    }
    selected_summary_label = st.selectbox("选择经历", list(labels.keys()), key="summary_material")
    selected_material = get_material(labels[selected_summary_label]) or {}
    if st.button("生成文书素材总结", type="primary"):
        st.text_area(
            "整理结果",
            value=build_material_summary(selected_material),
            height=360,
        )

st.divider()

tab_add, tab_edit = st.tabs(["新增素材", "编辑/删除素材"])

with tab_add:
    with st.form("add_material_form"):
        new_material = material_form("add")
        add_submitted = st.form_submit_button("保存新素材", type="primary")
    if add_submitted:
        if not new_material["experience_name"]:
            st.error("经历名称不能为空。")
        else:
            add_material(new_material)
            st.success("素材已保存。")
            st.rerun()

with tab_edit:
    materials = get_materials()
    if materials.empty:
        st.info("暂无可编辑素材。")
    else:
        labels = {
            f"{row.id} | {row.experience_name}": row.id
            for row in materials.itertuples()
        }
        selected_label = st.selectbox("选择要编辑的素材", list(labels.keys()))
        selected_id = labels[selected_label]
        selected_material = get_material(selected_id) or {}
        with st.form("edit_material_form"):
            updated_material = material_form("edit", selected_material)
            confirm_delete = st.checkbox("确认删除该素材", key="confirm_delete_material")
            col_save, col_delete = st.columns(2)
            update_submitted = col_save.form_submit_button("保存修改", type="primary")
            delete_submitted = col_delete.form_submit_button("删除素材")
        if update_submitted:
            if not updated_material["experience_name"]:
                st.error("经历名称不能为空。")
            else:
                update_material(selected_id, updated_material)
                st.success("素材修改已保存。")
                st.rerun()
        if delete_submitted:
            if confirm_delete:
                delete_material(selected_id)
                st.success("素材已删除。")
                st.rerun()
            else:
                st.warning("请先勾选确认删除。")
