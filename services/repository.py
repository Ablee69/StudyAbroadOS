from __future__ import annotations

import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from services.auth import get_current_user
from services.supabase_service import get_supabase_client


BASE_DIR = Path(__file__).resolve().parent.parent
EXPORTS_DIR = BASE_DIR / "exports"
TEMPLATES_DIR = BASE_DIR / "templates"


PROFILE_FIELDS = [
    "target_intake",
    "name",
    "undergraduate_major",
    "grade",
    "current_gpa",
    "gpa_scale",
    "toefl_current",
    "toefl_target",
    "gre_gmat_status",
    "target_regions",
    "target_majors",
    "budget_range",
    "internships",
    "research_experience",
    "competitions_projects",
    "tutoring_part_time",
    "stock_investment",
    "career_goals",
    "notes",
]

PROGRAM_FIELDS = [
    "region",
    "school_name",
    "program_name",
    "degree_type",
    "academic_direction",
    "website",
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
    "employment_notes",
    "category",
    "status",
    "notes",
]

TASK_FIELDS = [
    "task_name",
    "related_program",
    "task_type",
    "deadline",
    "priority",
    "status",
    "notes",
]

MATERIAL_FIELDS = [
    "experience_name",
    "experience_type",
    "period",
    "background",
    "action",
    "result",
    "abilities",
    "usage",
    "notes",
]

BUDGET_FIELDS = [
    "program_ref",
    "application_fee",
    "score_report_fee",
    "tuition",
    "living_cost",
    "visa_flight_estimate",
    "scholarship_amount",
    "total_cost",
    "notes",
]

DATE_FIELDS = {"deadline"}
BOOLEAN_FIELDS = {"scholarship_available"}

PROGRAM_IMPORT_COLUMNS = {
    "国家/地区": "region",
    "学校名称": "school_name",
    "项目名称": "program_name",
    "学位类型": "degree_type",
    "专业方向": "academic_direction",
    "项目官网链接": "website",
    "学费": "tuition",
    "生活费预估": "living_cost",
    "申请费": "application_fee",
    "截止日期": "deadline",
    "GPA 要求": "gpa_requirement",
    "托福要求": "toefl_requirement",
    "GRE/GMAT 要求": "gre_gmat_requirement",
    "推荐信要求": "recommendation_requirement",
    "文书要求": "essay_requirement",
    "是否有奖学金": "scholarship_available",
    "就业导向备注": "employment_notes",
    "申请分类": "category",
    "当前状态": "status",
    "备注": "notes",
}

PROGRAM_TEMPLATE_COLUMNS = list(PROGRAM_IMPORT_COLUMNS.keys())


def init_db() -> None:
    EXPORTS_DIR.mkdir(exist_ok=True)
    TEMPLATES_DIR.mkdir(exist_ok=True)


def _user_id() -> str:
    user = get_current_user()
    if not user:
        raise PermissionError("用户未登录。")
    return user["id"]


def _client():
    return get_supabase_client(with_session=True)


def _safe_execute(query: Any, action: str) -> Any:
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            return query.execute()
        except Exception as exc:  # Supabase client raises several exception types.
            last_error = exc
            if attempt == 0:
                time.sleep(0.4)
                continue
    st.error(f"{action}失败：云端数据库暂时不可用。")
    st.caption(f"技术信息：{last_error}")
    st.info("请先刷新页面再试；如果仍失败，检查 Supabase 项目是否暂停、网络是否正常、Secrets 是否填对。")
    st.stop()
    raise SystemExit


