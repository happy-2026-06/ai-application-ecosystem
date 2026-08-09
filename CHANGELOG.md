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
| ④ 素材管理平台 | 🟢 较完善 | 上传/标签/搜索/版本、Glassmorphism + Indigo 主题、原生上传替代组件库、图片预览、LLM打标 |
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

---
## 九、项目①-④ 全面安全审计 & 修复（2026/8/9）

> 对已完成的4个项目进行系统性代码审查，发现并修复 6 个严重 + 4 个高危 + 12 个中危 + 18 个低危问题。

### 发现的关键问题

| 严重度 | 数量 | 典型问题 |
|--------|:--:|------|
| 🔴 严重 | 6 | API Key 明文泄露(4项目)、项目④文件端点无认证、项目④导入错误 |
| 🟠 高危 | 4 | 弱密码/弱密钥、无暴力破解防护、CORS 端口不匹配 |
| 🟡 中危 | 12 | session.py 注释错误、system.py PUT 参数不规范、package.json 命名残留 |
| ⚪ 低优 | 18 | 未使用依赖、CSS 注释错误、locustfile 端口硬编码 |

---

### 难点 12：change-me-in-production 占位符 → 全项目密钥分离

| 项 | 内容 |
|------|------|
| **背景** | 审查发现 8 个 `.env`/`.env.docker` 文件中全部硬编码了真实 DeepSeek API Key（`sk-dfb0b6...`）+ 智谱 API Key（项目③），且 SECRET_KEY/JWT_SECRET_KEY 使用 `dev-secret-key`/`rag-jwt-secret-key` 等弱密钥 |
| **为什么危险** | `.env` 虽在 `.gitignore` 中，但 `.env.docker` 未被忽略（项目③）。一旦上传 Git，攻击者可无成本调用 API。而且所有项目共享同一个 API Key——一个项目泄露，全部沦陷 |
| **解决** | ① 替换所有真实 Key 为占位符（`your-deepseek-api-key-here`）② SECRET_KEY/JWT_SECRET_KEY 统一改为 `change-me-in-production-please`/`change-me-jwt-secret-please` ③ ADMIN_PASSWORD 从 `123456` 改为 `ChangeMe!2024` ④ 每个 `.env` 旁创建 `.env.example` 模板 ⑤ 根 `.gitignore` + 项目③ `.gitignore` 添加 `.env.docker` |
| **面试要点** | 这是一个**最小权限原则**的实践：开发环境也不应该用真实密钥——用占位符 + 文档说明去哪里申请。部署时通过 CI/CD 环境变量注入 |

### 难点 13：seed_admin_user 密码不同步 → 改 .env 后登录失败

| 项 | 内容 |
|------|------|
| **现象** | 改了 `.env` 中 `ADMIN_PASSWORD=ChangeMe!2024`，重启后端后用新密码登录失败；换旧密码 `123456` 反而能登录 |
| **排查过程** | ① 确认 `.env` 文件已保存 ② 确认 `config.py` 正确加载了新值（断点验证 `settings.ADMIN_PASSWORD`）③ 搜代码发现 `seed_admin_user()` 第 165 行：`if admin is None:` 只在用户不存在时创建——**已有用户不更新密码**！|
| **根因** | 原设计逻辑："密码只在首次创建时写入，之后由 Web UI 修改" → 但开发者改 `.env` 后预期密码跟配置走。这是一个**数据一致性假设错误**——代码假设 DB 是真相源，用户假设 .env 是真相源 |
| **解决** | 修改 `seed_admin_user()`：在 `else` 分支中加入 `verify_password(settings.ADMIN_PASSWORD, admin.hashed_password)` 检测，配置变更时自动重哈希并更新 DB。4 个项目全部修复 |
| **教训** | 配置驱动的值（.env）与状态驱动的值（DB）之间的一致性是需要主动维护的。不要假设"用户会通过 UI 改密码"——给开发者一个通过 .env 改密码的快速通道，然后**启动时自动同步** |

### 难点 14：项目④文件端点无认证 → 任意下载任意素材

