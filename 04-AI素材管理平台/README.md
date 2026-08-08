# 项目④ — AI素材管理平台 (B端)

## 🎯 项目目标
企业数字资产管理: AI自动打标 + 多模态检索 + 版本管理

## 🏗️ 技术框架
Vue3 + TypeScript + NaiveUI + FastAPI + LangChain + DeepSeek + PostgreSQL + Docker

## 📄 状态: 🟢 核心功能已完成

## 🚀 快速启动
```bash
docker compose up -d
```
访问: http://localhost:3004  
管理员: admin / ChangeMe!2024

## 📦 已实现功能

### Backend (FastAPI)
- ✅ JWT 认证体系 (login/register/forgot-password/refresh)
- ✅ 素材 CRUD (upload/list/get/update/delete)
- ✅ AI 智能打标签 (LLM驱动 + mock关键词回退)
- ✅ 文件服务 (?token=query参数支持 <img>/<a> 直接访问)
- ✅ 素材统计 (total/tagged/storage/by_type/by_status)
- ✅ 热门标签 (popular tags top 20)
- ✅ 免费图库 (Lorem Picsum 集成)
- ✅ URL 导入 (从公开URL导入图片)
- ✅ 管理后台 (用户管理 + Dashboard素材统计)
- ✅ Pydantic Schemas (AssetResponse/AssetUpdateRequest/AssetStats)
- ✅ PostgreSQL 持久化

### Frontend (Vue3 + NaiveUI)
- ✅ 三栏布局: 左侧筛选 + 素材网格 + 右侧详情
- ✅ 登录/注册/忘记密码页 (靛蓝品牌主题 + 暗色模式)
- ✅ 上传队列 (进度条 + 批量上传 + 上传前重命名)
- ✅ 网格卡片重命名 (点击文件名直接编辑)
- ✅ 详情面板 (AI标签/手动标签/基本信息/状态切换)
- ✅ 文搜图 + 图搜图模式切换
- ✅ 免费图库弹窗 (浏览 + 导入)
- ✅ URL 导入
- ✅ 文件类型筛选 + 热门标签筛选
- ✅ 下载 (token自动附加)
- ✅ 侧边栏实时统计
- ✅ Pinia 持久化 (asset-auth)
- ✅ 404页面 + 路由守卫
- ✅ Docker 热更新 (Vite dev server + 卷挂载)

## 🔌 API 端点
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/login | 登录 |
| POST | /api/auth/register | 注册 |
| POST | /api/assets/upload | 上传素材 |
| GET | /api/assets/list | 素材列表(分页/筛选) |
| GET | /api/assets/{id} | 素材详情 |
| PATCH | /api/assets/{id} | 更新素材 |
| DELETE | /api/assets/{id} | 删除素材 |
| GET | /api/assets/{id}/file | 文件服务 |
| GET | /api/assets/stats | 素材统计 |
| GET | /api/assets/tags/popular | 热门标签 |
| GET | /api/assets/free-stock-photos | 免费图库 |
| POST | /api/assets/import-from-url | URL导入 |
| GET | /api/admin/dashboard | 管理后台 |
| GET | /api/admin/users | 用户管理 |

## 🔗 与项目①②③的关联
- 项目②(自媒体助手)生成的图文素材 → 可导入项目④统一管理
- 项目①(客服)的知识库产品图 → 由项目④统一管理素材版本
- 项目③(脚本)的分镜参考素材 → 关联项目④的素材库
