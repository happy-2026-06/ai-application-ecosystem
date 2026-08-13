# AI模型微调训练平台 — 模型定制工厂

企业级模型微调训练平台。让通用大模型通过业务数据微调训练更懂特定领域知识。支持 QLoRA 高效微调、训练监控、A/B 对比评估、一键部署 API，以及 Smart Proxy 智能推理代理（意图路由 + 少样本检索 + 响应缓存）。

## ✨ 核心功能

- **🔬 QLoRA 微调训练**：低显存高效微调，支持超参配置（learning_rate、epochs、batch_size）
- **📈 训练监控**：Loss 曲线、评估指标（BLEU/ROUGE）展示（当前为模拟训练生成，真实微调引擎预留）
- **⚖️ A/B 对比测试**：微调模型 vs 基座模型对比，LLM Judge 自动评判
- **🚀 一键部署**：训练完成 → 部署为推理 API，其他项目可直接调用
- **🧠 Smart Proxy 三层推理**：
  - 第 1 层：意图路由（8 个业务领域零成本关键词匹配）
  - 第 2 层：训练数据少样本检索（混合评分：关键词 + 类别 + 文本相似度）
  - 第 3 层：LRU 响应缓存（MD5 哈希键 + TTL 过期 + 自动淘汰）
- **📦 模型仓库**：版本管理、模型对比、训练数据缓存
- **🔐 用户认证**：注册/登录、JWT 认证、角色权限
- **🔑 忘记密码**：Demo 模式支持密码重置
- **🎨 暗色模式**：全页面暗色主题支持

## 🏗️ 技术栈

| 层 | 技术 |
|---|------|
| **后端框架** | FastAPI (异步) + SQLAlchemy 2.0 |
| **前端** | Vue 3 + TypeScript + Naive UI + Pinia |
| **微调引擎** | QLoRA（模拟训练 + 真实 Unsloth 集成预留） |
| **评估** | BLEU/ROUGE + LLM-as-Judge |
| **推理加速** | Smart Proxy（意图路由 + 少样本检索 + 缓存） |
| **数据库** | SQLite (开发) / PostgreSQL (生产) |
| **部署** | Docker Compose |

## 🖥️ 端口

- 前端: `http://localhost:3008`
- 后端: `http://localhost:8808`
- API 文档: `http://localhost:8808/api/docs`

## 🚀 快速开始

```bash
# 本地开发
cd 08-AI模型微调训练平台

# 1. 启动后端（端口 8808）
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8808

# 2. 另开终端，启动前端（端口 3008）
cd ../frontend
npm install
npm run dev

# 或 Docker
docker compose up -d p8-backend p8-frontend
```

## 📁 项目结构

```
08-AI模型微调训练平台/
├── backend/
│   ├── app/
│   │   ├── api/              # 路由 (auth, finetune)
│   │   ├── core/             # JWT 认证
│   │   ├── models/           # ORM 模型 (FineTuneTask, ModelVersion, ABTest)
│   │   ├── schemas/          # Pydantic 数据模型
│   │   ├── services/         # 业务逻辑 (finetune_service, smart_proxy, intent_router, training_retriever)
│   │   └── main.py
│   ├── tests/                # pytest + locust
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/            # TrainingLab, TaskDetail, Login, Register, ForgotPassword, Settings, Admin
│   │   ├── stores/           # Pinia auth store
│   │   ├── api/              # API 客户端 (auth)
│   │   ├── router/           # Vue Router
│   │   └── layouts/          # AppLayout
│   ├── Dockerfile
│   └── package.json
├── sample-data/
└── README.md
```

## 🔗 跨项目联动（模型上线闭环）

| 联动 | 说明 |
|------|------|
| ⑥ → ⑧ | 数据中心导出数据集 → 创建微调任务 |
| ⑧ → ①②③⑤ | 微调模型部署为推理 API → 其他项目调用 |

## 📝 API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/finetune/tasks` | 创建微调任务 |
| GET  | `/api/finetune/tasks/{id}` | 查询任务状态 |
| POST | `/api/finetune/tasks/from-dataset/{id}` | 从数据中心创建微调任务 |
| PATCH | `/api/finetune/models/{id}/deploy` | 部署模型 API |
| POST | `/api/finetune/models/{id}/proxy` | Smart Proxy 推理 |
| GET  | `/api/finetune/models/cache-stats` | 缓存统计 |
| POST | `/api/finetune/models/cache-clear` | 清除缓存 |
| GET  | `/api/finetune/dashboard` | 训练仪表盘 |
| POST | `/api/finetune/tasks/{task_id}/abtests` | A/B 对比测试 |

## 📄 License

MIT License
