基础信息
22 岁 | 男 | AI 全栈开发实习生
https://github.com/happy-2026-06/ai-application-ecosystem
硕士在读 · 控制科学与工程 · 2029.06 毕业

专业技能
- 全栈开发：熟悉 Vue3 + FastAPI + PostgreSQL 全栈技术栈，独立完成 8 个 AI 应用从前端到后端到 Docker 部署的全链路开发，具备完整的工程化能力（CI/CD + Pre-commit + 单元测试 + 压力测试）。
- RAG 系统：熟悉 RAG 全链路设计与优化，包括文档解析（PDF/DOCX/Markdown 多格式）、中文感知分块、BGE-M3 嵌入、ChromaDB 向量存储、混合检索（向量 + BM25 + 图谱）、RRF 融合与 SSE 流式输出，具备检索质量评测（RAGAS/MRR/Hit）与性能调优经验。
- AI Agent：深入理解 Agent 架构设计原理，熟悉 Tool Calling、任务规划、流程编排、记忆系统等核心机制。独立实现过 AI Coding Agent（参考 Claude Code 架构）和多 Agent 协作平台（支持 Pipeline/Parallel/Vote/Debate 4 种编排模式）。熟悉 Claude Code、Cursor 等 AICoding 工具。
- 上下文工程：具备 Context Engineering 实践经验，设计并实现过 Skill 分层路由（解决 Token 成本与检索噪声）、自进化记忆沉淀（执行→反思→提炼→复用闭环）、分层上下文压缩（摘要预览→占位替换→按需检索→超限兜底）等机制。
- Python 后端：熟悉 FastAPI 异步框架、SQLAlchemy 2.0 异步 ORM、JWT 认证、SSE 流式响应、RESTful API 设计。了解数据库（PostgreSQL/SQLite WAL）、缓存（Redis/LRU）、消息队列基础概念。
- 前端能力：熟悉 Vue3 + TypeScript + NaiveUI + Pinia + Vite，具备组件化开发、状态管理、路由设计经验，能独立完成前端到后端的全链路开发。

项目经历
AI 应用生态平台｜AI 全栈开发｜2026.04 - 至今
项目简介：独立设计并开发 8 个 AI 应用组成的完整生态平台，覆盖 C 端（智能客服、内容生成、短视频脚本）、B 端（DAM 素材管理、销售培训系统）、中台（数据中心、多 Agent 协作平台、模型微调训练平台），通过 Docker Compose 统一编排 17 个容器，支持一键部署。项目已在 GitHub 开源。

技术栈：Vue3、FastAPI、LangChain、DeepSeek、ChromaDB、PostgreSQL、Docker、CI/CD

技术亮点：

RAG 全链路工程优化：围绕离线索引阶段（多格式文档解析、中文感知分块、BGE-M3 嵌入、ChromaDB 向量存储）、在线检索阶段（查询分类路由、向量 + BM25 混合检索、RRF 融合去重、Top-5 精准召回）与在线生成阶段（LCEL 链式组合、SSE 流式输出、来源引用溯源）完成全链路优化，支持三层优雅降级（ChromaDB→内存检索→纯 LLM），系统在任何环境下不崩溃。通过 SQLite WAL 模式 + PostgreSQL 迁移，将 50 并发失败率从 62% 降至 6%。

多 Agent 协作与跨系统联动：设计并实现多 Agent 协作平台，支持 Pipeline（流水线）/ Parallel（并行）/ Vote（投票 + LLM Judge 裁决）/ Debate（6 轮辩论 + 裁判裁决）4 种编排模式；实现跨项目数据飞轮：客服对话 → 数据中心清洗标注 → 模型微调训练 → 部署推理 API → 反馈优化，8 个项目通过 HTTP 联动，服务间 Docker 网络 DNS 通信。

