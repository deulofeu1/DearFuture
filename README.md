# DearFuture

> 把今天的担忧寄给未来。Reality will write back.

DearFuture 是一个可公开使用的异步 AI Agent 产品。用户提交一个关于未来的问题，系统将它转换成可验证声明；到达约定日期后，Agent 搜索现实证据、给出判断并生成未来回信。通过隐私审核的问题会匿名展示在公开的 Future Wall。

## 产品能力

- 可直接使用的响应式首页、问题提交表单和 Future Wall
- 中英双语界面，语言选择会保存在浏览器中
- 每个公开问题都有独立、可分享的详情页
- DeepSeek V4 Flash 生成结构化声明、验证标准和内容审核结果
- 到期后通过 Web Search 收集证据并判断预测结果
- 用户用“清晨、正午、午后、黄昏、入夜”选择回信时刻
- 应用内置轻量调度器，启动后每小时整点巡一次信箱
- `happened`、`partially_happened`、`did_not_happen`、`uncertain` 四种结论
- 模型临时失败时最多重试三次，不会错误地把失败当作结论
- 预留可选邮件通知能力，当前网页版本暂不收集邮箱
- SQLite WAL 模式、外键、索引、事务和 Alembic 迁移
- API 响应永远不包含用户邮箱
- 信件默认匿名进入慢递墙，敏感内容会被隐私审核拦截

## 核心流程

### Intake Graph

```text
Normalize Input → Plan Claim → Moderate Publicity → Build Verification Plan
```

它负责把自由文本转换为可以在未来客观检查的数据。DeepSeek 不可用时会使用保守的本地 fallback，因此提交功能不会完全依赖外部模型。

### Resolution Graph

```text
Research Evidence
       ↓
  Enough evidence?
   ↙      ↓       ↘
失败重试  正常判断  无法确定
```

它在问题到期后调用搜索能力，要求模型返回结构化证据。只有调用成功后才会保存结论并生成未来回信。

## 技术栈

