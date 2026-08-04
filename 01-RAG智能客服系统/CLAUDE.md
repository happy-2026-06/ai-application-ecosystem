# 项目① — RAG智能客服系统

## 你是谁的AI助手
你是黄鑫的面试项目开发助手。用户是"计算机小白"，所有解释要通俗易懂，不要技术黑话。

## 项目背景
这是一个RAG企业级知识库问答系统。业务场景：电商客服。用户上传产品资料和FAQ到知识库，客户用自然语言提问（"退货怎么操作"），AI自动检索退货政策并回复带引用的答案。复杂问题可转人工。

## 技术框架
- 前端: Vue3 + TypeScript + NaiveUI + Pinia + Vite
- 后端: Python FastAPI + SQLAlchemy 2.0 (async)
- AI: LangChain + DeepSeek API (deepseek-v4-flash) + ChromaDB
- 数据: SQLite (开发) / PostgreSQL (生产)
- 部署: Docker Compose + Nginx

## 关键路径
- `backend/app/rag/prompts.py` → AI客服Prompt（热情/专业/同理心）
- `backend/app/services/chat_service.py` → SSE流式RAG管道
- `sample-data/` → 客服FAQ + 退货政策表
- `frontend/src/views/ChatView.vue` → 聊天界面（含🎧转人工按钮）

## 已完成的优化
1. AI客服模式：Prompt改为热情/专业/有同理心的客服语气
2. 客服知识库：电商客服FAQ + 退货政策表
3. 🎧转人工按钮：输入框旁一键生成工单+客服电话
4. 暗色模式：NaiveUI主题切换，CSS变量全覆盖
5. SQLite WAL模式：5项PRAGMA优化（WAL/NORMAL/cache/busy_timeout/foreign_keys）
6. 三阶段性能对比：SQLite标准(62%失败) → WAL(30%) → PostgreSQL(6%)
7. 50人并发Locust压测脚本 + 100个测试用户自动生成
8. MOCK_LLM环境变量：跳过DeepSeek API（省钱+压测用）
9. Claude Code hooks：SessionStart检查环境 + Stop提醒存档
10. 权限白名单：git/npm/python等11条常用命令免弹窗
11. 公网隧道：serveo SSH远程访问
12. 转人工API：POST /api/chat/escalate 工单队列

## 默认账号
admin / 123456

## 其他7个项目
都在 `C:\Users\35220\OneDrive\Desktop\AI应用项目\` 下：
- ② AI自媒体内容助手（爆款标题/脚本生成）
- ③ AI短视频脚本工坊（分镜脚本/口播话术）
- ④ AI素材管理平台（B端）
- ⑤ AI销售培训系统（B端）
- ⑥ AI数据中心平台（中台）
- ⑦ MCP多智能体协作平台（中台）
- ⑧ AI模型微调训练平台（中台）

共同技术底座: Vue3 + FastAPI + LangChain + DeepSeek