| 项 | 内容 |
|------|------|
| **现象** | 审查时发现 `GET /api/assets/{asset_id}/file` 没有 `Depends(get_current_user)` 依赖 |
| **危害** | 任何人只要知道或猜到一个素材 ID（UUID），就能直接下载文件。对于 B 端 DAM 系统，素材往往是商业机密——这是**越权访问**漏洞 |
| **根因** | 所有 5 个 CRUD 端点中，4 个加了认证，唯独文件下载端点漏掉了——典型的**复制粘贴后忘记加认证** |
| **解决** | 添加 `current_user: User = Depends(get_current_user)` 到函数签名 |
| **面试要点** | 安全审查不是玄学——就是逐行检查每个端点的认证依赖。用 checklist 方式：这个端点是否需要登录？→ 有没有 Depends？→ 有没有所有权检查？ |

### 难点 15：项目④ forgot-password 用户枚举漏洞

| 项 | 内容 |
|------|------|
| **现象** | `forgot-password` 接口返回的 `hint` 字段区分了"用户存在"和"用户未注册"两种不同信息 |
| **危害** | 攻击者可以批量探测哪些用户名已在系统中注册（用户枚举），为后续暴力破解缩小范围 |
| **解决** | 移除 `hint` 字段，统一返回 `"如果该账号存在，密码重置链接已发送到注册邮箱"`——无论用户是否存在都返回相同消息 |
| **教训** | 忘记密码是**安全敏感**端点。正确的做法：始终返回成功消息 + 内部记录日志，不能给外部任何关于"用户是否存在"的信息 |

### 难点 16：项目④导入错误 → AI 打标静默失败

| 项 | 内容 |
|------|------|
| **现象** | `backend/app/api/assets.py` 第 127 行 `from app.rag.chain import get_llm_client`——但 `chain.py` 中函数名是 `get_llm`，不是 `get_llm_client` |
| **后果** | AI 自动打标功能上传后触发 `ImportError` → 被 try/except 静默吞掉 → 降级到关键词匹配打标。功能看起来"能用"但 AI 标签质量很差 |
| **教训** | 宽泛的 `except Exception` 会掩盖导入错误。关键路径的异常应该**分级处理**：`ImportError` 和其他异常分开，前者应该 fail-fast 而非静默降级 |

### 本次修复的其他优化

| 类别 | 改动 | 影响 |
|------|------|------|
| **配置规范化** | `package.json` name 从 `rag-frontend` → 各项目独立名称（`selfmedia-frontend`/`videofactory-frontend`/`asset-dam-frontend`） | ②③④ |
| **端口修复** | `locustfile.py` 压测端口、`generate_test_users.py` API 端口全部对齐各自项目 | ①②④ |
| **依赖清理** | 移除未使用的 `date-fns`、`highlight.js`、`@vicons/ionicons5` | ①②③④ |
| **注释修正** | `session.py` 中 DELETE 模式注释 → 实际使用的 WAL 模式说明 | ①②③④ |
| **API 规范化** | `system.py` PUT 端点从 query 参数 → Pydantic `ConfigUpdateRequest` body + Field 校验 | ①②③ |
| **CSS 修正** | `main.css` 顶部注释从"AI短视频脚本工坊" → 各自正确的项目名 | ①② |
| **知识库样本** | 项目② `generate_cs_samples.py` 从电商 FAQ → 自媒体内容（标题模板/脚本模板/平台风格/爆款案例） | ② |
| **侧边栏实时化** | 项目① `AppLayout.vue` 统计卡片从硬编码 → `onMounted` 动态拉取 API | ① |
| **大文件 OOM** | 项目① `kb.py` 上传从 `await file.read()` → 1MB 分块读取 | ① |
| **内存队列标注** | 项目① `HUMAN_AGENT_QUEUE` 添加"生产环境应迁移到 DB"注释 | ① |
| **弱密码启动警告** | 项目④ `main.py` 启动检查扩展覆盖常见弱密码（123456/password/admin） | ④ |
| **DB 命名** | 项目④ `DATABASE_URL_SYNC` 默认值 `rag_system.db` → `assetmgmt.db` | ④ |
| **邮箱域名** | 项目② `ADMIN_EMAIL` 从 `rag-system.local` → `selfmedia.local` | ② |
| **启动文宣** | 4个项目 `start.py` 标题/文案对齐到正确的项目名称 | ①②③④ |

### 代码审查的通用教训（面试用）