- **FastAPI**：网页服务、REST API、数据校验和自动接口文档
- **LangGraph**：两条有状态、可分支的 Agent 工作流
- **[DeepSeek V4 Flash](https://api-docs.deepseek.com/guides/responses_api/)**：声明规划、搜索研究、判断和信件生成
- **SQLAlchemy**：数据库模型、关系查询和事务管理
- **SQLite**：单实例正式数据库，开启 WAL、外键和 busy timeout
- **Alembic**：版本化数据库结构
- **SMTP**：可选结果邮件，无需绑定某一家邮件服务商
- **HTML / CSS / JavaScript**：无前端构建链，页面可以直接学习和修改

## 数据模型

```text
Question 1 ─── N Evidence
    │
    └───────── N Notification
```

- `questions`：问题、邮箱、声明、验证计划、状态、结论和未来回信
- `evidence`：来源标题、URL、摘要、发布时间和抓取时间
- `notifications`：邮件是否发送、失败原因和发送时间

## 本地运行

项目使用 [uv](https://docs.astral.sh/uv/) 管理 Python 环境。

```bash
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload
```

在 `.env` 中填写：

```env
DEEPSEEK_API_KEY=your-key
```

打开：

- 产品首页：<http://127.0.0.1:8000>
- API 文档：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/health>

应用启动时会自动执行 Alembic 迁移并创建 `dear_future.sqlite3`。`.env` 和数据库文件均已被 Git 忽略。

## 自动到期验证

本地启动 FastAPI 后，内置调度器会立即检查一次到期问题，之后默认每小时整点巡一次信箱：

```env
SCHEDULER_ENABLED=true
SCHEDULER_INTERVAL_SECONDS=3600
```

因此本地使用不需要再单独启动 Worker。

## 独立 Worker

部署平台已经提供 Cron 时，可以设置 `SCHEDULER_ENABLED=false`，然后由平台定期运行：

手动运行：

```bash
uv run dear-future-worker
```

也可以限制单次处理数量：

```bash
uv run dear-future-worker --limit 5
```

部署后让平台 Cron 每小时执行一次即可。Worker 只处理已经到期的问题；失败任务会在六小时后重试，最多三次。

## 可选邮件配置

当前网页不收集邮箱，回信直接出现在慢递墙和详情页。邮件模块作为以后扩展保留；需要恢复时，建议使用自己的域名配合事务邮件服务（例如 Resend）。

先在 Resend 添加并验证一个发信域名或子域名，例如 `letters.yourdomain.com`，创建 API Key，然后配置：

```env
MAIL_ENABLED=true
RESEND_API_KEY=re_your_api_key
MAIL_FROM="DearFuture Slow Mail <hello@letters.yourdomain.com>"
APP_BASE_URL=https://your-domain.com
```

应用优先通过 Resend HTTPS API 发信，因此可以在 Railway 的 Free、Trial 或 Hobby 方案运行。SMTP 仅作为备用方案保留。

发件地址不一定需要对应一个真实邮箱，但建议至少准备一个可以接收回复的地址或邮件转发规则。请勿把 API Key、SMTP 密码或 `.env` 提交到 GitHub。

重启应用后，可以立即发送一封试投信：

```bash
uv run dear-future-mail-test your@email.com
```

## API

| Method | Path                         | Purpose                |
| ------ | ---------------------------- | ---------------------- |
| `POST` | `/api/questions`             | 提交问题               |
| `GET`  | `/api/public/questions`      | Future Wall 列表       |
| `GET`  | `/api/questions/{public_id}` | 公开问题详情           |
| `GET`  | `/api/public/stats`          | 首页统计               |
| `GET`  | `/health`                    | 服务、数据库和配置状态 |

API 仍兼容可选邮箱字段，方便以后恢复邮件通知。

## 测试与代码检查

```bash
uv run pytest
uv run ruff check app tests migrations
uv run ruff format --check app tests migrations
```

测试覆盖隐私审核、结构化声明、证据分支、API 隐私、公开墙、统计、到期筛选、验证成功和失败重试。

## 项目结构

```text
app/
├── main.py       # FastAPI 路由与网页入口
├── graph.py      # Intake / Resolution LangGraph
├── llm.py        # DeepSeek 结构化调用
├── models.py     # SQLAlchemy 三表模型
├── schemas.py    # API 输入输出契约
├── services.py   # 业务流程、事务与重试
├── email.py      # Resend API 与 SMTP 通知适配器
├── db.py         # SQLite 和迁移初始化
├── worker.py     # Cron 入口
└── static/       # 产品页面
```

## 部署边界

SQLite 很适合 DearFuture 当前的单实例产品形态：读取多、写入相对少，部署和备份也很简单。推荐先用一个 Railway Web Service 同时运行 FastAPI 和内置调度器，不必额外拆分 Cron 或 Worker。

上线步骤：

1. 初始化 Git 仓库并把代码推送到 GitHub。
2. 在 Railway 中从 GitHub 仓库创建一个服务。
3. 添加持久化 Volume，并挂载到 `/data`。
4. 设置 `DATABASE_URL=sqlite:////data/dear_future.sqlite3`。
5. 设置 `SCHEDULER_ENABLED=true`，并保持一个运行实例，避免重复执行到期任务。
6. 配置 DeepSeek 和 `APP_BASE_URL`，并保持 `MAIL_ENABLED=false`。
7. Railway 会自动使用仓库中的 `Dockerfile` 构建并启动应用。
8. 在服务设置中把健康检查路径设置为 `/health`。
9. 在 Networking 中生成 Railway 测试域名，再把该地址填写到 `APP_BASE_URL` 并重新部署。
10. 确认完整流程后，再选择是否绑定自己的网页域名。

公开发布前还应补充：隐私政策、提交频率限制或验证码、邮件订阅/退订说明，以及 SQLite 数据库的定期备份。

只有当产品需要多实例横向扩展或出现持续高并发写入时，才需要迁移到 PostgreSQL。
