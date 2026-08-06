@echo off
chcp 65001 >nul
title AI项目集群 — 停止
cd /d "%~dp0"

echo.
echo 停止所有服务...
docker compose down
echo.

echo ================================================
echo   全部服务已停止
echo ================================================
echo.

pause
