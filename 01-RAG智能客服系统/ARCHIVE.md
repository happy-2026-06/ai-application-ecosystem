# 项目① RAG智能客服系统 — 开发存档

## 项目概述

企业级 AI 知识库问答系统，面向电商客服场景。管理员上传产品资料和 FAQ 到知识库，终端用户用自然语言提问（"退货怎么操作"），AI 自动检索并回复。

## 技术栈

| 层 | 技术 |
|------|------|
| 前端 | Vue3 + TypeScript + NaiveUI + Pinia + Vite + MarkdownIt |
| 后端 | Python FastAPI + SQLAlchemy 2.0 (async) + LangChain |
| AI | DeepSeek API (deepseek-v4-flash) + ChromaDB 向量检索 |
| 数据 | SQLite (开发) / PostgreSQL (生产) |

## 最终布局

**三栏客服台布局：**
- 左侧 200px：统计卡片（今日会话数/满意率/在线人数） + 导航（对话/知识库/设置/暗色模式）
- 中间 260px：会话列表（搜索/新建/删除/切换）
- 右侧 flex：聊天区（欢迎页/AI对话/输入框/转人工）

## 设计风格

- **主题色**：Professional Blue `#2563EB`
- **侧边栏**：`#0F172A` → `#1E293B` 深蓝渐变
- **用户气泡**：`#2563EB` → `#7C3AED` 蓝紫渐变
- **AI 气泡**：`#F1F5F9` 浅灰背景
- **字体**：Inter + PingFang SC，body 15px，标题 700-800 weight

## 开发中遇到的困难

### 1. Prompt 模板花括号冲突（LangChain `KeyError`）
**问题**：`prompts.py` 中写了 `{功能}` `{场景}` `{效果}` `{产品名}` 作为占位符给 AI 参考，但 LangChain 的 `ChatPromptTemplate` 会把这些当成模板变量去匹配输入字典，导致 `KeyError` 报错。
**解决**：将花括号双写转义 `{{功能}}` `{{场景}}` 等，LangChain 会正确把它们当成普通文本。花了好几个小时才定位到。

### 2. 端口冲突——两个项目开同一个端口
**问题**：项目①和项目②都默认用 8000 端口。先启动①占了 8000，②的后端启动没报错但其实在后台悄悄绑定失败。后果是②的前端请求全部打到了①的旧服务上——检索结果不对、回复内容也不对。
**解决**：彻底排查后发现是**端口冲突**。将①、②分别分配独立端口（8101/8202 后端，3001/3002 前端），同时给两个项目的 `.env`、`vite.config.ts`、`start.bat` 全部同步更新。

### 3. Windows `start` 命令标题含中文导致失败
**问题**：`start.bat` 里写 `start "RAG-Backend-01"` 在中文 Windows 下把"01"后面的中文字符当文件名解析，报"系统找不到文件"。
**解决**：去掉所有中文标题，改用纯英文如 `start "P1Backend"`。

### 4. 登录后跳转到不存在的路由
**问题**：LoginView 登录成功后 `router.push('/chat')`，但路由表里最初配的是 `/studio`。登录完跳到不存在的路由→白屏。
**解决**：统一将跳转路径改为 `/chat`，命名路由也保持一致性。

### 5. ChatView 会话管理迁移到 AppLayout
**问题**：原设计 ChatView 内有自己的会话列表面板。改成三栏布局后，会话列表要提到 AppLayout 中管理，ChatView 需要简化。
**解决**：将 session 相关的 CRUD 逻辑移到 AppLayout，ChatView 只负责消息显示和输入。中间出现了 `chatStore.currentSession = null` 直接修改 Pinia 状态的写法（绕过了封装），暂可接受但应后续改为 store 方法。

### 6. 暗色模式 CSS 覆盖不完整
**问题**：LoginView 的暗色模式只覆盖了 `.login-right` 背景和标题，缺少 `.form-card`、`.form-sub`、`.feat`、`.left-footer` 等元素的暗色样式。
**解决**：逐步补充所有遗漏的 `[data-theme="dark"]` 选择器。

## 访问信息

| 项目 | 地址 |
|------|------|
| 前端 | http://localhost:3001 |
| 后端 | http://localhost:8101/docs |
| 账号 | admin / 123456 |
