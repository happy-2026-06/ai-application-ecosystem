# AI Applications Collection

A collection of 8 AI-powered full-stack applications built with **Vue 3 + FastAPI + LangChain + DeepSeek**.

## Projects

| # | Project | Type | Description |
|---|---------|------|-------------|
| ① | RAG Customer Service | C-end | Enterprise knowledge-base Q&A for e-commerce |
| ② | AI Content Assistant | C-end | Viral titles, video scripts, social media copywriting |
| ③ | Short Video Script Studio | C-end | Storyboard scripts, TTS voiceover, subtitle export |
| ④ | Digital Asset Management | B-end | Asset upload, AI auto-tagging, image search |
| ⑤ | Sales Training System | B-end | AI role-play customer scenarios, multi-dimension scoring |
| ⑥ | Data Center Platform | Middle-platform | Data ingestion, cleaning, annotation, quality reports |
| ⑦ | Multi-Agent Collaboration | Middle-platform | Multi-agent task orchestration with SSE streaming |
| ⑧ | Model Fine-Tuning Platform | Middle-platform | QLoRA fine-tuning, A/B comparison, model deployment |

## Tech Stack

- **Frontend**: Vue 3 + TypeScript + Naive UI + Pinia + Vite
- **Backend**: Python FastAPI + SQLAlchemy 2.0 (async)
- **AI**: LangChain + DeepSeek API + ChromaDB
- **Data**: SQLite (WAL mode, dev)
- **Cross-project**: X-Internal-Call shared-secret data flywheel

## Quick Start (Local Dev)

### Prerequisites

- Python 3.11+
- Node.js 18+
- DeepSeek API Key ([get one here](https://platform.deepseek.com/api_keys))

### Launch All Backends

```bash
# 1. Configure API keys for each project (files are git-ignored)
#    Each backend/.env already contains the key locally.
#    For a fresh clone, copy .env.example to .env and add your key:
#   01-RAG智能客服系统/backend/.env.example → .env
#   ... (repeat for all 8 projects)

# 2. One-click start all 8 backends (Windows)
start-all-backends.bat

# Or start a single project
cd 01-RAG智能客服系统
start.bat
```

### Port Mapping

| Project | Backend | Frontend |
|---------|:------:|:--------:|
| ① RAG Customer Service | 8101 | 3001 |
| ② Content Assistant | 8202 | 3002 |
| ③ Script Studio | 8000 | 3000 |
| ④ Asset Management | 8400 | 3004 |
| ⑤ Sales Training | 8505 | 3005 |
| ⑥ Data Center | 8606 | 3006 |
| ⑦ Multi-Agent | 8707 | 3007 |
| ⑧ Fine-Tuning | 8808 | 3008 |

### Run a Single Project (Dev Mode)

```bash
# Example: Project ① RAG Customer Service
cd 01-RAG智能客服系统
# Terminal 1 - Backend
cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8101
# Terminal 2 - Frontend
cd frontend && npm run dev
```

## Project Structure

```
ai-applications/
├── 01-RAG智能客服系统/         # RAG Customer Service
├── 02-AI自媒体内容助手/        # Content Assistant
├── 03-AI短视频脚本工坊/        # Script Studio
├── 04-AI素材管理平台/          # Asset Management
├── 05-AI销售培训系统/          # Sales Training
├── 06-AI数据中心平台/          # Data Center
├── 07-MCP多智能体协作平台/      # Multi-Agent Platform
├── 08-AI模型微调训练平台/       # Fine-Tuning Platform
├── shared/                     # Shared libraries (data hub, action registry)
├── start-all-backends.bat      # One-click start for all 8 backends
└── CHANGELOG.md                # Interview manual (bug stories & architecture)
```

## Code Quality

- **Tests**: pytest for backend (all 8 projects, 10/10 passing each)
- **Type check**: vue-tsc for frontend (all 8 projects, 0 errors)
- **Load testing**: Locust scripts in each project's `backend/tests/`
- **CI**: GitHub Actions workflow (`.github/workflows/ci.yml`)

## Architecture

Each project follows the same full-stack pattern:

```
project/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── core/         # Auth, security, config
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response models
│   │   ├── services/     # Business logic layer
│   │   ├── rag/          # RAG module (Projects ①-③)
│   │   └── main.py       # App entry point
│   ├── tests/            # pytest + locust
│   ├── .env.example      # Environment template
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/        # Page components
│   │   ├── stores/       # Pinia state management
│   │   ├── api/          # API client modules
│   │   ├── router/       # Vue Router config
│   │   └── assets/       # Styles, images
│   └── package.json
├── sample-data/           # Demo knowledge base / data
└── README.md
```

## Cross-Project Integration

Projects are designed to work together in an AI ecosystem:

```
① 客服对话 ──┐
⑤ 话术训练 ──┤──→ ⑥ 数据中心 ──→ ⑧ 模型微调 ──→ 微调模型服务
④ 素材标签 ──┘        ↑                        │
                      └── 训练数据缓存/导出 ←────┘
⑦ 运营引擎 ←──调用──→ ①②③④⑤⑥⑧ (action_registry)
```

1. **Data Flywheel** — ①⑤④ push conversation/training/tag data to ⑥ via `X-Internal-Call` shared-secret auth; ⑥ cleans & annotates, then exports to ⑧ for fine-tuning
2. **Agent Orchestration** — ⑦ routes tasks to other systems via action registry (Docker service names + localhost fallback)
3. **Model Deployment** — ⑧'s deployed models are discoverable via `/models/active` for other projects

## Configuration

Each project requires a `.env` file in its `backend/` directory. Copy from the provided `.env.example`:

```env
# Required
DEEPSEEK_API_KEY=your-deepseek-api-key-here

# Database (dev)
DATABASE_URL=sqlite+aiosqlite:///./data/project_name.db

# Security
SECRET_KEY=your-secret-key-here
ADMIN_PASSWORD=your-admin-password
```

> ⚠️ Never commit real API keys or passwords. `.env` files are git-ignored.

## License

MIT License — see [LICENSE](LICENSE) for details.
