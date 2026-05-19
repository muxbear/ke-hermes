# ke-hermes

通用智能体服务平台，前后端分离架构。

## 目录

```
ke-hermes/
├── backend/    # Python FastAPI + DeepAgents 智能体后端
├── frontend/   # Vue 3 + Vite + Element Plus 前端
└── docs/       # 项目文档
```

## 环境与启动


| 项目       | 包管理                 | 启动命令                                               |
| -------- | ------------------- | -------------------------------------------------- |
| backend  | uv (pyproject.toml) | `cd backend && uv run uvicorn server:app --reload` |
| frontend | npm                 | `cd frontend && npm run dev`                       |


- 前端默认 `http://localhost:5173`，`/api` 代理到后端 `http://127.0.0.1:8000`
- 全局 gitignore 已忽略 `.env`、`node_modules/`、`.venv/` 等

## 规范

- 前端组件/函数/变量命名遵循各子目录 CLAUDE.md 约定
- 后端遵循 ruff (pycodestyle + pyflakes + isort + pydocstyle) 和 mypy strict
- 提交前确保通过 lint 和测试

