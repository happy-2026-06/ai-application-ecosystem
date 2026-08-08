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

## 已完成优化

### 项目① RAG智能客服系统
- 三栏客服台布局（侧边统计 + 会话列表 + 聊天区）
- 专业蓝主题 `#2563EB`，暗色模式全覆盖
- 🎧转人工客服 API + 工单生成
- ChatView：返回首页清除会话、切换防闪烁、消息编辑/删除
- 404捕获路由 + LoginView完整暗色模式
- **知识库管理增强**：
  - 文档上传即处理（同步完成，不再等待）
  - 支持 txt/md/csv/docx/pdf 在线预览
  - 上传后支持重命名（inline 编辑）
  - GBK 文件名自动修复（Windows 浏览器乱码问题）
  - 容器重启自动恢复（pending 文档自动重新处理）
  - Docker 数据卷持久化（uploads + chroma）
- **DeepSeek API**：全项目统一配置，RAG 回复基于真实知识库
- **知识库文档**：支持 4 种格式（txt/md/docx/pdf），Word 文档自动解析

### 项目② AI自媒体内容助手
- 顶部导航 + Dashboard首页 + 创作工作台
- 活力橙主题 `#FF6B35`，5平台品牌色标签
- 4个知识库文件（标题模板 + 脚本模板 + 平台风格指南 + 爆款案例库）
- Dashboard：快速创作 + 最近会话 + 实时统计 + 热门模板
- SSE流式生成 + sessionId历史加载
- 字体优化（Inter 32px/800 h1, 15px body）
- DeepSeek API 已配置

### 项目③ AI短视频脚本工坊
- 分镜脚本 + 口播话术生成
- DeepSeek API 已配置

### 项目④ AI素材管理平台
- B端 DAM 平台，素材上传/管理/检索
- Glassmorphism + Indigo 品牌主题
- DeepSeek API 已配置

## 仓库

https://gitee.com/golden-expert/ai-applications
