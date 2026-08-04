# AI 应用项目集 (AI Applications)

8个基于 Vue3 + FastAPI + LangChain + DeepSeek 的 AI 应用项目合集。

## 项目列表

| # | 项目 | 类型 | 说明 |
|---|------|------|------|
| ① | RAG智能客服系统 | C端 | 企业级知识库问答，电商客服场景 |
| ② | AI自媒体内容助手 | C端 | 爆款标题/视频脚本/图文文案生成 |
| ③ | AI短视频脚本工坊 | C端 | 分镜脚本/口播话术 |
| ④ | AI素材管理平台 | B端 | 素材上传/管理/检索 |
| ⑤ | AI销售培训系统 | B端 | 销售话术/场景模拟 |
| ⑥ | AI数据中心平台 | 中台 | 数据统计/可视化 |
| ⑦ | MCP多智能体协作平台 | 中台 | 多Agent协作框架 |
| ⑧ | AI模型微调训练平台 | 中台 | 模型微调/训练管理 |

## 技术栈

- 前端: Vue3 + TypeScript + NaiveUI + Pinia + Vite
- 后端: Python FastAPI + SQLAlchemy 2.0 (async)
- AI: LangChain + DeepSeek API + ChromaDB
- 数据: SQLite (开发) / PostgreSQL (生产)

## 启动方式

```bash
# 项目① RAG智能客服
cd 01-RAG智能客服系统 && start.bat
# → 前端 http://localhost:3001 | 后端 http://localhost:8101

# 项目② AI自媒体助手
cd 02-AI自媒体内容助手 && start.bat
# → 前端 http://localhost:3002 | 后端 http://localhost:8202
```

## 端口规划

| 项目 | 后端 | 前端 |
|------|:---:|:---:|
| ① RAG客服 | 8101 | 3001 |
| ② 自媒体 | 8202 | 3002 |
| ③ 脚本工坊 | 8303 | 3003 |
| ④ 素材管理 | 8404 | 3004 |
| ⑤ 销售培训 | 8505 | 3005 |
| ⑥ 数据中心 | 8606 | 3006 |
| ⑦ 多智能体 | 8707 | 3007 |
| ⑧ 模型训练 | 8808 | 3008 |
