# AI销售培训系统 — 话术对战教练

企业级 AI 销售角色扮演培训平台。AI 扮演不同类型的客户，销售人员练习应对话术，AI 从流畅度、说服力、产品知识、异议处理、情绪控制 5 个维度实时打分，帮助销售团队提升实战能力。

## ✨ 核心功能

- **🎭 角色扮演对练**：AI 扮演 4 类客户（挑剔型/犹豫型/专业型/急躁型），模拟真实销售场景
- **📊 5 维评分体系**：流畅度 + 说服力 + 产品知识 + 异议处理 + 情绪控制，每轮对话实时打分
- **💬 SSE 流式对话**：AI 客户实时回应，模拟真实对话节奏
- **📝 培训报告**：培训结束后生成综合分析报告，含进步曲线和薄弱环节分析
- **📚 知识库支撑**：内置销售话术模板、产品知识示例、异议处理技巧、培训场景案例
- **👥 多用户管理**：每位销售独立培训记录，支持历史回放
- **🔐 用户认证**：注册/登录、JWT 认证、角色权限
- **🔑 忘记密码**：Demo 模式支持密码重置
- **🎨 暗色模式**：全页面暗色主题支持

## 🏗️ 技术栈

| 层 | 技术 |
|---|------|
| **后端框架** | FastAPI (异步) + SQLAlchemy 2.0 |
| **前端** | Vue 3 + TypeScript + Naive UI + Pinia |
| **AI 引擎** | LangChain + DeepSeek API (deepseek-chat) |
| **LLM Judge** | DeepSeek 评判 5 维打分 |
| **数据库** | SQLite (开发) / PostgreSQL (生产) |
| **部署** | Docker Compose |

## 🖥️ 端口

- 前端: `http://localhost:3005`
- 后端: `http://localhost:8505`
- API 文档: `http://localhost:8505/api/docs`

## 🚀 快速开始

```bash
# 本地开发
cd 05-AI销售培训系统
start.bat

# 或 Docker
docker compose up -d p5-backend p5-frontend
```

### 默认账号

> 管理员 `admin`，密码见 `.env` 文件中的 `ADMIN_PASSWORD`。

## 📁 项目结构

```
05-AI销售培训系统/
├── backend/
│   ├── app/
│   │   ├── api/              # 路由 (auth, training)
│   │   ├── core/             # JWT 认证
│   │   ├── models/           # ORM 模型 (TrainingSession, TrainingRound)
│   │   ├── schemas/          # Pydantic 数据模型
│   │   ├── services/         # 业务逻辑 (training_service, action_registry, datahub_client)
│   │   └── main.py
│   ├── tests/                # pytest + locust
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/            # TrainingRoom, TrainingHistory, Login, Register, ForgotPassword, Admin
│   │   ├── stores/           # Pinia (auth, training)
│   │   ├── api/              # API 客户端 (auth, training)
│   │   ├── router/           # Vue Router
│   │   └── layouts/          # AppLayout
│   ├── Dockerfile
│   └── package.json
├── sample-data/               # 培训话术模板 + 产品知识 + 异议处理技巧 + 场景案例
├── start.bat / start.py
└── README.md
```

## 🔗 跨项目联动

| 联动 | 说明 |
|------|------|
| ⑤ → ⑥ (数据飞轮) | 培训评分记录推送到数据中心，用于数据分析和微调训练 |

## 📄 License

MIT License
