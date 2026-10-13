@echo off
title VialBot AI - Sistema de Operaciones Viales
echo ===================================================
echo   Iniciando VialBot AI - Concesion COSAD 25
echo   Interfaz Limpia, Moderna y Conectada a SQL Server
echo ===================================================
echo.

cd /d "%~dp0"
set PYTHONPATH=%CD%
set CHAINLIT_AUTH_SECRET=bGDy~G0ZtYY6vJ.TnHF/_uvV-=931TP@fALYXjDELHZMLYl@fJdm@ikKqJukn.Pa

:: Inicializar tablas SQLite para historial si no existen
.venv\Scripts\python.exe init_chainlit_db.py

:: Verificar que Ollama este activo
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2 -UseBasicParsing; Write-Host '[OK] Ollama activo en puerto 11434' -ForegroundColor Green } catch { Write-Host '[AVISO] Ollama no detectado en el puerto 11434' -ForegroundColor Yellow }"

echo.
echo ===================================================
echo  ACCESO LOCAL:    http://localhost:8001
echo  ACCESO EN RED:   http://192.168.80.161:8001
echo ===================================================
echo.

:: --host 0.0.0.0 permite la conexion desde otras computadoras de la red local
.venv\Scripts\chainlit.exe run app\chainlit_app.py --host 0.0.0.0 --port 8001 -w

pause
