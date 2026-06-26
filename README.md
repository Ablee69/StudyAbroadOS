# StudyAbroadOS

StudyAbroadOS 是一个可部署到云端的个人工作台，用于管理留学申请资料、选校项目、申请时间线、文书素材、预算与奖学金。当前版本使用 Streamlit + Supabase Postgres，支持邮箱密码登录和按用户隔离数据。

## 技术栈

- Python
- Streamlit
- Supabase Auth
- Supabase Postgres
- pandas
- python-docx
- openpyxl
- plotly 可选

## 项目结构

```text
StudyAbroadOS/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── database/
│   ├── __init__.py
│   └── schema.sql
├── services/
│   ├── __init__.py
│   ├── auth.py
│   ├── config.py
│   ├── repository.py
│   ├── supabase_service.py
│   └── ui.py
├── pages/
│   ├── 1_首页看板.py
│   ├── 2_个人申请档案.py
│   ├── 3_选校与项目库.py
│   ├── 4_申请时间线.py
│   ├── 5_文书素材库.py
│   ├── 6_预算与奖学金.py
│   └── 7_导出中心.py
├── exports/
└── templates/
```

## 云端数据库

项目不再依赖本地 SQLite 保存业务数据。所有业务数据通过 Supabase 写入 Postgres，并使用 `user_id` 与 Supabase Auth 用户绑定。

已覆盖的数据表：

- `profiles`：个人申请档案
- `programs`：选校与项目库
- `application_tasks`：申请时间线
- `writing_materials`：文书素材
- `budgets`：预算与奖学金
- `students`、`courses`、`mistakes`、`feedbacks`、`incomes`：家教工作台扩展表

选校数据库不会预置学校或项目要求，避免虚构信息。你可以在“选校与项目库”里手动新增，也可以下载 Excel 模板，把从官网核实后的学校/项目资料批量导入。导入时可以选择“共享给所有登录用户”，这样学校数据库会成为公共选校库；个人申请档案、任务、文书素材和预算仍然只对当前账号可见。建议每条项目都填写“信息来源链接”和“核验日期”，方便后续回到官网二次确认。

建表 SQL 位于：

```text
database/schema.sql
```

在 Supabase Dashboard 中打开 SQL Editor，复制并运行该文件内容。SQL 已启用 Row Level Security，并为每张表添加只允许 `auth.uid() = user_id` 的查询、插入、更新和删除策略。

如果你已经建过旧版本数据库，只需要在 Supabase SQL Editor 运行：

```sql
alter table public.programs add column if not exists source_url text;
alter table public.programs add column if not exists verified_date date;
alter table public.programs add column if not exists is_shared boolean not null default false;
```

同样的升级 SQL 也保存在：

```text
database/20260627_add_program_source_fields.sql
database/20260627_make_programs_shareable.sql
```

如果已经导入了希望公开给所有登录用户查看的学校项目，可以在 Supabase SQL Editor 额外运行：

```sql
update public.programs
set is_shared = true
where source_url is not null and verified_date is not null;
```

登录页默认勾选“在这台设备保持登录”。这会在当前浏览器保存 Supabase 登录 token，刷新页面一般不需要重新输入邮箱密码；点击“退出登录”会清除本地登录状态。

## 本地运行

建议使用 Python 3.10-3.12。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

复制 secrets 示例：

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

编辑 `.streamlit/secrets.toml`，填入你自己的 Supabase 配置：

```toml
SUPABASE_URL = "https://your-project-ref.supabase.co"
SUPABASE_KEY = "your-supabase-anon-key"
DATABASE_URL = "postgresql://postgres.your-project-ref:your-password@aws-0-region.pooler.supabase.com:6543/postgres"
```

启动应用：

```bash
streamlit run app.py
```

## Supabase 设置步骤

1. 进入 [Supabase](https://supabase.com/) 创建免费项目。
2. 在 Project Settings > API 中复制 `Project URL` 到 `SUPABASE_URL`。
3. 复制 `anon public` key 到 `SUPABASE_KEY`。
4. 在 Project Settings > Database 中复制连接字符串到 `DATABASE_URL`。
5. 在 Authentication > Providers 中确认 Email provider 已开启。
6. 在 SQL Editor 运行 `database/schema.sql`。
7. 回到应用，用邮箱密码创建账号或在 Supabase Authentication 中手动添加用户。

## Streamlit Community Cloud 部署

1. 将项目推送到 GitHub。
2. 确认 `.gitignore` 已忽略 `.streamlit/secrets.toml`、`.env`、本地数据库和导出文件。
3. 打开 [Streamlit Community Cloud](https://share.streamlit.io/)。
4. 选择 GitHub 仓库，入口文件填写 `app.py`。
5. 在 App settings > Secrets 中填写：

```toml
SUPABASE_URL = "https://your-project-ref.supabase.co"
SUPABASE_KEY = "your-supabase-anon-key"
DATABASE_URL = "postgresql://postgres.your-project-ref:your-password@aws-0-region.pooler.supabase.com:6543/postgres"
```

6. 部署后访问 Streamlit 提供的网址，使用邮箱密码登录。

## 安全说明

- 不要把真实 `.streamlit/secrets.toml`、`.env`、数据库密码或 API Key 提交到 GitHub。
- 代码只读取 `SUPABASE_URL`、`SUPABASE_KEY`、`DATABASE_URL`，不会明文写死密钥。
- 所有业务表都有 `user_id` 字段，代码查询会按 `user_id` 过滤，数据库 RLS 也会再次校验。
- 删除操作需要先勾选确认。
- 导出功能只读取当前登录用户的数据。
- 项目不包含示例学生隐私、家长联系方式或申请资料。
- 项目不内置学校和项目要求；你的学校数据库来自手动录入或 Excel/CSV 导入。

## 常见报错排查

### 1. 页面提示未配置 Supabase

检查本地 `.streamlit/secrets.toml` 或 Streamlit Cloud Secrets 是否包含：

```toml
SUPABASE_URL = "..."
SUPABASE_KEY = "..."
DATABASE_URL = "..."
```

### 2. 登录失败：Invalid login credentials

确认邮箱和密码正确；如果开启了邮箱确认，请先完成确认；也可以在 Supabase Dashboard > Authentication 中手动创建用户。

### 3. 表不存在或 relation does not exist

说明还没有运行建表 SQL。进入 Supabase SQL Editor，运行 `database/schema.sql`。

### 4. new row violates row-level security policy

通常是 RLS 策略未正确创建，或没有登录就尝试写入。重新运行 `database/schema.sql`，并确认应用中已经登录。

### 5. 本地 pip 安装 pandas 失败

不要使用 Python 3.15 alpha。建议安装 Python 3.10-3.12 后重新创建虚拟环境。

### 6. Streamlit Cloud 部署后找不到依赖

确认 `requirements.txt` 已提交，并包含 `streamlit`、`supabase`、`pandas`、`python-docx`、`openpyxl`。

### 7. 导出内容为空

导出功能只导出当前登录用户的数据。请确认你登录的是录入数据时使用的同一个邮箱。
