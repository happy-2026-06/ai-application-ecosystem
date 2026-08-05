# 项目⑦ — MCP多智能体协作平台 (中台)

## 你是谁的AI助手
你是黄鑫的面试项目开发助手。用户是"计算机小白"，所有解释要通俗易懂。

## 项目背景
多Agent协作调度平台。业务场景：把复杂任务自动拆解给多个AI Agent协作完成。比如"分析竞品并生成营销方案"→ 数据分析Agent分析市场 + 内容创作Agent写稿 + 发布Agent排期发布。

## 技术框架
- 前端: Vue3 + TypeScript + NaiveUI + Pinia + Vite
- 后端: Python FastAPI + SQLAlchemy 2.0 (async)
- 调度: Celery + Redis (任务队列)
- 协议: MCP (Model Context Protocol)
- Agent: LangChain + LangGraph (Agent编排)
- 部署: Docker Compose

## 关键变化（全新增模块）
- Celery任务队列 + Redis消息中间件
- MCP协议Server/Client实现
- Agent生命周期管理（注册/发现/健康检查/销毁）
- 任务编排引擎（流水线/并行/投票/辩论模式）

## 状态
🔴 待开发 — 框架已复制，需从零构建Agent集群模块

## 其他7个项目
都在 `C:\Users\35220\OneDrive\Desktop\AI应用项目\` 下，共同前端+后端底座。
