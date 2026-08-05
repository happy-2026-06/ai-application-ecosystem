# 项目③ — AI短视频脚本工坊

## 你是谁的AI助手
你是黄鑫的面试项目开发助手。用户是"计算机小白"，所有解释要通俗易懂。

## 项目背景
短视频自动化生产引擎。业务场景：短视频创作者。告诉AI产品信息，AI输出专业分镜表（镜号/时长/画面内容/口播文案/字幕特效），直接照着拍。

## 技术框架
- 前端: Vue3 + TypeScript + NaiveUI + Pinia + Vite
- 后端: Python FastAPI + SQLAlchemy 2.0 (async)
- AI: LangChain + DeepSeek API (deepseek-chat) + ChromaDB
- 数据: SQLite (开发) / PostgreSQL (生产)

## 关键路径
- `backend/app/rag/prompts.py` → 三种风格模式 Prompt（带货/测评/开箱）+ select_mode_guide()
- `backend/app/rag/chain.py` → build_chain(question) 动态选择模式
- `backend/app/services/chat_service.py` → 流式 SSE 响应管线
- `sample-data/` → 分镜模板库 + 口播话术模板
- `backend/.env` → APP_NAME=AI短视频脚本工坊

## 状态
🟢 核心功能已完成（2026-08-05）：
- ✅ 启动脚本标题/文案已修复
- ✅ Prompt 重写：三种风格（带货/测评/开箱）差异化 Prompt + 自动模式选择
- ✅ 前端页面文案对齐（登录页/注册页/侧边栏）
- ✅ 18个测试用例全部通过
- ✅ 历史记录功能：左侧会话列表 + 新建/查看/删除
- ⚠️ 待真机测试：需要配置 DEEPSEEK_API_KEY 后实测生成效果

## 其他7个项目
都在 `C:\Users\35220\OneDrive\Desktop\AI应用项目\` 下，共同技术底座: Vue3 + FastAPI + LangChain + DeepSeek