def _empty_df(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def _df(records: list[dict[str, Any]] | None, columns: list[str]) -> pd.DataFrame:
    if not records:
        return _empty_df(columns)
    df = pd.DataFrame(records)
    for column in columns:
        if column not in df.columns:
            df[column] = None
    return df[columns]


def _clean_payload(data: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    payload = {field: data.get(field) for field in fields}
    for field in DATE_FIELDS:
        if field in payload and payload[field] == "":
            payload[field] = None
    for field in BOOLEAN_FIELDS:
        if field in payload:
            payload[field] = bool(payload[field])
    return payload


def _select_owned(table: str, columns: list[str]) -> pd.DataFrame:
    response = _safe_execute(_client().table(table).select("*").eq("user_id", _user_id()), "读取数据")
    return _df(response.data, ["id", "user_id"] + columns + ["created_at", "updated_at"])


def _insert_owned(table: str, data: dict[str, Any], fields: list[str]) -> int | str:
    payload = _clean_payload(data, fields)
    payload["user_id"] = _user_id()
    response = _safe_execute(_client().table(table).insert(payload), "保存数据")
    if response.data:
        return response.data[0].get("id", "")
    return ""


def _update_owned(table: str, record_id: int | str, data: dict[str, Any], fields: list[str]) -> None:
    payload = _clean_payload(data, fields)
    _safe_execute(_client().table(table).update(payload).eq("id", record_id).eq("user_id", _user_id()), "更新数据")


def _delete_owned(table: str, record_id: int | str) -> None:
    _safe_execute(_client().table(table).delete().eq("id", record_id).eq("user_id", _user_id()), "删除数据")


def as_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def calc_total_cost(data: dict[str, Any]) -> float:
    return (
        as_float(data.get("application_fee"))
        + as_float(data.get("score_report_fee"))
        + as_float(data.get("tuition"))
        + as_float(data.get("living_cost"))
        + as_float(data.get("visa_flight_estimate"))
    )


def money(value: Any) -> str:
    return f"¥{as_float(value):,.0f}"


def default_profile() -> dict[str, Any]:
    return {
        "target_intake": "",
        "name": "",
        "undergraduate_major": "金融学",
        "grade": "大三",
        "current_gpa": 0,
        "gpa_scale": 4.0,
        "toefl_current": 0,
        "toefl_target": 0,
        "gre_gmat_status": "",
        "target_regions": "",
        "target_majors": "",
        "budget_range": "",
        "internships": "",
        "research_experience": "",
        "competitions_projects": "",
        "tutoring_part_time": "",
        "stock_investment": "",
        "career_goals": "",
        "notes": "",
    }


def get_profile() -> dict[str, Any]:
    response = _safe_execute(_client().table("profiles").select("*").eq("user_id", _user_id()).limit(1), "读取个人档案")
    if response.data:
        profile = default_profile()
        profile.update(response.data[0])
        return profile
    return default_profile()


def update_profile(data: dict[str, Any]) -> None:
    payload = _clean_payload(data, PROFILE_FIELDS)
    payload["user_id"] = _user_id()
    _safe_execute(_client().table("profiles").upsert(payload, on_conflict="user_id"), "保存个人档案")


def get_programs(
    search: str = "",
    region: str = "全部",
    category: str = "全部",
    status: str = "全部",
) -> pd.DataFrame:
    df = _select_owned("programs", PROGRAM_FIELDS)
    if df.empty:
        return df
    if search.strip():
        term = search.strip().casefold()
        mask = (
            df["school_name"].fillna("").str.casefold().str.contains(term, regex=False)
            | df["program_name"].fillna("").str.casefold().str.contains(term, regex=False)
            | df["academic_direction"].fillna("").str.casefold().str.contains(term, regex=False)
        )
        df = df[mask]
    if region != "全部":
        df = df[df["region"] == region]
    if category != "全部":
        df = df[df["category"] == category]
    if status != "全部":
        df = df[df["status"] == status]
    df = df.copy()
    df["_deadline_sort"] = pd.to_datetime(df["deadline"], errors="coerce")
    df = df.sort_values(by=["_deadline_sort", "updated_at", "id"], ascending=[True, False, False], na_position="last")
    return df.drop(columns=["_deadline_sort"])


def get_program(program_id: int | str) -> dict[str, Any] | None:
    response = _safe_execute(_client().table("programs").select("*").eq("id", program_id).eq("user_id", _user_id()).limit(1), "读取项目")
    return response.data[0] if response.data else None


def get_program_options() -> pd.DataFrame:
    df = get_programs()
    columns = ["id", "school_name", "program_name", "degree_type", "category", "status"]
    if df.empty:
        return _empty_df(columns)
    return df.sort_values(["school_name", "program_name"], na_position="last")[columns]


def add_program(data: dict[str, Any]) -> int | str:
    return _insert_owned("programs", data, PROGRAM_FIELDS)


def program_import_template_df() -> pd.DataFrame:
    return pd.DataFrame(columns=PROGRAM_TEMPLATE_COLUMNS)


def normalize_program_import(df: pd.DataFrame) -> tuple[list[dict[str, Any]], list[str]]:
    if df.empty:
        return [], ["表格是空的。"]

    column_map = {field: field for field in PROGRAM_FIELDS}
    column_map.update(PROGRAM_IMPORT_COLUMNS)
    normalized = df.rename(columns={column: column_map.get(str(column).strip(), column) for column in df.columns})

    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    numeric_fields = {"tuition", "living_cost", "application_fee"}

    for index, raw_row in normalized.iterrows():
        row_number = int(index) + 2
        data: dict[str, Any] = {}
        for field in PROGRAM_FIELDS:
            value = raw_row.get(field, "")
            if pd.isna(value):
                value = ""
            if isinstance(value, str):
                value = value.strip()
            data[field] = value

        if not any(str(data.get(field) or "").strip() for field in PROGRAM_FIELDS):
            continue

        if not str(data.get("school_name") or "").strip():
            errors.append(f"第 {row_number} 行缺少学校名称。")
        if not str(data.get("program_name") or "").strip():
            errors.append(f"第 {row_number} 行缺少项目名称。")

        for field in numeric_fields:
            data[field] = as_float(data.get(field))

        data["scholarship_available"] = _parse_bool(data.get("scholarship_available"))
        data["deadline"] = _parse_import_date(data.get("deadline"), row_number, errors)
        if not data.get("category"):
            data["category"] = "匹配"
        if not data.get("status"):
            data["status"] = "未开始"

        rows.append(data)

    return rows, errors


def import_programs_from_df(df: pd.DataFrame) -> dict[str, int | list[str]]:
    rows, errors = normalize_program_import(df)
    if errors:
        return {"created": 0, "skipped": 0, "errors": errors}

    existing = get_programs()
    existing_keys = set()
    if not existing.empty:
        for row in existing.to_dict("records"):
            existing_keys.add(_program_key(row))

    created = 0
    skipped = 0
    for row in rows:
        key = _program_key(row)
        if key in existing_keys:
            skipped += 1
            continue
        add_program(row)
        existing_keys.add(key)
        created += 1

    return {"created": created, "skipped": skipped, "errors": []}


def _program_key(row: dict[str, Any]) -> tuple[str, str]:
    return (
        str(row.get("school_name") or "").strip().casefold(),
        str(row.get("program_name") or "").strip().casefold(),
    )


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().casefold()
    return text in {"1", "true", "yes", "y", "是", "有", "有奖学金"}


def _parse_import_date(value: Any, row_number: int, errors: list[str]) -> str | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        errors.append(f"第 {row_number} 行截止日期无法识别，请使用 YYYY-MM-DD。")
        return None
    return parsed.date().isoformat()


def update_program(program_id: int | str, data: dict[str, Any]) -> None:
    _update_owned("programs", program_id, data, PROGRAM_FIELDS)


def delete_program(program_id: int | str) -> None:
    _delete_owned("programs", program_id)


def get_program_filter_values(column: str) -> list[str]:
    if column not in {"region", "category", "status"}:
        return ["全部"]
    df = get_programs()
    if df.empty:
        return ["全部"]
    values = sorted(value for value in df[column].dropna().astype(str).unique().tolist() if value)
    return ["全部"] + values


def get_tasks() -> pd.DataFrame:
    df = _select_owned("application_tasks", TASK_FIELDS)
    if df.empty:
        return df
    df["_deadline_sort"] = pd.to_datetime(df["deadline"], errors="coerce")
    df = df.sort_values(by=["_deadline_sort", "id"], ascending=[True, False], na_position="last")
    return df.drop(columns=["_deadline_sort"])


def get_task(task_id: int | str) -> dict[str, Any] | None:
    response = _safe_execute(_client().table("application_tasks").select("*").eq("id", task_id).eq("user_id", _user_id()).limit(1), "读取任务")
    return response.data[0] if response.data else None


def add_task(data: dict[str, Any]) -> int | str:
    return _insert_owned("application_tasks", data, TASK_FIELDS)


def update_task(task_id: int | str, data: dict[str, Any]) -> None:
    _update_owned("application_tasks", task_id, data, TASK_FIELDS)


def delete_task(task_id: int | str) -> None:
    _delete_owned("application_tasks", task_id)


def get_recent_tasks(days: int = 30) -> pd.DataFrame:
    df = get_tasks()
    if df.empty:
        return df
    deadlines = pd.to_datetime(df["deadline"], errors="coerce").dt.date
    today = date.today()
    end_day = today + timedelta(days=days)
    return df[(deadlines >= today) & (deadlines <= end_day)]


def get_overdue_tasks() -> pd.DataFrame:
    df = get_tasks()
    if df.empty:
        return df
    deadlines = pd.to_datetime(df["deadline"], errors="coerce").dt.date
    return df[(deadlines < date.today()) & (df["status"] != "已完成")]


def get_completed_tasks() -> pd.DataFrame:
    df = get_tasks()
    if df.empty:
        return df
    deadlines = pd.to_datetime(df["deadline"], errors="coerce")
    completed = df[df["status"] == "已完成"].copy()
    completed["_deadline_sort"] = deadlines
    completed = completed.sort_values(by=["_deadline_sort", "id"], ascending=[False, False], na_position="last")
    return completed.drop(columns=["_deadline_sort"])


def get_materials() -> pd.DataFrame:
    df = _select_owned("writing_materials", MATERIAL_FIELDS)
    if df.empty:
        return df
    return df.sort_values(by=["updated_at", "id"], ascending=[False, False])


def get_material(material_id: int | str) -> dict[str, Any] | None:
    response = _safe_execute(_client().table("writing_materials").select("*").eq("id", material_id).eq("user_id", _user_id()).limit(1), "读取文书素材")
    return response.data[0] if response.data else None


def add_material(data: dict[str, Any]) -> int | str:
    return _insert_owned("writing_materials", data, MATERIAL_FIELDS)


def update_material(material_id: int | str, data: dict[str, Any]) -> None:
    _update_owned("writing_materials", material_id, data, MATERIAL_FIELDS)


def delete_material(material_id: int | str) -> None:
    _delete_owned("writing_materials", material_id)


def build_material_summary(material: dict[str, Any]) -> str:
    parts = [
        f"经历名称：{material.get('experience_name') or '未填写'}",
        f"经历类型：{material.get('experience_type') or '未填写'}",
        f"时间：{material.get('period') or '未填写'}",
    ]
    if material.get("background"):
        parts.append(f"背景：{material['background']}")
    if material.get("action"):
        parts.append(f"具体行动：{material['action']}")
    if material.get("result"):
        parts.append(f"结果：{material['result']}")
    if material.get("abilities"):
        parts.append(f"体现能力：{material['abilities']}")
    if material.get("usage"):
        parts.append(f"适用场景：{material['usage']}")
    if material.get("notes"):
        parts.append(f"补充备注：{material['notes']}")

    narrative_lines = []
    if material.get("background"):
        narrative_lines.append(f"在{material['background']}的背景下，")
    if material.get("action"):
        narrative_lines.append(f"我采取的关键行动是：{material['action']}。")
    if material.get("result"):
        narrative_lines.append(f"最终结果是：{material['result']}。")
    if material.get("abilities"):
        narrative_lines.append(f"这段经历可以重点呈现{material['abilities']}。")

    narrative = "".join(narrative_lines).strip()
    if narrative:
        parts.append(f"文书素材表述：{narrative}")
    else:
        parts.append("文书素材表述：当前信息不足，请先补充背景、行动、结果或能力字段。")
    parts.append("说明：以上内容仅整理你已输入的信息，未添加虚构经历。")
    return "\n\n".join(parts)


def get_budgets() -> pd.DataFrame:
    df = _select_owned("budgets", BUDGET_FIELDS)
    if df.empty:
        return df
    for column in [
        "application_fee",
        "score_report_fee",
        "tuition",
        "living_cost",
        "visa_flight_estimate",
        "scholarship_amount",
    ]:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)
    df["computed_total_cost"] = (
        df["application_fee"]
        + df["score_report_fee"]
        + df["tuition"]
        + df["living_cost"]
        + df["visa_flight_estimate"]
    )
    df["net_cost"] = df["computed_total_cost"] - df["scholarship_amount"]
    return df.sort_values(by=["updated_at", "id"], ascending=[False, False])


def get_budget(budget_id: int | str) -> dict[str, Any] | None:
    response = _safe_execute(_client().table("budgets").select("*").eq("id", budget_id).eq("user_id", _user_id()).limit(1), "读取预算")
    return response.data[0] if response.data else None


def add_budget(data: dict[str, Any]) -> int | str:
    data = data.copy()
    data["total_cost"] = calc_total_cost(data)
    return _insert_owned("budgets", data, BUDGET_FIELDS)


def update_budget(budget_id: int | str, data: dict[str, Any]) -> None:
    data = data.copy()
    data["total_cost"] = calc_total_cost(data)
    _update_owned("budgets", budget_id, data, BUDGET_FIELDS)


def delete_budget(budget_id: int | str) -> None:
    _delete_owned("budgets", budget_id)


def budget_stats() -> dict[str, Any]:
    budgets = get_budgets()
    if budgets.empty:
        return {
            "application_stage_cost": 0.0,
            "total_project_cost": 0.0,
            "total_net_cost": 0.0,
            "cheapest": None,
            "highest": None,
            "budgets": budgets,
        }
    application_stage_cost = (
        budgets["application_fee"].fillna(0).sum()
        + budgets["score_report_fee"].fillna(0).sum()
        + budgets["visa_flight_estimate"].fillna(0).sum()
    )
    cheapest = budgets.sort_values("net_cost", ascending=True).iloc[0].to_dict()
    highest = budgets.sort_values("net_cost", ascending=False).iloc[0].to_dict()
    return {
        "application_stage_cost": float(application_stage_cost),
        "total_project_cost": float(budgets["computed_total_cost"].fillna(0).sum()),
        "total_net_cost": float(budgets["net_cost"].fillna(0).sum()),
        "cheapest": cheapest,
        "highest": highest,
        "budgets": budgets,
    }


def get_upcoming_programs(days: int = 60) -> pd.DataFrame:
    df = get_programs()
    if df.empty:
        return df[["id", "region", "school_name", "program_name", "deadline", "category", "status"]]
    deadlines = pd.to_datetime(df["deadline"], errors="coerce").dt.date
    today = date.today()
    end_day = today + timedelta(days=days)
    filtered = df[(deadlines >= today) & (deadlines <= end_day)]
    return filtered[["id", "region", "school_name", "program_name", "deadline", "category", "status"]]


def dashboard_stats() -> dict[str, Any]:
    profile = get_profile()
    programs = get_programs()
    budgets = budget_stats()
    return {
        "profile": profile,
        "program_count": len(programs),
        "recent_tasks": get_recent_tasks(30),
        "upcoming_programs": get_upcoming_programs(60),
        "estimated_budget": float(budgets["total_net_cost"]),
    }


def label_program(row: pd.Series | dict[str, Any]) -> str:
    school = row.get("school_name") or "未命名学校"
    program = row.get("program_name") or "未命名项目"
    degree = row.get("degree_type") or ""
    suffix = f" ({degree})" if degree else ""
    return f"{school} - {program}{suffix}"
