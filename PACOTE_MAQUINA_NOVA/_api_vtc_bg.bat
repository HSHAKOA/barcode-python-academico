@echo off
rem ====================================================================
rem  Ajudante interno - NAO precisa dar dois cliques aqui.
rem  Usado pelo "INICIAR_API_VTC_SEGUNDO_PLANO.vbs" para rodar a API
rem  em segundo plano (sem janela preta) e gravar logs em api_vtc.log.
rem ====================================================================
chcp 65001 >nul
cd /d "%~dp0"
set "PY=python"
if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"
if exist "%~dp0..\.venv\Scripts\python.exe" set "PY=%~dp0..\.venv\Scripts\python.exe"

"%PY%" --version >nul 2>&1
if errorlevel 1 (
    echo [%date% %time%] ERRO: Python nao encontrado neste PC. >> "%~dp0api_vtc.log"
    exit /b 1
)

rem Em ambiente academico, nao alteramos energia do PC (powercfg) nem expomos em 0.0.0.0 por padrao.
rem Para uso em servidor industrial, ajuste --host para 0.0.0.0 apos definir VTC_API_KEY.

echo. >> "%~dp0api_vtc.log"
echo ======================================================== >> "%~dp0api_vtc.log"
echo  Barcode Academico API iniciada em %date% as %time% >> "%~dp0api_vtc.log"
echo ======================================================== >> "%~dp0api_vtc.log"

"%PY%" -m uvicorn api_vtc:app --host 127.0.0.1 --port 8765 >> "%~dp0api_vtc.log" 2>&1
