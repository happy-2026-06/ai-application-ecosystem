@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════╗
echo ║       AI 项目集群 — 一键启动                  ║
echo ╚══════════════════════════════════════════════╝
echo.
echo [1/2] 启动 Docker 容器...
cd /d "%~dp0"
docker compose up -d
echo.
echo [2/2] 等待服务就绪...
timeout /t 5 /nobreak >nul
echo.
echo ╔══════════════════════════════════════════════╗
echo ║          全部启动完成！                       ║
echo ╠══════════════════════════════════════════════╣
echo ║  ① RAG客服    → http://localhost:3001        ║
echo ║  ② 自媒体助手  → http://localhost:3002        ║
echo ║  ③ 短视频工坊  → http://localhost:3000        ║
echo ║  ④ 素材管理    → http://localhost:3004        ║
echo ╠══════════════════════════════════════════════╣
echo ║  Portainer 管理 → http://localhost:9000       ║
echo ╚══════════════════════════════════════════════╝
echo.
pause
