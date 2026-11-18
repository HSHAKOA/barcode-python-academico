@echo off
chcp 65001 >nul
title Barcode Academico - Exportador CSV (Power Query)
echo ============================================
echo   Barcode Academico - Exportador de CSV
echo ============================================
echo.
echo   Pode deixar o Excel ABERTO - ele atualiza sozinho.
echo   Nao gera arquivos temporarios.
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
"%PY%" exportador_csv.py
pause
