# 8个AI应用项目 — 升级日志 & 面试复盘

> 面试用速查文档：技术栈 → 架构设计 → 核心难点 → Bug解决记录

---

## 一、技术框架

```
┌─────────────────────────────────────────┐
│  前端: Vue3 + TypeScript + NaiveUI      │
│        Pinia + Vue Router + Vite        │
│        MarkdownIt + Inter 字体          │
├─────────────────────────────────────────┤
│  后端: Python FastAPI + SQLAlchemy 2.0  │
│        JWT 认证 + SSE 流式              │
│        异步 async/await                 │
├─────────────────────────────────────────┤
│  AI:  LangChain + DeepSeek v4 Flash     │
│        ChromaDB 向量检索                │
│        RAG (检索增强生成)                │
├─────────────────────────────────────────┤
│  数据: SQLite WAL (开发)                │
│        PostgreSQL + Redis (生产/Docker)  │
├─────────────────────────────────────────┤
│  部署: Docker Compose + Nginx            │
│        8项目端口独立互不冲突             │
└─────────────────────────────────────────┘
```

## 二、8个项目概览

| # | 项目 | 定位 | 核心功能 | 端口 |
|---|------|------|---------|:---:|
| ① | RAG智能客服系统 | C端 | 知识库问答、转人工、引用溯源 | `8101:3001` |
| ② | AI自媒体内容助手 | C端 | 爆款标题/脚本/图文/建议生成，5平台适配 | `8202:3002` |
| ③ | AI短视频脚本工坊 | C端 | 分镜表+口播稿+拍摄建议 | `8303:3003` |
| ④ | AI素材管理平台 | B端 | 素材上传/自动标签/文搜图/版本管理 | `8404:3004` |
| ⑤ | AI销售培训系统 | B端 | AI扮演客户/角色扮演/多维度打分 | `8505:3005` |
| ⑥ | AI数据中心平台 | 中台 | 数据采集→清洗→标注→版本→质量报告 | `8606:3006` |
| ⑦ | MCP多智能体协作平台 | 中台 | 多Agent任务拆解+协作调度 | `8707:3007` |
| ⑧ | AI模型微调训练平台 | 中台 | QLoRA微调+A/B对比+一键部署API | `8808:3008` |

---

## 三、核心难点 & Bug 解决（面试重点）

### 难点 1：LangChain Prompt 花括号冲突

| 项 | 内容 |
|------|------|
| **现象** | LLM 调用抛出 `KeyError: Input to ChatPromptTemplate is missing variables {功能, 场景, 效果}` |
| **根因** | `prompts.py` 中写了 `{功能} + {场景} = {效果}` 作为给 AI 参考的示例模板，LangChain 的 `ChatPromptTemplate` 把所有 `{xxx}` 都当成变量去匹配输入字典 |
| **解决** | 双写花括号转义：`{{功能}} + {{场景}} = {{效果}}`，LangChain 就会把它们当作普通文本 |
| **影响范围** | 项目①②③的 `prompts.py` 都需要修复 |
| **教训** | LangChain 的模板语法与 Markdown/代码示例中的花括号冲突是常见坑，遇到 `KeyError` 且变量名是中文时第一时间排查这个 |

### 难点 2：两个项目端口冲突 → 连环错

| 项 | 内容 |
|------|------|
| **现象** | 项目②回复"LLM 服务未配置"、检索到的知识库内容是项目①的旧数据（手机参数表、电商FAQ） |
| **排查过程** | ① 检查 `.env` → API Key 正常 ② 检查 chain 代码 → 正常 ③ `curl http://localhost:8000/` → 返回 `"name":"RAG智能客服系统"`（项目①的名字！）→ **原来 8000 端口被项目①占了** |
| **根因** | 两个项目默认都用 8000 端口启动，先启动的项目占了端口，后面的项目悄悄启动失败。所有请求都打到旧服务上 |
| **解决** | 8个项目分配独立端口，互不冲突（8101/8202/8303…），同时同步更新 `.env`、`vite.config.ts`、`start.bat` 中所有端口引用 |

