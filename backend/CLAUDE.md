# ke-hermes Backend

Python 智能体后端，基于 FastAPI + LangGraph。

## 技术栈

- **Web**: FastAPI + Uvicorn
- **Agent**: DeepAgents LangGraph (`langgraph>=1.0`)
- **LLM**: DeepSeek (deepseek-v4-pro)
- **Embeddings**: DashScope (text-embedding-v4)
- **数据库**: SQLAlchemy async + aiosqlite (开发) / 可替换为 PostgreSQL
- **认证**: JWT (HS256) + bcrypt + RSA-2048 密码加密传输
- **缓存**: Redis (可选，自动降级到内存 MemoryStore)
- **包管理**: uv (pyproject.toml)

## 目录结构

```
backend/src/
├── server.py          # FastAPI 入口，lifespan 中初始化 DB 和 Store
├── api/               # 路由层
│   ├── __init__.py    # 聚合所有子路由
│   ├── deps.py        # 依赖注入 (get_db, get_store, get_client_ip)
│   ├── agent/         # 对话/智能体接口
│   ├── auth/          # 登录/注册/Token 刷新
│   ├── captcha/       # 滑块验证码
│   ├── oauth/         # 第三方登录 (GitHub/Google/微信)
│   └── sms/           # 短信验证码
├── core/              # 核心模块
│   ├── security.py    # JWT 签发/解码、bcrypt 加解密、RSA 密钥对
│   ├── store.py       # KeyValueStore 抽象 (Redis + MemoryStore 降级)
│   └── response.py    # 统一响应格式 ApiResponse
├── agent/             # LangGraph agent
│   ├── graph.py       # 图定义
│   ├── config/        # 配置类 (Settings, 从 .env 读取)
│   ├── tools/         # agent 工具
│   ├── models/        # 数据模型
│   └── utils/         # agent 工具函数
└── db/                # 数据库
    ├── engine.py      # 异步引擎 + get_db + init_db
    ├── base.py        # DeclarativeBase
    └── models/        # ORM 模型
```

## 环境变量 (`.env`)

参见 `.env.example`，关键变量：

- `DEEPSEEK_API_KEY` / `DEEPSEEK_MODEL` / `DEEPSEEK_BASE_URL` — LLM 配置
- `DATABASE_URL` — 数据库连接 (SQLite: `sqlite+aiosqlite:///ke-hermes.db`)
- `JWT_SECRET_KEY` — JWT 密钥 (留空则自动生成持久化到 `.jwt_secret`)
- `REDIS_URL` — Redis 连接 (不可用时自动降级)
- `RSA_KEY_SIZE` — 密码加密 RSA 密钥长度 (默认 2048)

## 常用命令

```bash
cd backend
uv sync                    # 安装依赖
uv run python run.py       # 启动开发服务器 (含热重载)
uv run pytest               # 运行测试
uv run ruff check .         # lint
uv run ruff format .        # 格式化
uv run mypy --strict src/   # 类型检查
```

## 代码规范

- **命名**: snake_case (文件/函数/变量), PascalCase (类)
- **Lint**: ruff (pycodestyle + pyflakes + isort + pydocstyle)
- **类型**: mypy strict 模式, 所有函数必须标注返回类型
- **Docstring**: Google 风格, 首行为祈使句
- **导入顺序**: 标准库 → 第三方 → 本地 (ruff I 自动管理)
- **路由**: 每个功能模块独立子目录, 通过 `api/__init__.py` 聚合

