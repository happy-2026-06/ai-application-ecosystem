# AI Applications Collection

A collection of 8 AI-powered full-stack applications built with **Vue 3 + FastAPI + LangChain + DeepSeek**.

## Projects

| # | Project | Type | Description |
|---|---------|------|-------------|
| ① | RAG Customer Service | C-end | Enterprise knowledge-base Q&A for e-commerce |
| ② | AI Content Assistant | C-end | Viral titles, video scripts, social media copywriting |
| ③ | Short Video Script Studio | C-end | Storyboard scripts, TTS voiceover, subtitle export |
| ④ | Digital Asset Management | B-end | Asset upload, AI auto-tagging, multimodal search |
| ⑤ | Sales Training System | B-end | AI role-play customer scenarios, multi-dimension scoring |
| ⑥ | Data Center Platform | Middle-platform | Data ingestion, cleaning, annotation, quality reports |
| ⑦ | Multi-Agent Collaboration | Middle-platform | Multi-agent task orchestration with SSE streaming |
| ⑧ | Model Fine-Tuning Platform | Middle-platform | QLoRA fine-tuning, A/B comparison, one-click deployment |

## Tech Stack

- **Frontend**: Vue 3 + TypeScript + Naive UI + Pinia + Vite
- **Backend**: Python FastAPI + SQLAlchemy 2.0 (async)
- **AI**: LangChain + DeepSeek API + ChromaDB
- **Data**: SQLite (dev) / PostgreSQL (production) + Redis
- **Deploy**: Docker Compose + Nginx

## Quick Start

### Prerequisites

- Docker & Docker Compose
- DeepSeek API Key ([get one here](https://platform.deepseek.com/api_keys))

### Launch All Projects

```bash
# 1. Clone the repository
git clone <repo-url>
cd <repo-directory>

# 2. Configure environment for each project
# Copy .env.example to .env in each backend directory and add your API key:
#   01-RAG智能客服系统/backend/.env.example → .env
#   02-AI自媒体内容助手/backend/.env.example → .env
#   ... (repeat for all 8 projects)

# 3. Start all services
docker compose up -d --build

# 4. Access the apps
```

### Port Mapping

| Project | Backend | Frontend |
|---------|:------:|:--------:|
| ① RAG Customer Service | 8101 | 3001 |
| ② Content Assistant | 8202 | 3002 |
| ③ Script Studio | 8303 | 3003 |
| ④ Asset Management | 8404 | 3004 |
| ⑤ Sales Training | 8505 | 3005 |
| ⑥ Data Center | 8606 | 3006 |
| ⑦ Multi-Agent | 8707 | 3007 |
| ⑧ Fine-Tuning | 8808 | 3008 |

### Run a Single Project (Dev Mode)

Each project has its own `start.bat` for local development:

```bash
# Example: Project ① RAG Customer Service
cd 01-RAG智能客服系统
# Run start.bat (Windows) or:
# Terminal 1 - Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8101
# Terminal 2 - Frontend
cd frontend && npm install && npm run dev
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
├── postgres/                   # PostgreSQL init scripts
├── docker-compose.yml          # Unified Docker Compose
├── pyproject.toml              # Python linting config (ruff)
├── .eslintrc.json              # Frontend linting config
├── check-all.sh                # One-click code review script
└── run-stress-test.sh          # Stress testing script
```

## Code Quality

- **Python**: ruff formatting & linting (`pyproject.toml`)
- **Frontend**: ESLint + Vue 3 recommended rules (`.eslintrc.json`)
- **Pre-commit**: automated checks via `.pre-commit-config.yaml`
- **CI**: GitHub Actions workflow (`.github/workflows/ci.yml`)
- **Tests**: pytest for backend (8/8 projects)
- **Load testing**: Locust scripts in each project's `backend/tests/`

```bash
# Run all checks
./check-all.sh

# Run stress tests
./run-stress-test.sh all --users=50 --run-time=3m
```

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
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/        # Page components
│   │   ├── stores/       # Pinia state management
│   │   ├── api/          # API client modules
│   │   ├── router/       # Vue Router config
│   │   └── assets/       # Styles, images
│   ├── Dockerfile
│   └── package.json
├── sample-data/           # Demo knowledge base / data
└── README.md
```

## Cross-Project Integration

Projects are designed to work together in an AI ecosystem:

1. **Data Flywheel** — ①⑤ → ⑥ → ⑧: customer service & training data feeds into the Data Center for cleaning and annotation, then exports to the Fine-Tuning Platform to train custom models
2. **Asset Sharing** — ④ → ②③: managed digital assets are publicly searchable for content creation
3. **Agent Orchestration** — ⑦ → ①②③④⑤⑥⑧: the Multi-Agent Platform routes tasks to other systems via keyword matching
4. **Model Deployment** — ⑧ → ①②③⑤: fine-tuned models are deployed as inference APIs for other projects

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
