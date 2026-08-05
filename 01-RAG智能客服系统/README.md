# RAG 企业级知识库问答系统

基于 **LangChain** 框架开发的企业级 RAG（检索增强生成）知识库问答系统，专注于电商平台商品知识库智能问答。

## ✨ 核心功能

- **🔍 智能问答**：基于知识库的 RAG 问答，支持流式输出和引用溯源
- **📚 知识库管理**：文档上传、自动解析、向量化存储（Admin）
- **👥 多用户多会话**：独立会话管理，历史记录持久化
- **🔐 用户认证**：注册/登录、JWT 认证、角色权限控制
- **📊 管理后台**：用户管理、系统仪表盘、知识库统计
- **🧠 GraphRAG**：知识图谱增强检索（Neo4j + 向量混合检索）
- **🎨 暗色模式**：支持亮色/暗色主题切换

## 🏗️ 技术栈

| 层 | 技术 |
|---|------|
| **后端框架** | FastAPI (异步) + SQLAlchemy 2.0 |
| **前端** | Vue 3 + TypeScript + Naive UI |
| **AI 框架** | LangChain |
| **LLM** | DeepSeek API (deepseek-chat) |
| **Embedding** | BGE-M3 (Ollama 本地) |
| **向量数据库** | ChromaDB |
| **图数据库** | Neo4j (GraphRAG — Phase 4 存根) |
| **关系数据库** | SQLite (开发) / PostgreSQL (生产) |
| **缓存** | Redis |
| **部署** | Docker Compose |

## 🚀 快速开始

### 前置条件

- Docker & Docker Compose
- DeepSeek API Key ([获取地址](https://platform.deepseek.com/))
- （可选）NVIDIA GPU（本地 Ollama 加速）

### 一键部署

```bash
# 1. 克隆项目
cd langchain-rag-system

# 2. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入你的 DEEPSEEK_API_KEY

# 3. 启动所有服务
docker-compose up -d

# 4. 预加载 Embedding 模型（首次运行）
docker-compose exec ollama ollama pull bge-m3

# 5. 访问系统
# 前端: http://localhost:3001
# API 文档: http://localhost:8101/api/docs
```

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8101

# 前端
cd frontend
npm install
npm run dev

# 基础设施（需要单独启动）
docker-compose up -d postgres redis chromadb neo4j ollama
```

### 默认账号

> ⚠️ 首次启动后系统会自动创建管理员账号，用户名 `admin`，密码请查看 `.env` 文件中的 `ADMIN_PASSWORD` 配置项。请登录后立即修改密码。

## 📁 项目结构
- ✅ AI客服模式（热情/专业/同理心 Prompt）
- ✅ SSE 流式问答 + 引用溯源
- ✅ 知识库管理（文档上传/解析/向量化）
- ✅ 多用户多会话 + 历史持久化
- ✅ 用户认证（JWT）+ 角色权限
- ✅ 管理后台 + 仪表盘统计
- ✅ 转人工客服（内存工单队列）
- ✅ 暗色模式 + 三栏客服台布局
- ✅ 50人并发 Locust 压测通过
- ⚠️ GraphRAG（Neo4j 知识图谱）为 Phase 4 存根，尚未实现
- ⚠️ BM25 混合检索为存根，当前仅用向量检索

```
langchain-rag-system/
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── api/              # API 路由 (auth, chat, kb, admin)
│   │   ├── core/             # 安全认证、JWT
│   │   ├── models/           # SQLAlchemy ORM 模型
│   │   ├── schemas/          # Pydantic 数据模型
│   │   ├── services/         # 业务逻辑层
│   │   ├── rag/              # RAG 核心模块
│   │   │   ├── graph/        # GraphRAG (Neo4j)
│   │   │   ├── embeddings.py # BGE-M3 嵌入
│   │   │   ├── vectorstore.py# ChromaDB 操作
│   │   │   ├── retriever.py  # 混合检索
│   │   │   ├── chain.py      # LangChain Chain
│   │   │   └── prompts.py    # Prompt 模板
│   │   └── main.py           # 应用入口
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # Vue 3 前端
│   ├── src/
│   │   ├── views/            # 页面组件
│   │   ├── stores/           # Pinia 状态管理
│   │   ├── api/              # API 调用封装
│   │   └── router/           # 路由配置
│   └── Dockerfile
├── nginx/                    # Nginx 反向代理
├── docker-compose.yml        # 服务编排
└── README.md
```

## 🔄 RAG 管道

```
用户提问 → Query Rewriting → 混合检索 (Vector + BM25 + Graph)
    → RRF 融合 → Reranker 精排 → Prompt 构建
    → DeepSeek 流式生成 → 引用溯源 → 返回答案
```

## 📝 API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| GET  | `/api/chat/sessions` | 会话列表 |
| POST | `/api/chat/ask` | 发送问题（SSE 流式） |
| GET  | `/api/kb/documents` | 文档列表 (Admin) |
| POST | `/api/kb/documents/upload` | 上传文档 (Admin) |
| GET  | `/api/admin/dashboard` | 管理仪表盘 (Admin) |

## 📄 License

MIT License - 毕业设计项目
