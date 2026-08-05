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

## 页面布局
- **三栏客服台**：侧边栏(200px) + 会话列表(260px) + 聊天区(flex)
- 侧边栏顶部3个统计卡片（今日会话/满意率/在线）
- 导航：对话 → 知识库管理 → 设置 → 暗色切换 → 退出
- 聊天区：欢迎页 + AI气泡 + 消息编辑/删除 + 转人工

## 设计风格
- 主色 `#2563EB` 专业蓝，侧边栏 `#0F172A→#1E293B` 深蓝渐变
- 用户气泡 `#2563EB→#7C3AED` 蓝紫渐变，AI气泡 `#F1F5F9` 浅灰
- 字体 Inter + PingFang SC，body 15px
- 暗色模式：主背景 `#0F172A`，卡片 `#18181D`

## 端口
- 后端: `8101` (API文档 http://localhost:8101/docs)
- 前端: `3001` (页面 http://localhost:3001)

## 已完成的优化
1. AI客服模式：Prompt改为热情/专业/有同理心的客服语气
2. 客服知识库：电商客服FAQ + 退货政策表
3. 🎧转人工按钮：调用 `POST /api/chat/escalate` 生成工单+客服电话
4. 暗色模式：NaiveUI主题切换 + `[data-theme="dark"]` CSS全覆盖
5. SQLite WAL模式：5项PRAGMA优化（WAL/NORMAL/cache/busy_timeout/foreign_keys）
6. 三阶段性能对比：SQLite标准(62%失败) → WAL(30%) → PostgreSQL(6%)
7. 50人并发Locust压测脚本 + 100个测试用户自动生成
8. MOCK_LLM环境变量：跳过DeepSeek API（省钱+压测用）
9. 三栏客服台布局：侧边统计 + 会话列表 + 聊天区
10. ChatView完善：返回首页清除会话、切换防闪烁、编辑只删单条
11. 404捕获路由 + LoginView完整暗色模式
12. 端口独立 (8101)：与项目②-⑧互不冲突

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
