# 变更记录 — AI短视频脚本工坊

## v2.1 — 2026-08-05：四大新功能 — 一站式短视频生产管线

### 🎙️ AI配音 (TTS)
- **技术方案**：Microsoft Edge-TTS（免费无限量，神经网络中文语音）
- **语音库**：25种中文语音（普通话男/女声 + 粤语 + 台湾普通话）
- **功能**：自动从脚本提取口播文案 → 选择语音角色 → 调节语速 → 生成 MP3
- **新增文件**：`backend/app/services/tts_service.py`（语音目录 + 文本提取 + 流式生成）
- **API端点**：`GET /api/generation/tts/voices`、`POST /api/generation/tts`、`GET /api/generation/tts/download/{filename}`

### 🎬 AI视频生成
- **技术方案**：智谱 CogVideoX-2（官方 Python SDK，新用户 50 元免费额度）
- **功能**：根据分镜"画面内容"描述 → 提交视频生成任务 → 异步查询状态
- **支持模型**：CogVideoX-2 (高质量) + CogVideoX-Flash (快速)
- **新增文件**：`backend/app/services/video_service.py`（任务提交 + 状态查询 + 批量生成 + 下载）
- **API端点**：`POST /api/generation/video`、`GET /api/generation/video/{task_id}`

### 📝 字幕导出 (SRT/ASS)
- **技术方案**：纯后端解析 + pysrt 库（无需外部 API）
- **SRT 格式**：通用字幕格式，兼容所有播放器和编辑软件
- **ASS 格式**：高级字幕格式，支持样式定义（字体/颜色/描边/位置）
- **智能时间码**：从分镜表和口播文字长度自动计算时间轴
- **新增文件**：`backend/app/services/subtitle_service.py`（表格解析 + SRT/ASS 生成 + 文件导出）
- **API端点**：`POST /api/generation/subtitles`、`GET /api/generation/subtitles/download/{filename}`

### ✂️ 剪映对接 (CapCut 草稿生成)
- **技术方案**：自研 draft_content.json 生成器（无需第三方库）
- **功能**：解析分镜表 → 生成时间线轨道（视频/音频/字幕）→ 导出完整草稿文件夹
- **输出格式**：标准剪映 Windows 桌面版 draft_content.json + draft_meta_info.json
- **使用方式**：下载 ZIP → 解压到剪映草稿目录 → 在剪映中打开编辑
- **新增文件**：`backend/app/services/capcut_service.py`（素材构建 + 轨道生成 + 导出打包）
- **API端点**：`POST /api/generation/capcut-draft`、`GET /api/generation/capcut-draft/download/{folder_name}`

### 🧩 后端架构变更
- **config.py**：新增 TTS/视频/字幕/剪映 配置项
- **models/message.py**：新增 `assets` JSON 字段（存储生成的资源引用）
- **api/__init__.py**：注册 generation 路由
- **api/generation.py**：统一生成功能 API（9 个端点）
- **requirements.txt**：新增 `edge-tts`、`zhipuai`、`pysrt`

### 🖥️ 前端变更
- **api/generation.ts**：新增前端 API 模块
- **ScriptStudio.vue**：结果工具栏新增 4 个功能按钮 + 4 个配置弹窗
  - 🎙️ AI配音弹窗：语音选择 + 语速调节 + 生成/下载
  - 📝 字幕导出弹窗：格式选择(SRT/ASS) + 语速设置 + 内容预览 + 下载
  - 🎬 AI视频弹窗：模型选择 + 分镜多选(避免并发超限) + 自动轮询 + 视频播放器 + 下载
  - ✂️ 剪映对接弹窗：项目名称 + 分镜结构预览 + 下载草稿包

