# 项目② AI自媒体内容助手 — 开发存档

## 项目概述

AI 爆款内容生成工具，面向自媒体创作者。用户告诉 AI 自己的产品信息，AI 生成爆款标题 + 短视频脚本 + 图文文案 + 发布建议，支持抖音/小红书/B站/视频号/快手 5 个平台风格适配。

## 技术栈

| 层 | 技术 |
|------|------|
| 前端 | Vue3 + TypeScript + NaiveUI + Pinia + Vite + MarkdownIt |
| 后端 | Python FastAPI + SQLAlchemy 2.0 (async) + LangChain |
| AI | DeepSeek API (deepseek-v4-flash) + ChromaDB |
| 模板 | sample-data（标题模板库/脚本模板库/平台风格指南/爆款案例库） |

## 最终布局

**顶部导航 + Dashboard 首页：**
- 顶部 56px：毛玻璃导航栏（首页/创作/知识库/用户头像/暗色切换）
- Dashboard 首页：2×2 卡片网格（快速开始创作 + 最近创作 + 创作统计 + 热门模板）+ 快捷模板栏
- 创作页：左侧输入面板（需求/平台选择/内容类型/快捷模板）+ 右侧流式结果展示

## 设计风格

- **主题色**：Vibrant Orange `#FF6B35`
- **平台色**：抖音 `#FF0050` / 小红书 `#FF2442` / B站 `#FB7299` / 视频号 `#07C160` / 快手 `#FF4906`
- **侧边栏/顶栏**：`#1A0F2E` → `#2D1B3E` 深紫调渐变
- **背景**：`#FFFBF8` 暖白
- **字体**：Inter + PingFang SC，h1 32px/800

## 开发中遇到的困难

### 1. Prompt 花括号被 LangChain 误解析（KeyError）
与项目①相同的问题。`prompts.py` 中 `{功能}` `{场景}` `{效果}` `{产品名}` 被当成模板变量，导致流式调用抛出 `KeyError`，触发了 fallback 返回"LLM 服务未配置"。将花括号双写 `{{...}}` 解决。

### 2. 端口冲突——项目①占用了 8000
项目②的后端启动时 8000 端口已被项目①占用。因为没报明显错误（uvicorn 绑定失败时不会触发 start.bat 的异常检测），前端实际打到了项目①的旧服务。检索结果出现了"手机参数表""电商FAQ"等旧数据——这些文件只存在于项目①的 sample-data/ 中。
分配到独立端口 8202/3002 后解决。

### 3. 登录/注册页面品牌文字错误
项目②的 LoginView 和 RegisterView 最初复制自项目①，里面还写着"RAG 知识库问答系统""基于 AI 的电商商品智能问答助手"。完全替换为"AI自媒体内容助手""爆款标题·视频脚本·图文文案"。

### 4. 侧边栏→顶栏布局重构
两项目最初共用同一套侧边栏布局。项目②改为顶部导航条+全宽 Dashboard 需要：
- 重写 `AppLayout.vue`（56px 毛玻璃顶栏 + 用户徽章）
- 新建 `DashboardHome.vue`（2×2 卡片 + 平台色标签 + 模板栏 + 问候语）
- 修改 `router/index.ts`（默认路由改为 `/home`）
- 修改 `LoginView.vue`（登录后跳 `/home` 而非 `/studio`）
- ContentStudio 新增"返回首页"子标题栏

### 5. DashboardHome 统计数据造假
创作统计卡片中的"标题数/脚本数/文案数"是硬编码估算值（会话数 × 0.9/0.7/0.6），不是后端真实统计。标记为待完善。

### 6. ContentStudio 的 sessionId 参数未生效
路由定义了 `/studio/:sessionId` 但 `ContentStudio.vue` 的 `onMounted` 只处理 `route.query.template`，完全忽略 `route.params.sessionId`。从 Dashboard 点击"最近创作"跳转到指定会话时，不会加载历史消息。

### 7. 竞态条件——`start.bat` 中英文标题问题
与项目①相同，`start "SelfMedia-Backend"` 中的中文字符在 Windows cmd 中导致启动失败。已用纯英文标题修复。

### 8. Admin 页面暗色模式不完整
AdminDashboardView 和 AdminUsersView 的暗色模式只覆盖了标题颜色，缺少卡片背景、数据表格行、标签（Tag）、按钮的暗色样式。

## 知识库内容

| 文件 | 内容 | 规模 |
|------|------|------|
| `标题模板库.md` | 5平台24条标题模板 + 情绪化标题 + 数字型标题 | ~50条模板 |
| `脚本模板库.md` | 带货/测评/开箱/口播 4类脚本结构 | 完整4类 |
| `平台风格指南.md` ⭐新增 | 5平台详细指南 + AIDA/SCQA/PAS公式 | ~200行 |
| `爆款案例库.md` ⭐新增 | 18个真实爆款案例(跨5平台5品类) | ~150行 |

## 访问信息

| 项目 | 地址 |
|------|------|
| 前端 | http://localhost:3002 |
| 后端 | http://localhost:8202/docs |
| 账号 | admin / 123456 |
