@echo off
chcp 65001 >nul
title Barcode Academico - Producao por Receita
echo ============================================
echo   Barcode Academico - Producao por Receita
echo   Versao Demonstrativa (Dados Ficticios)
echo ============================================
echo.
cd /d "%~dp0"
set "PY=python"
if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"
if exist "%~dp0..\.venv\Scripts\python.exe" set "PY=%~dp0..\.venv\Scripts\python.exe"

"%PY%" --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale em python.org
    echo Marque "Add Python to PATH" na instalacao.
    pause
    exit /b 1
)
echo Verificando dependencias...
"%PY%" -m pip show keyboard >nul 2>&1 || (echo Instalando keyboard... & "%PY%" -m pip install keyboard --quiet)
"%PY%" -m pip show reportlab >nul 2>&1 || (echo Instalando reportlab... & "%PY%" -m pip install reportlab --quiet)
echo.
echo Iniciando... (scanner em segundo plano ATIVO)
echo.
"%PY%" barcode_vtc.py
if errorlevel 1 pause