### 难点 3：三栏客服台布局重构

| 项 | 内容 |
|------|------|
| **背景** | 项目①和②原本共用一套「侧边栏+主内容」布局，完全没有差异 |
| **目标** | ① 改成三栏客服台（侧边统计 + 会话列表 + 聊天区），② 改成顶栏+Dashboard首页 |
| **关键改动** | ① 侧边栏顶部新增3个统计卡片、会话列表从 ChatView 移到 AppLayout 管理、ChatView 只负责消息展示 ② 侧边栏完全废弃 → 56px毛玻璃顶栏 + 新建 `DashboardHome.vue`（2×2卡片+模板栏） |
| **踩坑** | `ChatView` 移除 session 面板后，`currentId` 计算属性回退逻辑有问题——返回 `/chat` 时不显示欢迎页；`submitEdit` 的 `splice(idx)` 只有一个参数会删除所有后续消息而非单条 |

### 难点 4：Windows start.bat 中文标题启动失败

| 项 | 内容 |
|------|------|
| **现象** | 双击 `start.bat` 无反应或报"系统找不到文件" |
| **根因** | Windows `start "窗口标题"` 命令中，标题含特定中文字符会被解析为文件名 |
| **解决** | 所有 `start` 命令使用纯英文标题（如 `start "P1Backend"`） |

### 难点 5：Docker 容器内 Vite 代理失效

| 项 | 内容 |
|------|------|
| **现象** | 前端容器内 `/api` 请求全部 502/连接拒绝 |
| **根因** | Vite proxy target 写的是 `http://localhost:8202`，但 Docker 容器内 localhost 指向自身而非宿主机 |
| **解决** | Docker 环境 proxy target 改为容器 service name（如 `http://backend:8202`），Nginx 配置同步更新 |

### 难点 6：spaCy 依赖导致文档加载器崩溃

| 项 | 内容 |
|------|------|
| **现象** | 上传文档后加载失败，`ModuleNotFoundError: spacy` |
| **根因** | LangChain 的 `UnstructuredLoader` 底层依赖 spaCy 模型，但 `requirements.txt` 中未安装 |
| **解决** | 改用不依赖 spaCy 的 `TextLoader` + 自定义 splitter 绕过，减少额外依赖 |

### 难点 7：SQLite → WAL → PostgreSQL 性能三阶段

| 项 | 内容 |
|------|------|
| **场景** | 50人并发压测 |
| **第一阶段** | SQLite 标准模式 → **62% 请求失败**（锁竞争） |
| **第二阶段** | 启用 WAL 模式 + 5项 PRAGMA 优化 → **失败率降至 30%** |
| **第三阶段** | 切换 PostgreSQL → **失败率 6%** |
| **PRAGMA 优化** | `journal_mode=WAL`, `synchronous=NORMAL`, `cache_size=-8000`, `busy_timeout=5000`, `foreign_keys=ON` |

### 难点 8：Windows 浏览器上传中文文件名乱码（GBK→Latin-1→UTF-8 编码链）

| 项 | 内容 |
|------|------|
| **现象** | 知识库上传 `小红牛电商产品知识库.md`，数据库存成了 `ÃÂ¡ÃÂºÃ...` 这种乱码 |
| **排查过程** | ① 检查后端收到 `file.filename` 的值 → 已是乱码 ② 确认浏览器发送的是 GBK 编码的 multipart 文件名 ③ Python FastAPI 默认用 Latin-1 解码 multipart header → GBK 字节被错误解释为 Latin-1 字符 |
| **根因** | 编码链：原始 GBK 字节 → Latin-1 错误解码 → 产生乱码字符串。中间经过 `encode('latin-1')` 能还原 GBK 字节，再 `decode('gbk')` 得到正确中文 |
| **解决** | 写 `_fix_filename()` 函数：`name.encode('latin-1').decode('gbk')`，修复后同时在 DB + 磁盘文件上更新 |
| **教训** | 跨国/跨平台文件上传的编码问题是隐蔽坑。RFC 5987 规定 multipart 文件名用 UTF-8，但部分 Windows 系统仍用系统 locale（GBK）。防御方案：在接口入口检测并修复，而非依赖客户端规范 |

