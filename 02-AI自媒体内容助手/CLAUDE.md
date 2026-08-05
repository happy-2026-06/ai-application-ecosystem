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
- `sample-data/` → 标题模板库 + 脚本模板库 + 平台风格指南 + 爆款案例库（5大平台）
- `frontend/src/views/ContentStudio.vue` → 创作工作台（SSE流式生成）
- `frontend/src/views/DashboardHome.vue` → Dashboard首页

## 页面布局
- **顶部导航 + Dashboard**：56px毛玻璃顶栏 + 全宽内容区
- 顶栏：✍️ 创作助手 + 首页/创作/管理 + 用户头像/暗色/退出
- Dashboard首页：问候语 + 2×2卡片网格（快速创作/最近会话/统计/热门模板） + 快捷模板栏
- 创作页：左侧输入面板(320px) + 右侧流式结果 + "←返回首页"

## 设计风格
- 主色 `#FF6B35` 活力橙，侧边栏 `#1A0F2E→#2D1B3E` 深紫渐变
- 平台色：抖音 `#FF0050` 小红书 `#FF2442` B站 `#FB7299` 视频号 `#07C160` 快手 `#FF4906`
- 字体 Inter + PingFang SC，h1 32px/800，body 15px
- 暗色模式：主背景 `#0F0A14`，卡片 `#1E1E28`

## 端口
- 后端: `8202` (API文档 http://localhost:8202/docs)
- 前端: `3002` (页面 http://localhost:3002)

## 已完成的优化
1. 自媒体创作Prompt：爆款标题+脚本+图文+建议四合一输出
2. 5平台风格适配模板：标题模板库 + 脚本模板库 + 平台风格指南 + 爆款案例库（共4个文件）
3. Dashboard首页：快速创作 + 最近会话 + 实时统计 + 热门模板
4. 顶部导航栏：毛玻璃效果，平台色标签
5. 平台色复选框：5个平台各用品牌色（抖/红/B/视/快）
6. SSE流式生成：打字机效果 + 加载动画 + 平台标签
7. ContentStudio sessionId支持：从Dashboard"最近创作"进入加载历史
8. Pinia持久化key已更新（`creator-auth`）
9. 暗色模式全面覆盖（所有页面+组件）
10. 字体优化：Inter + h1 32px/800 + 全局body 15px
11. Prompt花括号转义修复（`{功能}` → `{{功能}}`）
12. 端口独立 (8202)：与项目①互不冲突

## 默认账号
admin / 123456

## 其他7个项目
都在 `C:\Users\35220\OneDrive\Desktop\AI应用项目\` 下：
- ① RAG智能客服系统（知识库问答）
- ③ AI短视频脚本工坊（分镜脚本/口播话术）
- ④ AI素材管理平台（B端）
- ⑤ AI销售培训系统（B端）
- ⑥ AI数据中心平台（中台）
- ⑦ MCP多智能体协作平台（中台）
- ⑧ AI模型微调训练平台（中台）

共同技术底座: Vue3 + FastAPI + LangChain + DeepSeek
