from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st

from services.auth import require_login
from services.repository import (
    add_program,
    delete_program,
    get_program,
    get_program_filter_values,
    get_program_options,
    get_programs,
    import_programs_from_df,
    init_db,
    normalize_program_import,
    program_import_template_df,
    update_program,
)
from services.ui import setup_page


setup_page("选校与项目库")
require_login()
init_db()
st.title("选校与项目库")

CATEGORY_OPTIONS = ["冲刺", "匹配", "保底", "奖学金友好"]
STATUS_OPTIONS = ["未开始", "准备中", "已提交", "已录取", "被拒", "放弃"]
DEGREE_OPTIONS = ["", "MSc", "MS", "MA", "MFin", "MBA", "MPhil", "PhD", "其他"]


def option_index(options: list[str], value: str | None, default: int = 0) -> int:
    if value in options:
        return options.index(value)
    return default


def parse_deadline(value: str) -> tuple[str, bool]:
    text = value.strip()
    if not text:
        return "", True
    try:
        datetime.strptime(text, "%Y-%m-%d")
        return text, True
    except ValueError:
        return text, False


def excel_bytes(df: pd.DataFrame, sheet_name: str) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()


def read_uploaded_program_file(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    return pd.read_excel(uploaded_file)


def project_form(prefix: str, defaults: dict | None = None) -> dict:
    defaults = defaults or {}
    col1, col2, col3 = st.columns(3)
    region = col1.text_input("国家/地区", value=defaults.get("region") or "", key=f"{prefix}_region")
    school_name = col2.text_input("学校名称", value=defaults.get("school_name") or "", key=f"{prefix}_school")
    program_name = col3.text_input("项目名称", value=defaults.get("program_name") or "", key=f"{prefix}_program")

    col4, col5, col6 = st.columns(3)
    degree_type = col4.selectbox(
        "学位类型",
        DEGREE_OPTIONS,
        index=option_index(DEGREE_OPTIONS, defaults.get("degree_type")),
        key=f"{prefix}_degree",
    )
    academic_direction = col5.text_input("专业方向", value=defaults.get("academic_direction") or "", key=f"{prefix}_direction")
    website = col6.text_input("项目官网链接", value=defaults.get("website") or "", key=f"{prefix}_website")

    col7, col8, col9 = st.columns(3)
    tuition = col7.number_input("学费", min_value=0.0, value=float(defaults.get("tuition") or 0), step=1000.0, key=f"{prefix}_tuition")
    living_cost = col8.number_input("生活费预估", min_value=0.0, value=float(defaults.get("living_cost") or 0), step=1000.0, key=f"{prefix}_living")
    application_fee = col9.number_input("申请费", min_value=0.0, value=float(defaults.get("application_fee") or 0), step=10.0, key=f"{prefix}_app_fee")

    col10, col11, col12 = st.columns(3)
    deadline = col10.text_input("截止日期", value=defaults.get("deadline") or "", placeholder="YYYY-MM-DD，可留空", key=f"{prefix}_deadline")
    category = col11.selectbox(
        "申请分类",
        CATEGORY_OPTIONS,
        index=option_index(CATEGORY_OPTIONS, defaults.get("category"), default=1),
        key=f"{prefix}_category",
    )
    status = col12.selectbox(
        "当前状态",
        STATUS_OPTIONS,
        index=option_index(STATUS_OPTIONS, defaults.get("status")),
        key=f"{prefix}_status",
    )

    col13, col14 = st.columns(2)
    gpa_requirement = col13.text_input("GPA 要求", value=defaults.get("gpa_requirement") or "", key=f"{prefix}_gpa_req")
    toefl_requirement = col14.text_input("托福要求", value=defaults.get("toefl_requirement") or "", key=f"{prefix}_toefl_req")

    col15, col16 = st.columns(2)
    gre_gmat_requirement = col15.text_input("GRE/GMAT 要求", value=defaults.get("gre_gmat_requirement") or "", key=f"{prefix}_gre_req")
    recommendation_requirement = col16.text_input("推荐信要求", value=defaults.get("recommendation_requirement") or "", key=f"{prefix}_rec_req")

    essay_requirement = st.text_area("文书要求", value=defaults.get("essay_requirement") or "", height=90, key=f"{prefix}_essay_req")
    scholarship_available = st.checkbox("是否有奖学金", value=bool(defaults.get("scholarship_available") or 0), key=f"{prefix}_scholarship")
    employment_notes = st.text_area("就业导向备注", value=defaults.get("employment_notes") or "", height=80, key=f"{prefix}_employment")
    notes = st.text_area("备注", value=defaults.get("notes") or "", height=80, key=f"{prefix}_notes")

    return {
        "region": region,
        "school_name": school_name.strip(),
        "program_name": program_name.strip(),
        "degree_type": degree_type,
        "academic_direction": academic_direction,
        "website": website,
        "tuition": tuition,
        "living_cost": living_cost,
        "application_fee": application_fee,
        "deadline": deadline,
        "gpa_requirement": gpa_requirement,
        "toefl_requirement": toefl_requirement,
        "gre_gmat_requirement": gre_gmat_requirement,
        "recommendation_requirement": recommendation_requirement,
        "essay_requirement": essay_requirement,
        "scholarship_available": int(scholarship_available),
        "employment_notes": employment_notes,
        "category": category,
        "status": status,
        "notes": notes,
    }


st.subheader("项目筛选")
f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
search = f1.text_input("搜索学校/项目/方向", placeholder="输入关键词")
region_filter = f2.selectbox("国家/地区", get_program_filter_values("region"))
category_filter = f3.selectbox("申请分类", get_program_filter_values("category"))
status_filter = f4.selectbox("当前状态", get_program_filter_values("status"))

programs = get_programs(search, region_filter, category_filter, status_filter)
st.caption("项目按截止日期从近到远排序，未填写截止日期的项目排在后面。")

if programs.empty:
    st.info("还没有项目记录，或当前筛选条件下没有结果。")
else:
    display = programs.copy()
    display["scholarship_available"] = display["scholarship_available"].map(lambda value: "是" if int(value or 0) else "否")
    display = display[
        [
            "id",
            "region",
            "school_name",
            "program_name",
            "degree_type",
            "academic_direction",
            "tuition",
            "living_cost",
            "application_fee",
            "deadline",
            "gpa_requirement",
            "toefl_requirement",
            "gre_gmat_requirement",
            "recommendation_requirement",
            "essay_requirement",
            "scholarship_available",
            "category",
            "status",
            "employment_notes",
            "notes",
            "website",
        ]
    ].rename(
        columns={
            "id": "ID",
            "region": "国家/地区",
            "school_name": "学校名称",
            "program_name": "项目名称",
            "degree_type": "学位类型",
            "academic_direction": "专业方向",
            "website": "项目官网链接",
            "tuition": "学费",
            "living_cost": "生活费预估",
            "application_fee": "申请费",
            "deadline": "截止日期",
            "gpa_requirement": "GPA 要求",
            "toefl_requirement": "托福要求",
            "gre_gmat_requirement": "GRE/GMAT 要求",
            "recommendation_requirement": "推荐信要求",
            "essay_requirement": "文书要求",
            "scholarship_available": "是否有奖学金",
            "employment_notes": "就业导向备注",
            "category": "申请分类",
            "status": "当前状态",
            "notes": "备注",
        }
    )
    st.dataframe(display, use_container_width=True, hide_index=True)

st.divider()

tab_add, tab_import, tab_edit = st.tabs(["新增项目", "批量导入", "编辑/删除项目"])

with tab_add:
    with st.form("add_program_form"):
        new_data = project_form("add")
        add_submitted = st.form_submit_button("保存新项目", type="primary")
    if add_submitted:
        deadline, valid = parse_deadline(new_data["deadline"])
        new_data["deadline"] = deadline
        if not new_data["school_name"] or not new_data["program_name"]:
            st.error("学校名称和项目名称不能为空。")
        elif not valid:
            st.error("截止日期格式应为 YYYY-MM-DD，例如 2026-12-01。")
        else:
            add_program(new_data)
            st.success("项目已保存。")
            st.rerun()

with tab_import:
    st.subheader("批量导入选校表")
    st.caption("系统不会内置或编造学校信息。请把你从官网核实后的学校/项目资料填进模板，再导入到自己的账号。")

    template_df = program_import_template_df()
    st.download_button(
        "下载选校导入模板 Excel",
        data=excel_bytes(template_df, "选校导入模板"),
        file_name="StudyAbroadOS_选校导入模板.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    uploaded_file = st.file_uploader("上传填写好的 Excel 或 CSV", type=["xlsx", "csv"])
    if uploaded_file:
        try:
            upload_df = read_uploaded_program_file(uploaded_file)
        except Exception as exc:
            st.error(f"读取文件失败：{exc}")
            upload_df = pd.DataFrame()

        if not upload_df.empty:
            rows, errors = normalize_program_import(upload_df)
            if errors:
                st.error("导入前检查发现问题，请先修改表格。")
                for error in errors[:10]:
                    st.write(f"- {error}")
                if len(errors) > 10:
                    st.caption(f"还有 {len(errors) - 10} 条问题未显示。")
            elif not rows:
                st.warning("没有识别到可导入的项目行。")
            else:
                st.success(f"已识别 {len(rows)} 条项目，下面是前 20 条预览。")
                preview = pd.DataFrame(rows).head(20)
                st.dataframe(preview, use_container_width=True, hide_index=True)
                if st.button("确认导入到我的选校库", type="primary", use_container_width=True):
                    result = import_programs_from_df(upload_df)
                    if result["errors"]:
                        st.error("导入失败，请根据提示修改表格。")
                        for error in result["errors"]:
                            st.write(f"- {error}")
                    else:
                        st.success(f"导入完成：新增 {result['created']} 条，跳过重复 {result['skipped']} 条。")
                        st.rerun()

with tab_edit:
    options = get_program_options()
    if options.empty:
        st.info("暂无可编辑项目。")
    else:
        labels = {
            f"{row.id} | {row.school_name} - {row.program_name}": row.id
            for row in options.itertuples()
        }
        selected_label = st.selectbox("选择要编辑的项目", list(labels.keys()))
        selected_id = labels[selected_label]
        selected_program = get_program(selected_id) or {}
        with st.form("edit_program_form"):
            updated_data = project_form("edit", selected_program)
            confirm_delete = st.checkbox("确认删除该项目", key="confirm_delete_program")
            col_save, col_delete = st.columns(2)
            update_submitted = col_save.form_submit_button("保存修改", type="primary")
            delete_submitted = col_delete.form_submit_button("删除项目")
        if update_submitted:
            deadline, valid = parse_deadline(updated_data["deadline"])
            updated_data["deadline"] = deadline
            if not updated_data["school_name"] or not updated_data["program_name"]:
                st.error("学校名称和项目名称不能为空。")
            elif not valid:
                st.error("截止日期格式应为 YYYY-MM-DD，例如 2026-12-01。")
            else:
                update_program(selected_id, updated_data)
                st.success("项目修改已保存。")
                st.rerun()
        if delete_submitted:
            if confirm_delete:
                delete_program(selected_id)
                st.success("项目已删除。")
                st.rerun()
            else:
                st.warning("请先勾选确认删除。")