### 难点 9：上传后文档一直"等待中"→ 异步改同步的架构权衡

| 项 | 内容 |
|------|------|
| **现象** | 上传文档后状态一直是 `pending`，刷新不更新，点预览也看不了。后来发现是容器重启中断了后台 `asyncio.create_task` |
| **原方案** | 上传 API 先存文件 → 返回 `pending` → `asyncio.create_task` 后台处理。优点：响应快。缺点：任务不可靠，重启即丢失 |
| **新方案** | 上传 API 同步调用 `process_document_async()` → 处理完再返回。优点：用户看到的一定是 `completed`，永不丢失。缺点：大文件上传需等几秒 |
| **面试要点** | 这是一个典型的「用延迟换可靠性」的架构决策。面对后台任务可靠性问题时，不是加消息队列（过度设计），而是先评估同步处理是否够用——对 50MB 以内的文档，处理时间 <5 秒，同步完全可行。**选型原则：能同步就不异步，消息队列是最后手段** |
| **补充保障** | 在 `main.py` 的 `lifespan` 启动钩子中加恢复逻辑：扫描所有 `pending`/`processing` 状态文档并自动重处理，即使未来再出现意外中断也能自愈 |

### 难点 10：DOCX/PDF 文件无法预览 → LangChain Loader 提取文本

| 项 | 内容 |
|------|------|
| **现象** | 知识库上传了 `Java 实习面试.docx`，点预览显示"不支持预览 docx 文件，仅支持 txt/md/csv" |
| **根因** | 后端预览接口只处理 txt/md/csv（用 `open().read()` 直接读），docx 是 ZIP 压缩的 XML 格式，无法直接文本读取 |
| **解决** | 用 LangChain 的 `Docx2txtLoader`（底层是 `python-docx` 解 ZIP 读 XML）和 `PyPDFLoader`（底层是 `pypdf`）提取纯文本。复用现有的 `loader.py` 模块，不引入新依赖 |
| **关键代码** | `from langchain_community.document_loaders import Docx2txtLoader; loader = Docx2txtLoader(file_path); docs = loader.load()` |
| **教训** | 二进制文档（docx/pdf）和文本文件（txt/md）是两个世界。不要用 `open().read()` 处理一切——先判断文件类型，再选对应的 Loader |

### 难点 11：Docker volume 只读 + Vite 缓存 → 前端改动不生效

| 项 | 内容 |
|------|------|
| **现象** | 修改了 `AdminKBView.vue`，`docker compose restart` 后页面还是旧的，完全没变化 |
| **排查** | ① `docker cp` 注入文件 → "mounted volume is read-only" ② 发现前端代码在 Docker 构建时被打包进镜像，volume 是只读挂载 ③ `docker exec` 进去手动改 → Read-only file system |
| **根因** | Vite 开发模式下，`node_modules/.vite/` 缓存了编译后的模块。代码更新后缓存未失效，Vite 继续从旧缓存读取 |
| **解决** | 方案1：`docker exec p1-frontend rm -rf /app/node_modules/.vite` 清 Vite 缓存 + `docker restart`（临时）。方案2：`docker compose up --build` 重建镜像（永久） |
| **教训** | 前端容器化开发要关注两点：① Vite HMR 在 Docker 内的工作方式（需要 `--host 0.0.0.0`）② 依赖缓存（`.vite/`、`node_modules/`）的清理机制。开发阶段建议用 volume mount 而非 COPY 进镜像

---

## 四、项目① 重要升级记录

### 布局 & UI
| 日期 | 改动 | 说明 |
|------|------|------|
| 8/4 | 三栏客服台布局 | 侧边200px(统计+导航) + 会话列表260px + 聊天flex，替代旧单栏 |
| 8/4 | 专业蓝主题 `#2563EB` | 侧边栏深蓝渐变、用户气泡蓝紫渐变、AI气泡浅灰、Inter字体 |
| 8/4 | LoginView 美化 | 左侧蓝渐变+毛玻璃效果、右侧卡片16px圆角+阴影、H5暗色模式补全 |