| 教训 | 说明 |
|------|------|
| **每个端点都要加认证** | 不能假设"其他端点都有，这个也应该有"——必须肉眼逐行确认 |
| **安全信息不能区分回显** | 忘记密码/登录失败这类接口，无论用户是否存在都返回相同消息 |
| **配置 ≠ 数据库** | .env 改了但 DB 里是旧值的场景很常见——启动时做同步，不要假设一致性 |
| **except Exception 是双刃剑** | 它能防止服务崩溃，但会掩盖 ImportError/NameError 这类该 fail-fast 的错误 |
| **复制粘贴是 bug 工厂** | 项目②的 generate_cs_samples 是项目①的、CSS 注释写的是项目③——跨项目复用代码时必须检查上下文 |

---

## 十、SSE 流式响应实现细节（面试加分）

| 项 | 内容 |
|------|------|
| **后端实现** | FastAPI `StreamingResponse` + `text/event-stream` MIME 类型 + `async generator` 逐 token 产出 |
| **事件协议** | 5 种事件类型：`thinking`（状态）、`retrieving`（检索中）、`token`（流式文字）、`sources`（引用来源）、`done`（完成+统计） |
| **前端实现** | 原生 `fetch()` + `ReadableStream` 手动解析 `data:` 行，配合 `AbortController` 支持取消 |
| **容错设计** | 三层回退：ChromaDB 向量搜索 → 简单关键词搜索 → 开发模式 mock 回答；`MOCK_LLM` 环境变量支持无 API 压测 |
| **清理管道** | `_clean_llm_output()` 用正则移除 LangChain 流式输出的内部 artifact（AIMessageChunk repr 片段、run ID 等） |
| **性能** | DB 中 `message_count` 用 `SELECT COUNT(*)` 计算而非客户端 +2，避免并发下计数漂移 |

---

*最后更新: 2026-08-09 (新增难点12-16：安全审计修复 + SSE 实现细节 + 项目④完整记录)*
*完整记录: README.md (项目列表+端口+启动方式) / CLAUDE.md (各项目开发手册)*

---

## 十一、项目④ AI素材管理平台 — 全面优化记录

### 4.1 项目定位
8个项目组合中**唯一的B2B企业级产品**（DAM 数字资产管理），填补C端(①②③)和B端之间的空白。

### 4.2 设计系统
| 项 | 值 |
|------|------|
| 主色 | `#6366F1` (Indigo/靛蓝) |
| 渐变 | `#6366F1 → #A855F7` |
| 侧边栏 | `#0F0B1E → #1A1230 → #0D0828` 深邃紫黑 |
| 暗色模式 | 主背景 `#0A0812`，卡片 `#12101A` |

### 4.3 前端 Glassmorphism 视觉重构（5个页面）

| 页面 | 改动 |
|------|------|
| **LoginView** | 12个浮动粒子 + 左侧功能列表 hover 动画 + 右侧玻璃拟态卡片(`backdrop-filter: blur(20px)`) + 登录按钮渐变+shimmer流光动画 + 密码可见性切换 + 错误类型区分(🚫/🔑/⛔) |
| **RegisterView** | 8个背景粒子 + 玻璃卡片 + 密码强度指示器(红/黄/绿三色进度条) + 确认密码✅/❌实时校验 + 品牌图标前缀 |
| **AssetGrid** | 原生`<input type="file">`替代 NaiveUI `n-upload` + 真实图片预览(`<img>` + `object-fit: cover`) + 三排序(时间/名称/大小) + hover缩放 |
| **SettingsView** | 40个emoji头像选择器 + 靛蓝主题突出选中态 |
| **AdminDashboard** | 4统计卡片(grid布局) + 素材概览区 + 正负反馈卡片 + 双API数据源(`/admin/dashboard`+`/assets/list`) |

### 4.4 后端升级

| 项 | 改动 |
|------|------|
| 认证对齐①②③ | `TokenResponse` 添加 `user` 字段、登录错误分三档("用户不存在"/"密码错误"/"账户禁用")、新增 `forgot-password` + `reset-password` + `escalate` 端点 |
| AI打标 | 从 mock 关键词匹配 → LLM 驱动（DeepSeek 分析文件名+类型，返回3-5个中文标签+描述） |
| 图片预览 | 新增 `GET /api/assets/{id}/file` 文件服务端点 |
| Docker | 添加 `p4_uploads` 命名卷持久化上传文件 |

