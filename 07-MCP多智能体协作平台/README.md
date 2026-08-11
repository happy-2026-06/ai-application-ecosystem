# MCP多智能体协作平台 — 智能运营引擎

多 Agent 协作调度平台。将复杂任务自动拆解，分配给多个 AI Agent 协作完成，支持 4 种编排模式（流水线/并行/投票/辩论），通过 SSE 流式实时展示 Agent 协作过程。

## ✨ 核心功能

- **🤖 Agent 管理**：Agent 注册、发现、生命周期管理
- **🔀 4 种编排模式**：
  - **Pipeline（流水线）**：Agent 顺序执行，前一个输出成为下一个的输入
  - **Parallel（并行）**：多 Agent 同时从不同角度处理同一任务
  - **Vote（投票）**：各 Agent 独立投票 + LLM Judge 公正裁判
  - **Debate（辩论）**：正方→反方→反驳→总结→裁判，6 轮辩论流程
- **📡 SSE 实时流式**：SSE 逐事件推送每个 Agent 的执行状态
- **🔗 跨项目调度**：关键词匹配用户意图 → 自动 HTTP 调用其他 7 个系统的 API
- **📋 任务管理**：任务 CRUD、执行历史、结果聚合
- **🔐 用户认证**：注册/登录、JWT 认证、角色权限
- **🔑 忘记密码**：Demo 模式支持密码重置
- **🎨 暗色模式**：全页面暗色主题支持

## 🏗️ 技术栈

| 层 | 技术 |
|---|------|
| **后端框架** | FastAPI (异步) + SQLAlchemy 2.0 |
| **前端** | Vue 3 + TypeScript + Naive UI + Pinia |
| **AI 引擎** | LangChain + DeepSeek API |
| **跨项目通信** | httpx + Docker DNS 服务发现 |
| **数据库** | SQLite (开发) / PostgreSQL (生产) |
| **部署** | Docker Compose |

## 🖥️ 端口

- 前端: `http://localhost:3007`
- 后端: `http://localhost:8707`
- API 文档: `http://localhost:8707/api/docs`

## 🚀 快速开始

```bash
# 本地开发
cd 07-MCP多智能体协作平台
start.bat

# 或 Docker
docker compose up -d p7-backend p7-frontend
```

## 📁 项目结构

```
07-MCP多智能体协作平台/
├── backend/
│   ├── app/
│   │   ├── api/              # 路由 (auth, agent)
│   │   ├── core/             # JWT 认证
│   │   ├── models/           # ORM 模型 (Agent, Task, Execution)
│   │   ├── schemas/          # Pydantic 数据模型
│   │   ├── services/         # 业务逻辑 (agent_service, action_registry, datahub_client)
│   │   └── main.py
│   ├── tests/                # pytest + locust
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/            # AgentConsole, Login, Register, ForgotPassword, AdminDashboard, AdminUsers
│   │   ├── stores/           # Pinia auth store
│   │   ├── api/              # API 客户端 (auth, agent)
│   │   ├── router/           # Vue Router
│   │   └── layouts/          # AppLayout
│   ├── Dockerfile
│   └── package.json
├── sample-data/
└── README.md
```

## 🔗 跨项目联动（Agent 编排中枢）

| 联动 | 说明 |
|------|------|
| ⑦ → ①②③④⑤⑥⑧ | 关键词匹配用户意图 → HTTP 自动调用其他系统 API |
| shared/action_registry | 11 个注册操作的统一调用表 |

## 📝 API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/agent/tasks/stream` | SSE 流式执行 Agent 任务 |
| GET  | `/api/agent/tasks` | 任务列表 |
| GET  | `/api/agent/tasks/{id}/executions` | 查看执行步骤 |
| DELETE | `/api/agent/tasks/{id}` | 删除任务 |
| POST | `/api/agent/agents/seed` | 初始化 Agent |
| GET  | `/api/agent/agents` | Agent 列表 |

## 📄 License

MIT License
