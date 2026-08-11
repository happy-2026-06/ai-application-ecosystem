# AI数据中心平台 — 数据中枢

企业级数据底座平台。汇聚各业务系统的数据（客服对话、培训记录、内容创作等），统一进行采集→清洗→AI标注→版本化→质量分析→导出微调格式，为上层 AI 应用提供高质量数据支撑。

## ✨ 核心功能

- **📥 数据接入**：外部系统通过 `external/ingest` 接口推送数据，支持 `X-Internal-Call` 内部认证
- **🧹 数据清洗**：自动清洗噪声数据，标准化数据格式
- **🏷️ AI 自动标注**：LLM 驱动的自动标注引擎
- **📦 版本管理**：数据集版本化，支持历史版本对比
- **📊 质量报告**：数据质量仪表盘，含完整性、一致性、时效性分析
- **📤 导出微调格式**：`export-for-finetune` 接口，导出训练就绪格式供模型工厂使用
- **🔍 数据预览**：DataSetDetail 页支持数据预览与标注工作台
- **🔐 用户认证**：注册/登录/JWT 认证/忘记密码
- **👥 管理后台**：用户管理 + 数据仪表盘
- **🎨 暗色模式**：全页面暗色主题支持

## 🏗️ 技术栈

| 层 | 技术 |
|---|------|
| **后端框架** | FastAPI (异步) + SQLAlchemy 2.0 |
| **前端** | Vue 3 + TypeScript + Naive UI + Pinia |
| **AI 标注引擎** | LangChain + DeepSeek API |
| **数据库** | SQLite (开发) / PostgreSQL (生产) |
| **部署** | Docker Compose |

## 🖥️ 端口

- 前端: `http://localhost:3006`
- 后端: `http://localhost:8606`
- API 文档: `http://localhost:8606/api/docs`

## 🚀 快速开始

```bash
# 本地开发
cd 06-AI数据中心平台
start.bat

# 或 Docker
docker compose up -d p6-backend p6-frontend
```

## 📁 项目结构

```
06-AI数据中心平台/
├── backend/
│   ├── app/
│   │   ├── api/              # 路由 (auth, data)
│   │   ├── core/             # JWT 认证
│   │   ├── models/           # ORM 模型 (DataSet, DataVersion, DataAnnotation)
│   │   ├── schemas/          # Pydantic 数据模型
│   │   ├── services/         # 业务逻辑 (data_service, action_registry, datahub_client)
│   │   └── main.py
│   ├── tests/                # pytest + locust
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/            # DataConsole, DataSetDetail, Login, Register, ForgotPassword, Admin
│   │   ├── stores/           # Pinia auth store
│   │   ├── api/              # API 客户端 (auth, data)
│   │   ├── router/           # Vue Router
│   │   └── layouts/          # AppLayout
│   ├── Dockerfile
│   └── package.json
├── sample-data/
├── start.bat / start.py
└── README.md
```

## 🔗 跨项目联动（数据飞轮核心节点）

| 联动 | 说明 |
|------|------|
| ①⑤ → ⑥ | 客服对话 + 培训记录推送到数据中心 |
| ⑥ → ⑧ | 导出微调格式供模型工厂训练 |

## 📄 License

MIT License
