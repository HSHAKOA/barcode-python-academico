@echo off
chcp 65001 >nul
title VTC - Configurar Inicio Automatico
echo ============================================
echo   VTC - Configurar Inicio Automatico
echo ============================================
echo.
echo   Isso faz o VTC Barcode abrir sozinho toda vez
echo   que o Windows ligar e o usuario fizer login.
echo   (roda so pro usuario atual, sem precisar ser admin)
echo.

set "ALVO=%~dp0INICIAR_VTC_BARCODE.bat"
set "ATALHO=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VTC Barcode.lnk"

powershell -NoProfile -Command ^
    "$s = New-Object -ComObject WScript.Shell;" ^
    "$sc = $s.CreateShortcut('%ATALHO%');" ^
    "$sc.TargetPath = '%ALVO%';" ^
    "$sc.WorkingDirectory = '%~dp0';" ^
    "$sc.Description = 'VTC Barcode - inicia automaticamente';" ^
    "$sc.Save()"

if exist "%ATALHO%" (
    echo   OK! Atalho criado em:
    echo   %ATALHO%
    echo.
    echo   Da proxima vez que der login nesse usuario, o VTC
    echo   Barcode abre sozinho. Pode testar reiniciando agora,
    echo   ou so deixar pra proxima vez que a maquina ligar.
) else (
    echo   [ERRO] Nao consegui criar o atalho de inicio automatico.
)
echo.
pause
