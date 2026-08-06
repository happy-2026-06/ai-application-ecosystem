@echo off
chcp 65001 >nul
title RAG智能客服系统 - 01
cd /d "%~dp0"
python "%~dp0start.py"