工程性能与质量保障：建立三层代码质量保障体系（Pre-commit hooks → GitHub Actions CI 4 Job 矩阵 → 一键审查脚本），8 个项目 ruff 零问题、vue-tsc 零问题、pytest 全部通过。为每个项目编写专属 Locust 压力测试脚本（5 种测试标签、55 个真实业务场景问题池、3 种用户类权重分配），20 并发 × 60 秒压测 6/8 项目失败率 < 5%。

MiniCode｜AI Agent 开发｜2025.12 - 2026.04
项目简介：参考 Claude Code 架构设计并实现 AI Coding Agent，基于 Query Loop + Tool Use 构建任务执行闭环，重点设计 Skill 路由、自进化记忆沉淀、分层上下文压缩、多 Agent 协作与权限安全审查等机制，提升复杂任务下的执行准确率、上下文稳定性与推理效率。

技术栈：Agent、Tool Calling、Memory System、Prompt Cache、Claude Code、Python

技术亮点：

Skill 能力体系：设计 Skill 分层路由系统，将原子 Tool、高层 Skill 与 Skill 目录分层组织，结合任务意图识别、元信息标签、适用边界与示例进行二阶段召回与精排，解决 Skill 自进化增长下的检索噪声、功能重叠、召回空间过大与 Token 成本高问题。

自进化记忆沉淀：设计自进化记忆沉淀机制，将执行过程中的程序性经验、情景记忆、用户画像自动提炼为可复用记忆资产，构建 "执行–反思–提炼–分类存储–索引更新–按需复用" 的闭环，实现跨会话复用、错误修复加速、Skill 能力生长。

分层上下文压缩：设计分层上下文压缩机制，将大工具结果外化、缓存友好型占位压缩与结构化笔记摘要结合，构建 "摘要预览–占位替换–按需检索–超限兜底" 的上下文治理闭环，在保证长会话稳定性的同时提升 Prompt Cache 收益并降低 Token 成本。

中心化多 Agent 协作：设计中心化多 Agent 协作架构，以主 Agent 统一规划、审批与质量控制，子 Agent 以 Tool Call 方式受控执行，通过不移交控制权、最小化结果传递、工具权限约束与路径边界限制保障安全性，支持 Fork / Worktree / Agent Team 等协作模式。

权限与安全审查：构建规则过滤、工具自检、AI 风险分类 (Prompt 注入防御) 与人工确认的多层审查链路，提升 Agent 在真实开发环境下的可控性与安全性。

面向个人的多模态 RAG 知识库问答系统｜AI 应用开发｜2026.01 - 2026.05
项目简介：面向个人知识管理场景的多模态 RAG 问答系统，支持 PDF、Markdown、图片等常见知识源，围绕离线索引阶段、在线检索阶段、效果测评、增量索引与缓存加速完成全链路工程优化，提升个人知识场景下的问答准确率与系统响应效率。

技术栈：Python、LangChain、Chroma、BM25、RAGAS、OCR、VLM

技术亮点：

离线索引优化：重点优化了复杂 PDF 和 Markdown 的解析流程；针对包含图片的文档，结合 OCR 与 VLM 提取文本和语义信息；同时对切分后的 chunk 进行清洗和元数据绑定，并建立 BM25 与稠密向量的混合索引。

在线检索优化：设计并优化 RAG 在线检索链路，涵盖查询改写、问题路由、多路召回、Rerank 精排、上下文拼装与引用核查机制，并通过低置信度二次检索机制提升召回效果和回答质量。

测评与工程性能优化：基于 RAGAS 测评框架、MRR、Hit 搭建检索与生成联合评估流程，实现对切分策略、召回参数与重排模型的量化分析。

增量索引、分层缓存与工厂模式解耦：设计基于文档 Hash 的增量索引与热更新机制，支持文档新增、修改、删除的快速同步；将文档解析、切块、向量化、查询改写、Rerank 等链路解耦为可插拔模块，便于效果对比；通过分层缓存复用 QA 结构及索引结构。

教育背景
自动化 (本科)　2022.09 - 2026.06
控制科学与工程 (硕士)　2026.09 - 2029.06