### 4.5 跨项目关联
- 项目②(自媒体)生成的图文素材 → 可导入项目④统一管理
- 项目①(客服)的知识库图片 → 由项目④统一管理版本
- 项目③(脚本)的分镜参考素材 → 关联项目④的素材库
- 共享 PostgreSQL，独立 database `assetmgmt`

### 4.6 关键 Bug 修复

#### 难点 17：NaiveUI `n-upload` 组件与自定义上传冲突 → 422

| 项 | 内容 |
|------|------|
| **现象** | 浏览器上传素材始终返回 422 Unprocessable Entity，curl 测试却正常 |
| **排查过程** | ① curl 直连后端 8400 端口 → 200 OK ② curl 通过 nginx 3004 → 200 OK ③ 浏览器上传 → 422 Field required ④ 后端日志：`"Field required" loc:["body","file"]`——没收到 file 字段 ⑤ 发现 axios 实例设有默认 `Content-Type: application/json`，FormData 上传时这个头会覆盖浏览器自动生成的 `multipart/form-data; boundary=xxx` ⑥ 去掉默认头后仍 422——排查第二步：NaiveUI `n-upload` 默认 `defaultUpload: true`，组件内部尝试用自己 XHR 上传（没有设 `action` 属性），文件状态混乱 |
| **根因** | 两层问题叠加：(1) axios 默认 `Content-Type: application/json` 覆盖了 FormData boundary (2) NaiveUI `n-upload` 自带上传与手动 `@change` 回调冲突 |
| **解决** | ① 移除 axios 默认 Content-Type ② 用原生 `<input type="file" multiple>` + `@click` 触发 + `@change` 回调彻底替代 `n-upload`，绕开组件库黑盒 |
| **教训** | 组件库的上传组件做了太多内部状态管理，和自定义 axios 上传逻辑天然冲突。当上传场景简单（选文件→发请求），原生 `<input type="file">` 比任何组件库都可靠。**不要为"看起来像组件库风格"引入黑盒复杂度** |

#### 难点 18：Pinia persist 竞态条件 → 登录后立即 401

| 项 | 内容 |
|------|------|
| **现象** | 登录成功→上传成功→2秒后列表刷新 401→refresh 也 401→强制跳登录。每次登录后首次操作可用，后续全 401 |
| **排查** | curl 全链路(login→upload→list) 200。后端日志：浏览器 upload 200 → list 401 → refresh 401。说明 token 在上传后被替换为旧值。问题在 Pinia persist 插件异步写 localStorage 与 `router.push()` 跳转之间的竞态条件——新页面读到的可能是空/旧 token |
| **根因** | `authStore.login()` 设置 token → `router.push()` 跳转 → 新组件 `onMounted` 发请求，但 persist 插件写 localStorage 可能延迟。加上 `main.ts` 中 persist 插件被 try/catch 包裹，失败时清空 `rag-auth` 键（项目①旧代码残留） |
| **解决** | ① LoginView 登录成功后延迟 300ms：`await new Promise(r => setTimeout(r, 300))` ② 清理 main.ts 中错误的 try/catch 和 `rag-auth` 清除逻辑 |
| **教训** | 异步持久化 + 路由跳转 = 写后读竞态。解法：跳转前加微小延迟保证写入完成。面试话术："相当于你刚存了东西还没关抽屉就去拿" |

#### 难点 19：Docker 容器重建后上传文件丢失 → 命名卷持久化

| 项 | 内容 |
|------|------|
| **现象** | 上传的素材在容器重建后全部 404，只有 DB 记录还在 |
| **根因** | 上传目录在容器可写层内，`docker compose up --build` 重建后清空 |
| **解决** | docker-compose.yml 声明 `p4_uploads` 命名卷，挂载到 `/app/data/uploads` |

### 4.7 技术要点（面试速查）

| 点 | 一句话 |
|------|------|
| 为什么用原生 input 替代 n-upload | 组件库上传黑盒与自定义 axios 逻辑冲突，原生更可靠 |
| 为什么去掉默认 Content-Type | axios 默认 `application/json` 会覆盖 FormData 的 `multipart/form-data; boundary` |
| Pinia persist 竞态 | 持久化写入与路由跳转的异步时序问题，延迟 300ms |
| 图片预览实现 | 后端 FileResponse + 前端 `object-fit: cover` |
| Indigo 品牌 | B端需专业感——`#6366F1` 靛蓝 + 紫罗兰渐变 + 玻璃拟态 |
