@echo off
chcp 65001 >nul
title VTC - Remover Inicio Automatico da API
echo ========================================================
echo   VTC - Remover Inicio Automatico da API
echo ========================================================
echo.

set "ATALHO=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VTC API.lnk"
set "REMOVIDO=0"

if exist "%ATALHO%" (
    del "%ATALHO%"
    set "REMOVIDO=1"
    echo   [OK] Atalho da pasta Inicializar removido com sucesso.
)

schtasks /Query /TN "VTC - API de Integracao" >nul 2>&1
if not errorlevel 1 (
    schtasks /Delete /TN "VTC - API de Integracao" /F >nul 2>&1
    set "REMOVIDO=1"
    echo   [OK] Tarefa agendada do Windows removida com sucesso.
)

if "%REMOVIDO%"=="1" (
    echo.
    echo   A API VTC nao sera mais iniciada automaticamente.
) else (
    echo   [INFO] O inicio automatico da API nao estava ativado neste PC.
)

echo.
pause
