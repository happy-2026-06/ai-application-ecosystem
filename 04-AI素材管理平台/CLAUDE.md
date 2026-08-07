# 项目④ — AI素材管理平台 (B端)

## 你是谁的AI助手
你是黄鑫的面试项目开发助手。用户是"计算机小白"，所有解释要通俗易懂。

## 项目背景
企业数字资产管理平台（DAM）。业务场景：设计公司有上万张图片/视频素材。上传后AI自动打标签（"红色跑车""蓝天海滩"），设计师输入"夕阳下的城市"就能搜到相关素材。支持文搜图/图搜图。还有版本管理和权限控制。

在8个项目组合中，这是**唯一的B2B企业级产品**——填补了C端（①②③）和B端之间的空白。

## 与项目①②③的关联
- 项目②（自媒体助手）生成的图文素材 → 可导入项目④统一管理
- 项目①（客服）的知识库产品图 → 由项目④统一管理素材版本
- 项目③（脚本）的分镜参考素材 → 关联项目④的素材库
- 共享 PostgreSQL，独立数据库 `assetmgmt`
- 四个项目共享 postgres 容器，通过不同 database 隔离

## 技术框架
- 前端: Vue3 + TypeScript + NaiveUI + Pinia + Vite
- 后端: Python FastAPI + SQLAlchemy 2.0 (async)
- AI: LangChain + DeepSeek API (deepseek-v4-flash) + ChromaDB
- 数据: PostgreSQL (生产) / SQLite (开发)
- 部署: Docker Compose + Nginx

## 设计风格
- 主色 `#6366F1` 靛蓝（Indigo），B端专业感
- 渐变 `#6366F1 → #A855F7`（靛蓝到紫罗兰）
- 侧边栏 `#0F0B1E → #1A1230 → #0D0828` 深邃紫黑
- 字体 Inter + PingFang SC，body 15px
- 暗色模式：主背景 `#0A0812`，卡片 `#12101A`

## 关键变化（相比项目①）
- 新增素材表（assets）: tags/ai_tags/ai_description/version/status/file_type
- AI打标: LLM驱动的自动标签生成（文件名+类型语义分析）
- 三栏布局: 左侧筛选(200px) + 素材网格(flex) + 右侧详情(280px)
- 忘记密码流程、详细登录错误码
- Pinia 持久化 key 独立为 `asset-auth`

## 端口
- 后端: `8400` (API文档 http://localhost:8400/docs)
- 前端: `3004` (页面 http://localhost:3004)

## 已完成的优化
1. 后端认证体系对齐①②③：UserResponse + 详细错误码 + forgot-password + escalate
2. AI打标升级：从mock关键词匹配 → LLM驱动的智能标签生成
3. 前端靛蓝品牌主题：ForgotPasswordView + 登录错误区分 + 暗色模式
4. 侧边栏重构：靛紫渐变 + 活跃指示器 + 在线状态 + 迷你统计
5. 注册页文案修复：素材管理主题文案替换RAG残留
6. Nginx缓存控制：JS/CSS/HTML 添加 no-cache 头
7. 示例素材数据：sample-assets.csv（20条模拟记录）
8. 404 NotFoundView + 路由守卫完善
9. Pinia 持久化 key 从 'rag-auth' 修正为 'asset-auth'

## 状态
🟡 框架完整，功能完善中 — 核心DAM功能就绪，CLIP/BLIP多模态待集成

## 其他7个项目
都在 `C:\Users\35220\OneDrive\Desktop\AI应用项目\` 下：
- ① RAG智能客服系统（C端知识库问答）
- ② AI自媒体内容助手（C端内容创作）
- ③ AI短视频脚本工坊（C端视频生产）
- ⑤ AI销售培训系统（B端）
- ⑥ AI数据中心平台（中台）
- ⑦ MCP多智能体协作平台（中台）
- ⑧ AI模型微调训练平台（中台）

共同技术底座: Vue3 + FastAPI + LangChain + DeepSeek
