@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════╗
echo ║       停止所有 AI 项目容器                    ║
echo ╚══════════════════════════════════════════════╝
echo.
cd /d "%~dp0"
docker compose down
echo.
echo ✅ 所有容器已停止！
echo.
pause
