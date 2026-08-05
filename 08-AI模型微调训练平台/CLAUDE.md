# 项目⑧ — AI模型微调训练平台 (中台)

## 你是谁的AI助手
你是黄鑫的面试项目开发助手。用户是"计算机小白"，所有解释要通俗易懂。

## 项目背景
让通用大模型通过微调训练更懂特定业务。用项目⑥数据中心提供的高质量业务数据，对模型做QLoRA微调（低显存可用），微调前后A/B对比，一键部署为API。支持RLHF强化学习持续优化。

## 技术框架
- 前端: Vue3 + TypeScript + NaiveUI + Pinia + Vite
- 后端: Python FastAPI + SQLAlchemy 2.0 (async)
- 微调引擎: Unsloth + LLaMA-Factory + QLoRA
- 评估: BLEU/ROUGE + LLM-as-Judge
- 部署: vLLM (模型推理服务)
- GPU: 本地 / Google Colab T4 / AutoDL
- 存储: PostgreSQL + MinIO

## 关键变化（全新增模块）
- 微调任务管理（创建/运行/监控/停止）
- 训练可视化（Loss曲线/学习率/评估指标）
- 模型仓库（版本管理/模型对比/一键部署）
- RLHF反馈循环集成

## 状态
🔴 待开发 — 框架已复制，需从零构建微调训练模块

## 其他7个项目
都在 `C:\Users\35220\OneDrive\Desktop\AI应用项目\` 下，共同前端+后端底座。
