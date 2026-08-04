# 项目② — AI自媒体内容助手

## 你是谁的AI助手
你是黄鑫的面试项目开发助手。用户是"计算机小白"，所有解释要通俗易懂。

## 项目背景
AI爆款内容生成工具。业务场景：自媒体创作者（比如手机店主想拍抖音带货）。告诉AI产品信息，AI生成爆款标题+短视频脚本+图文文案，支持抖音/小红书/B站/视频号/快手5平台风格适配。

## 技术框架
- 前端: Vue3 + TypeScript + NaiveUI + Pinia + Vite
- 后端: Python FastAPI + SQLAlchemy 2.0 (async)
- AI: LangChain + DeepSeek API (deepseek-v4-flash) + ChromaDB
- 数据: SQLite (开发) / PostgreSQL (生产)

## 关键路径
- `backend/app/rag/prompts.py` → 自媒体创作助手Prompt
- `sample-data/` → 标题模板库 + 脚本模板库（5大平台）
- `backend/.env` → APP_NAME=AI自媒体内容助手

## 状态
🟡 框架已建，Prompt已改为自媒体助手
待完成：前端标题修改、sample-data清理旧产品数据

## 其他7个项目
都在 `C:\Users\35220\OneDrive\Desktop\AI应用项目\` 下，共同技术底座: Vue3 + FastAPI + LangChain + DeepSeek
