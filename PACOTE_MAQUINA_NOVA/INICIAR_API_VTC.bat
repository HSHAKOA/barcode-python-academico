@echo off
chcp 65001 >nul
title Barcode Academico - API de Integracao
echo ============================================
echo   Barcode Academico - API Local (porta 8765)
echo ============================================
echo.
echo   Documentacao interativa: http://127.0.0.1:8765/docs
echo   Defina a variavel VTC_API_KEY antes de usar rotas protegidas.
echo.
cd /d "%~dp0"
set "PY=python"
if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"
if exist "%~dp0..\.venv\Scripts\python.exe" set "PY=%~dp0..\.venv\Scripts\python.exe"

"%PY%" --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado.
    pause
    exit /b 1
)
rem Por seguranca, sobe em 127.0.0.1. Para rede local, altere para --host 0.0.0.0 apos definir VTC_API_KEY.
"%PY%" -m uvicorn api_vtc:app --host 127.0.0.1 --port 8765
pause
