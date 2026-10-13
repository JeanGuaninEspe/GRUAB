@echo off
title Open WebUI Sandbox - VialBot COSAD
echo ===================================================
echo   Iniciando Sandbox de Open WebUI (Modo Aislado)
echo ===================================================
echo.
echo Conectando Open WebUI a FastAPI con acceso a SQL Server:
echo   - Backend Proxy: http://127.0.0.1:8000/api/v1/ai
echo   - Modelo: vialbot-sql (con datos reales de SQL Server)
echo.
echo Abriendo en: http://localhost:8080
echo.

set OPENAI_API_BASE_URL=http://127.0.0.1:8000/api/v1/ai
set OPENAI_API_KEY=sk-vialbot-local
set WEBUI_PORT=8080

uv run --with "torch==2.4.1" --with "open-webui" open-webui serve --port 8080

pause
