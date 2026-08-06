@echo off
chcp 65001 >nul
title AI项目集群 — 启动面板
cd /d "%~dp0"

echo.
echo ================================================
echo   AI 项目集群 — 启动方式选择
echo ================================================
echo.
echo   [1] Docker 启动 (推荐)
echo       全自动管理, 开机自启, 永不丢数据
echo       需要 Docker Desktop 已在运行
echo.
echo   [2] 本地启动
echo       传统 Python + Node 方式
echo       需要本机已安装 Python 和 Node.js
echo.
echo ================================================

:ask
set CHOICE=
set /p CHOICE="请选择 (1 或 2): "

if "%CHOICE%"=="1" goto docker
if "%CHOICE%"=="2" goto local
echo 请输入 1 或 2
goto ask

:docker
echo.
echo 启动 Docker 模式...
call "%~dp0docker-start.bat"
goto end

:local
echo.
echo 启动本地模式...
python "%~dp0launcher.py"
goto end

:end