### 🐛 Bug 修复 (v2.1)
- **subtitle_service.py / capcut_service.py**：LLM 多表格 Markdown 解析越界 IndexError — 新增列数校验自动跳过非分镜表
- **video_service.py**：智谱 SDK 版本兼容 — `generations.create` → `generations()`，`generations.retrieve` → `retrieve_videos_result()`
- **TimestampMixin**：时间戳从 UTC 改为北京时间(UTC+8)，修复历史记录"8小时前"显示错误
- **数据库迁移**：`ALTER TABLE messages ADD COLUMN assets JSON` — 补充缺失字段

### 🎨 UI 增强 (v2.1)
- **🎙️ AI配音弹窗**：动画进度条 + 内置音频播放器（在线试听，无需下载）
- **📝 字幕导出弹窗**：动画进度条 + 黑底代码预览框（直接查看字幕内容）
- **🎬 AI视频弹窗**：分镜勾选器（默认只选1个，避免并发超限）+ 进度条 + 20s自动轮询 + 内嵌视频播放器
- **✂️ 剪映对接弹窗**：动画进度条 + 分镜结构预览列表
- **历史记录侧边栏**：标题智能提取产品名 + 批量删除模式 + 时间修正

---

## v2.0 — 2026-08-05：前端全面改造

### 🎨 设计系统重构
- **新主题**：电影级金色 + 深色炭灰色（`#C8A951`），与项目①专业蓝、项目②活力橙明确差异化
- **CSS变量体系**：`main.css` 完整的设计令牌系统（`--primary`, `--bg-body`, `--text-primary` 等18个变量）
- **设计令牌**：新增 `assets/styles/tokens.ts` — TypeScript常量供组件引用
- **字体**：加载 Google Fonts Inter（400/500/600/700/800），搭配 PingFang SC
- **NaiveUI主题**：配置 `themeOverrides` 统一组件颜色

### 🐛 Bug修复
- **LoginView.vue**：补充完整 `<script setup>` + `<style scoped>`（之前缺失导致页面崩溃）
- **RegisterView.vue**：补充完整 `<script setup>` + `<style scoped>`（同上）
- **AppLayout.vue**：修复路由 `/admin/kb` → `/admin/dashboard`（之前路由不存在）
- **AdminUsersView.vue**：移除死链接"知识库"按钮
- **main.css**：修正注释头（之前写的是"RAG Knowledge Base Q&A System"）
- **main.css**：修正暗色滚动条选择器 `[theme='dark']` → `[data-theme='dark']`
- **authStore.ts**：持久化key `rag-auth` → `script-studio-auth`
- **main.ts**：同步清理以上key名
- **router/index.ts**：新增 404 捕获路由

### 🧩 新增共享组件
- **EmptyState.vue**：统一空状态组件（浮动动画图标 + 标题 + 描述 + 操作槽）
- **PageHeader.vue**：统一页面标题组件（金色左边框 + 标题 + 副标题 + 操作槽）
- **LoadingSpinner.vue**：统一加载组件（金色旋转器 + 提示文字 + 平台标签脉动）

### 🎬 视图改造
- **AppLayout.vue**：侧边栏改为炭灰渐变 + 金色品牌名渐变文字 + 金色导航高亮 + 角色"导演/创作者"
- **ScriptStudio.vue**：全面重写 — 使用共享组件、平台品牌色芯片选择器、增强Markdown样式（金色表头/渐变下划线/斑马纹/暗色全覆盖）、历史搜索、确认删除
- **AdminDashboardView.vue**：全面重写 — 统计卡片彩色顶部边框、知识库/反馈卡片、暗色模式
- **AdminUsersView.vue**：使用PageHeader、数据表格暗色覆盖
- **SettingsView.vue**：使用PageHeader、头像选中金色边框、暗色覆盖完善

### 📄 新增页面
- **NotFoundView.vue**：404页面 — "场景未找到"（电影主题文案）

---

## v1.0 — 2026-08-04：初始版本
- 三种视频导演模式（带货/测评/开箱）+ 自动模式检测
- SSE流式脚本生成
- 历史会话管理
- 用户认证 + 管理后台
- 18个测试用例通过
