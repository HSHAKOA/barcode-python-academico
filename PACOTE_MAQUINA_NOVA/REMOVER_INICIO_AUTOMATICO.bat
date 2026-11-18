@echo off
chcp 65001 >nul
title VTC - Remover Inicio Automatico
set "ATALHO=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VTC Barcode.lnk"

if exist "%ATALHO%" (
    del "%ATALHO%"
    echo   Removido. O VTC Barcode nao abre mais sozinho no login.
) else (
    echo   Nao tinha inicio automatico configurado pra esse usuario.
)
echo.
pause
