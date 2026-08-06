@echo off
chcp 65001 >nul
title AI项目一键启动
cd /d "%~dp0"
python "%~dp0launcher.py"