### 功能修复
| 日期 | Bug | 修复 |
|------|-----|------|
| 8/4 | 返回 `/chat` 不显示欢迎页 | watch 添加 else 分支清除 session |
| 8/4 | 转人工只生成本地消息 | 接入 `POST /api/chat/escalate` 真实 API |
| 8/4 | 编辑消息静默删除后续对话 | `splice(idx, 1)` 只删1条而非 tail |
| 8/4 | 切换会话闪烁 | 加载新消息前先 `messages = []` |
| 8/4 | 无 404 路由 | 添加 `/:pathMatch(.*)*` 捕获所有 |
| 8/8 | spaCy 依赖崩溃 | 改用 TextLoader 绕过 |
| 8/8 | DOCX/PDF 无法预览 | 接 LangChain Docx2txtLoader + PyPDFLoader 提取文本 |
| 8/8 | Windows 上传中文文件名乱码 | `_fix_filename()`：GBK→Latin-1→UTF-8 编码修复 |
| 8/8 | 上传后文档一直 pending | 异步改同步处理 + 启动恢复（扫描 pending 自动重处理） |
| 8/8 | 预览 API 返回 401 | Pinia 持久化 key 是 `token`，前用 `localStorage.access_token` |
| 8/8 | Docker Vite 缓存不更新 | 清 `.vite/` 缓存 + 重建镜像 |
| 8/8 | Docker 文档数据丢失 | 添加 `p1_uploads` + `p1_chroma` 命名卷持久化 |

---

## 五、项目② 重要升级记录

### 布局 & UI
| 日期 | 改动 | 说明 |
|------|------|------|
| 8/4 | 侧边栏 → 顶部导航 | 56px毛玻璃顶栏，全宽布局 |
| 8/4 | 新建 DashboardHome | 2×2卡片(快速创作/最近会话/统计/模板) + 快捷模板栏 |
| 8/4 | 活力橙主题 `#FF6B35` | 5平台品牌色标签(抖红B视快)、暖白背景 #FFFBF8、h1 32px/800 |
| 8/4 | LoginView 品牌修复 | "RAG知识库问答"→"AI自媒体内容助手"，4个功能卡片全部替换 |
| 8/7 | 内容扩充 | 新增 `平台风格指南.md` + `爆款案例库.md`(18案例)，扩充标题模板库(50+条) |

### 功能修复
| 日期 | Bug | 修复 |
|------|-----|------|
| 8/4 | 登录跳 `/chat`→白屏 | 改为 `/studio` 后改为 `/home` |
| 8/4 | ContentStudio 忽略 sessionId | onMounted 中读取 `route.params.sessionId` 加载历史 |
| 8/4 | Dashboard 统计造假 | 移除虚假乘法系数，只展示真实数据 |
| 8/4 | 导航"知识库"→"管理" | 修正自媒体助手的品牌用语 |
| 8/4 | Pinia 持久化 key `rag-auth` | 改为 `creator-auth` |
| 8/4 | ContentStudio.vue.bak | 删除遗留备份文件 |
| 8/8 | 登录页演示密码 | 更新为 `ChangeMe!2024` |

---

## 六、Docker 化部署（2026/8/6-8/7）

| 日期 | 改动 | 影响项目 |
|------|------|---------|
| 8/6 | 3个项目 Docker 化 | ①②③ 完整 Docker Compose + Nginx |
| 8/6 | 启动脚本重写 | 一键启动 + 守护进程检测 + 冷启动重试 |
| 8/6 | 清理冗余文件 | 删除 39 个文件 / 2801 行死代码 |
| 8/7 | Docker 热更新 | `--reload` + volume mount 实现开发模式热重载 |
| 8/7 | Vite 代理修复 | Docker 内使用 service name 而非 localhost |
| 8/7 | Nginx 禁用缓存 | 修复 Docker 环境前端更新不生效 |

