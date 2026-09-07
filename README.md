# DearFuture 🐌

> 把今天的担忧，寄给未来。现实会慢慢回信。<br>
> Send today's worries to the future. Reality will write back.

<p>
  <a href="https://dearfuture-production.up.railway.app/">🌐 在线体验 / Live Demo</a>
  ·
  <a href="https://github.com/deulofeu1/DearFuture">💻 GitHub</a>
</p>

## 中文介绍

DearFuture 是一只寄往未来的慢递蜗牛。

你可以写下一个关于未来的问题，例如：

> “一个月以后，我现在担心的工作变化真的发生了吗？”

选择一个未来日期和时刻后，DearFuture 会把问题整理成可以验证的声明。约定时间到达后，异步 Agent 会搜索现实中的公开证据，判断事情后来是否发生，并生成一封来自未来的回信。

现在就可以打开[在线体验](https://dearfuture-production.up.railway.app/)：

1. 写下一件你正在担心的事；
2. 选择未来的日期和“清晨 / 正午 / 午后 / 黄昏 / 入夜”；
3. 把它交给慢递蜗牛；
4. 之后回到详情页或慢递信墙，看看现实带回了什么答案。

### 产品特点

- 🌱 把模糊的焦虑转换成可以在未来检查的具体声明
- 🐌 任务不会要求用户一直在线，到期后由定时调度器自动触发
- 🔎 使用公开证据，而不是只保存模型的一句猜测
- ✉️ 生成一封温和的未来回信，结果展示在详情页和慢递信墙
- 🌏 支持中文 / English 页面切换
- 🧭 每个公开问题都有独立的可分享链接
- 🛡️ 公开展示默认匿名，并对明显的个人敏感内容进行审核

### 当前版本说明

当前网页版本暂时不收集邮箱，也不会发送邮件。验证完成后，结果会出现在问题详情页和慢递信墙中。邮件通知模块已经预留，未来可以接入 Resend 等事务邮件服务。

### 结果状态

| 状态 | 含义 |
| --- | --- |
| `scheduled` | 信件已经寄出，正在等待约定的未来时刻 |
| `verifying` | 慢递蜗牛正在寻找现实证据 |
| `resolved` | 验证完成，回信已经送达 |
| `retry_pending` | 服务重启中断了验证，等待下一次巡检恢复 |
| `uncertain` | 公开证据不足，未来暂时没有给出明确答案 |

---

## English

DearFuture is a slow-mail service for worries about the future.

Write down a future-facing question such as:

> “Will the change I am worried about at work really happen within a month?”

Choose a future date and a gentle time of day. DearFuture turns the question into a testable claim. When the date arrives, an asynchronous AI agent searches public evidence, evaluates what actually happened, and writes a warm letter back to the past you.

Try it now at the [Live Demo](https://dearfuture-production.up.railway.app/):

1. Write down something you are worried about;
2. Choose a future date and time of day;
3. Send it to the slow-mail snail;
4. Return to the detail page or the Slow Mail Wall to see what reality brought back.

### Product highlights

- 🌱 Turns vague worries into concrete, verifiable future claims
- 🐌 Runs asynchronously, so users do not need to stay online
- 🔎 Grounds the final judgment in public evidence
- ✉️ Generates a warm future letter and publishes the result on the detail page and wall
- 🌏 Bilingual Chinese / English interface
- 🧭 Shareable public detail page for every approved question
- 🛡️ Anonymous public display with basic personal-content moderation

### Current version

The current web version does not collect email addresses or send email notifications. Completed results appear on the question detail page and the Slow Mail Wall. An email adapter is kept for a future Resend integration.

### 管理入口 / Admin access

部署者可以访问 `/admin` 管理公开信件。后台使用 `ADMIN_TOKEN` 保护；“移除”是可恢复的软删除，不会物理删除数据库记录。管理页面不会展示邮箱。请在本地 `.env` 或 Railway Variables 中设置一个随机长口令，不要提交到 GitHub。

The deployer can open `/admin` to manage public letters. The page is protected by `ADMIN_TOKEN`; removing a letter is a reversible soft delete, and the management view never exposes email addresses. Set a long random token in local `.env` or Railway Variables, and never commit it to GitHub.

---

## How the product works

```text
User writes a worry
        ↓
FastAPI validates the request
        ↓
Intake Graph
  normalize → plan claim → privacy check → build plan
        ↓
SQLite stores the task and its scheduled time
        ↓
Hourly Scheduler finds due tasks
        ↓
Resolution Graph
  research evidence → route by evidence quality → judge → write letter
        ↓
SQLite stores the verdict, evidence and future letter
        ↓
The Slow Mail Wall shows the result
```

The central idea is a **long-running asynchronous Agent workflow**: the initial HTTP request finishes quickly, while the meaningful research work is persisted and resumed later by a scheduled background process.

## Technology highlights

- **FastAPI**：网页服务、REST API、请求校验和自动 OpenAPI 文档
- **LangGraph**：用 State、Node 和 Edge 编排两个有状态 Agent 工作流
- **DeepSeek V4 Flash**：生成可验证声明、搜索研究结果、判断结论和未来回信
- **Pydantic**：约束 API 输入和 LLM JSON 输出，降低模型文本的不确定性
- **SQLAlchemy + SQLite**：保存问题、状态、证据和任务重试信息
- **Alembic**：用版本化迁移管理数据库结构变化
- **Asyncio Scheduler**：在 08:05、12:05、18:05、21:05 检查到期任务，不需要用户保持在线
- **Retry and recovery**：模型失败与证据不足分开处理，失败任务最多重试三次
- **Privacy by design**：公开响应不包含邮箱，模型审核结合本地敏感信息规则
- **Railway + Dockerfile**：单个轻量 Web Service，使用 Volume 持久化 SQLite

## Architecture

The project has two LangGraph workflows.

### 1. Intake Graph

```text
START
  ↓
normalize_input
  ↓
plan_claim ── DeepSeek or local fallback
  ↓
moderate_publicity ── model eligibility + local rules
  ↓
build_verification_plan
  ↓
END
```

It converts free-form text into:

- a category;
- a concrete claim;
- one to five verification criteria;
- a moderation decision;
- a readable verification plan.

### 2. Resolution Graph

```text
START
  ↓
research_evidence
  ↓
route_research
  ├── enough evidence → finalize_resolution
  ├── insufficient evidence → finalize_inconclusive
  └── model failure → mark_research_failed
```

Only a valid, structured model result is persisted as a resolved outcome. Insufficient evidence becomes `uncertain`; a failed model call is retried immediately up to three times instead of being misreported as a conclusion.

## Data model

```text
Question 1 ─── N Evidence
    │
    └───────── N Notification
```

- `questions`：原始问题、声明、验证计划、时间、状态、结论和未来回信
- `evidence`：来源标题、URL、摘要、发布时间和抓取时间
- `notifications`：未来邮件通知的发送状态和错误信息

The public URL uses a UUID `public_id` instead of exposing the sequential database ID. Public API responses use Pydantic response models and never include the email field.

## Run locally

The project uses [uv](https://docs.astral.sh/uv/) to manage the Python environment.

```bash
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload
```

Set the DeepSeek key in `.env`:

```env
DATABASE_URL=sqlite:///./dear_future.sqlite3
DEEPSEEK_API_KEY=your-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
ADMIN_TOKEN=your-long-random-admin-token
SCHEDULER_ENABLED=true
SCHEDULER_CHECK_TIMES=08:05,12:05,18:05,21:05
SCHEDULER_TIMEZONE=Asia/Shanghai
MAIL_ENABLED=false
```

Local pages:

- Product: <http://127.0.0.1:8000>
- API docs: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

The application applies Alembic migrations during startup. The local SQLite database, `.env` and virtual environment are ignored by Git.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/questions` | Submit a future question |
| `GET` | `/api/public/questions` | List the Slow Mail Wall |
| `GET` | `/api/questions/{public_id}` | Read a public question detail |
| `GET` | `/api/public/stats` | Read public wall statistics |
| `GET` | `/health` | Check service, database and configuration |
| `GET` | `/admin` | Open the management page |
| `GET` | `/api/admin/questions` | List questions (Bearer token required) |
| `DELETE` | `/api/admin/questions/{public_id}` | Hide a question (Bearer token required) |
| `POST` | `/api/admin/questions/{public_id}/restore` | Restore a hidden question (Bearer token required) |

Example request:

```bash
curl -X POST http://127.0.0.1:8000/api/questions \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "AI 会在一个月内显著改变初级开发者的工作方式吗？",
    "check_at": "2026-10-06T07:00:00+00:00"
  }'
```

## Deployment

The public demo is deployed on Railway:

<https://dearfuture-production.up.railway.app/>

For the current single-instance SQLite deployment:

1. Connect the GitHub repository to a Railway service.
2. Attach a persistent Volume with mount path `/data`.
3. Add the following service variables:

```env
DATABASE_URL=sqlite:////data/dear_future.sqlite3
DEEPSEEK_API_KEY=your-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
APP_BASE_URL=https://dearfuture-production.up.railway.app
ADMIN_TOKEN=your-long-random-admin-token
SCHEDULER_ENABLED=true
SCHEDULER_CHECK_TIMES=08:05,12:05,18:05,21:05
 SCHEDULER_TIMEZONE=Asia/Shanghai
MAIL_ENABLED=false
```

4. Generate a Railway public domain if the service does not already have one.
5. Set the health check path to `/health`.
6. Keep one running instance so the in-process scheduler does not claim the same task twice. The scheduler checks at 08:05, 12:05, 18:05, and 21:05 in Asia/Shanghai by default.

SQLite is intentional here: the product has low write volume and a single service. If the product grows to multiple instances or high concurrent writes, move the database to PostgreSQL and move scheduled verification to a dedicated Worker or queue.

## Project structure

```text
app/
├── main.py       # FastAPI routes, lifespan and health check
├── graph.py      # Intake and Resolution LangGraph workflows
├── llm.py        # DeepSeek client and Pydantic output models
├── models.py     # SQLAlchemy Question, Evidence and Notification models
├── schemas.py    # API input/output contracts and datetime serialization
├── services.py   # Business flow, transactions, retries and persistence
├── scheduler.py  # Hourly in-process scheduler
├── worker.py     # Optional one-shot worker entry point
├── db.py         # SQLite engine, PRAGMA settings and migrations
└── static/       # Bilingual HTML, CSS and JavaScript frontend

migrations/
└── versions/     # Alembic database schema history

tests/            # API, graph, LLM, email and worker tests
```

## Tests and code quality

```bash
uv run pytest
uv run ruff check app tests migrations
uv run ruff format --check app tests migrations
```

The tests cover input validation, public-content moderation, structured Agent output, evidence branches, API privacy, due-task selection, successful resolution and retry behavior.

## License

This project is released under the MIT License. See [LICENSE](LICENSE).

---

## 中文技术补充

如果你想学习这个项目的实现细节，建议按下面顺序阅读源码：

```text
app/main.py
  → app/schemas.py
  → app/services.py
  → app/graph.py
  → app/llm.py
  → app/models.py
  → app/scheduler.py
```

重点理解四个问题：

1. FastAPI 如何把 HTTP 请求交给业务层；
2. LangGraph 如何通过 State、Node 和 Edge 组织 Agent；
3. SQLAlchemy 如何把 Python 对象保存为关系数据；
4. Scheduler 如何让任务在未来继续执行。

更完整的本地学习手册位于 `docs/dear-future-learning-guide.html`，该文件仅用于本地学习，不随本 README 发布。
