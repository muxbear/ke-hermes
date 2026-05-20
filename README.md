<p align="center">
  <h1 align="center">⚡ Ke Hermes</h1>
  <p align="center"><strong>General-Purpose AI Agent Service</strong></p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python">
  <img src="https://img.shields.io/badge/vue-3.5-brightgreen" alt="Vue">
  <img src="https://img.shields.io/badge/fastapi-0.100+-teal" alt="FastAPI">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

[中文文档](README.zh-CN.md)

## Overview

Ke Hermes is a general-purpose AI agent web application with a separated frontend/backend architecture. It provides an intelligent conversational interface backed by DeepAgents (LangGraph) and DeepSeek LLM, featuring real-time streaming responses, user authentication, and third-party OAuth login.

## Features

- **AI Chat** — Real-time SSE streaming conversation with the DeepSeek LLM, plus non-streaming fallback
- **Authentication** — JWT-based login with bcrypt password hashing and RSA-2048 encrypted password transmission
- **Registration** — Phone (SMS) and email registration flows
- **OAuth Login** — GitHub, Google, and WeChat third-party login
- **Captcha** — Slider-based verification code
- **Rate Limiting** — Configurable login failure lockout and SMS daily limits
- **i18n** — Multi-language UI support (vue-i18n)

## Architecture

```
┌─────────────────────────────────────────┐
│              Frontend (Vue 3)            │
│    Element Plus + Pinia + Vue Router     │
│    localhost:5173                        │
└──────────────┬──────────────────────────┘
               │ /api (Vite proxy)
┌──────────────▼──────────────────────────┐
│            Backend (FastAPI)             │
│    LangGraph + DeepSeek + SQLAlchemy     │
│    localhost:8000                        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│        LLM: DeepSeek (deepseek-v4-pro)   │
│    Embeddings: DashScope                 │
│    Storage: SQLite / PostgreSQL          │
│    Cache: Redis (optional)               │
└─────────────────────────────────────────┘
```

## Project Structure

```
ke-hermes/
├── frontend/          # Vue 3 + Vite + Element Plus
│   ├── src/
│   │   ├── views/     # Page components
│   │   ├── components/# Reusable components
│   │   ├── composables/# Composition functions
│   │   ├── stores/    # Pinia stores
│   │   ├── services/  # API layer (Axios + SSE)
│   │   ├── router/    # Vue Router config
│   │   ├── types/     # TypeScript types
│   │   └── locales/   # i18n language packs
│   └── tests/
├── backend/           # Python FastAPI + LangGraph
│   ├── src/
│   │   ├── server.py  # App entry point
│   │   ├── api/       # Route modules (auth/chat/captcha/oauth/sms)
│   │   ├── agent/     # LangGraph agent (graph/config/models/tools)
│   │   ├── core/      # Core utilities (security/store/response)
│   │   └── db/        # Database engine and ORM models
│   └── tests/
└── docs/              # Project documentation
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- uv (Python package manager)

### Backend

```bash
cd backend
cp .env.example .env     # Edit .env with your API keys
uv sync                  # Install dependencies
uv run uvicorn server:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` — the dev server proxies `/api` requests to the backend.

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `DEEPSEEK_API_KEY` | DeepSeek API key | Yes |
| `DEEPSEEK_MODEL` | Model name (default: `deepseek-v4-pro`) | No |
| `DEEPSEEK_BASE_URL` | API base URL | No |
| `DATABASE_URL` | Database URL (SQLite: `sqlite+aiosqlite:///ke-hermes.db`) | No |
| `REDIS_URL` | Redis URL (falls back to in-memory store) | No |
| `JWT_SECRET_KEY` | JWT signing key (auto-generated if empty) | No |

## Scripts

| Directory | Command | Description |
|---|---|---|
| backend | `uv run pytest` | Run tests |
| backend | `uv run ruff check .` | Lint |
| backend | `uv run ruff format .` | Format code |
| frontend | `npm run dev` | Start dev server |
| frontend | `npm run build` | Production build |
| frontend | `npm run test` | Run tests |
| frontend | `npm run lint` | Lint |

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend Framework | Vue 3 + TypeScript |
| UI Library | Element Plus |
| State Management | Pinia |
| Build Tool | Vite 5 |
| Backend Framework | FastAPI |
| Agent Framework | DeepAgents / LangGraph |
| LLM | DeepSeek (deepseek-v4-pro) |
| Embeddings | DashScope (text-embedding-v4) |
| Database | SQLAlchemy async + SQLite / PostgreSQL |
| Cache | Redis (with in-memory fallback) |
| Auth | JWT (HS256) + bcrypt + RSA-2048 |
| Testing | pytest + vitest |

## License

[MIT](LICENSE)