---

## 七、项目③-⑧ 初始框架（2026/8/5-8/8）

| 项目 | 状态 | 特色 |
|------|:--:|------|
| ③ 短视频脚本工坊 | 🟡 框架已建 | 分镜表 + 口播稿 + 拍摄建议 + B-roll 模板 |
| ④ 素材管理平台 | 🟢 较完善 | 上传/标签/搜索/版本、Glassmorphism + Indigo 主题、统计API合并 |
| ⑤ 销售培训 | 🟡 框架已建 | AI 扮演客户 + 角色扮演 + 多维度打分 |
| ⑥ 数据中心 | 🟡 框架已建 | 数据底座，为其他项目提供数据支撑 |
| ⑦ 多智能体 | 🟡 框架已建 | 多 Agent 协作调度 |
| ⑧ 模型训练 | 🟡 框架已建 | QLoRA 微调 + A/B 对比 + RLHF |

---

## 八、面试常见追问预案

**Q: 为什么选 LangChain 而不是直接调 API？**
> LangChain 提供了统一的 Prompt 模板、Chain 组装、向量检索集成。8个项目共享同一套 RAG pipeline（chain.py / retriever.py / vectorstore.py），新增项目只需换 Prompt 模板和 sample-data，开发效率高。

**Q: 8个项目如何避免代码重复？**
> 每个项目独立完整（可单独运行），共享技术底座设计模式（Vue3+FastAPI+LangChain）。通过端口规划和统一启动脚本管理。sample-data 是每个项目的差异化核心。

**Q: 遇到的最难 bug 是什么？**
> 有两个：
> 1. **GBK 编码乱码链**——表象是中文文件名变乱码，排查了数据库、前端、HTTP header 才发现是 Windows 浏览器→Python FastAPI 的多层编码错误。用 `encode('latin-1').decode('gbk')` 修复。
> 2. **端口冲突的连环错**——表象是 LLM 不工作、检索内容不对，排查了 API Key、代码逻辑、环境变量才发现是旧进程占了端口。最后引入 8 端口独立规划从根源解决。

**Q: 为什么 SQLite 换 PostgreSQL？**
> 50并发下 SQLite 锁竞争严重(62%失败)，WAL 模式改善到 30% 但仍有瓶颈。PostgreSQL 支持真正并发写入，失败率降至 6%。

**Q: 上传的文件为什么有时候要等好久？**
> 旧版用 `asyncio.create_task` 后台处理，上传即返回 `pending`。问题：容器重启后台任务就丢了。新版改为同步处理——上传接口等处理完才返回，用户看到的一定是 `completed`。对于 50MB 以内的文档处理 <5 秒，同步完全可行。遵循"能同步就不异步"原则。

**Q: DOCX/PDF 这类二进制文档怎么处理的？**
> 用 LangChain 的 `Docx2txtLoader`（python-docx）和 `PyPDFLoader`（pypdf）提取纯文本，再分 chunk 存入向量库。不能直接用 `open().read()`——docx 本质是 ZIP 压缩的 XML，需要用专门的解析器。

**Q: Docker 数据持久化怎么做的？**
> 关键两步：① `docker-compose.yml` 中声明命名卷（`p1_uploads`、`p1_chroma`），容器删除后数据保留。② `main.py` 启动钩子中扫描 DB 的 completed 文档，重新索引到内存检索器。即使 ChromaDB 挂了也不影响服务。

**Q: 暗色模式怎么实现的？**
> 双层方案：NaiveUI 的 `darkTheme` 负责组件，自定义 `[data-theme="dark"]` CSS 选择器在 `<html>` 上切换，Pinia store 持久化用户偏好到 localStorage。

---

*最后更新: 2026-08-09 (新增难点8-11 + 面试预案补充)*
*完整记录: README.md (项目列表+端口+启动方式) / CLAUDE.md (各项目开发手册) / ARCHIVE.md (项目①②详细存档)*
