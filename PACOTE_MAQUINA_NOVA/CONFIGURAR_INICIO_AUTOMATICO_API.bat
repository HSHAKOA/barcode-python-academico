@echo off
chcp 65001 >nul
title VTC - Configurar Inicio Automatico da API
echo ========================================================
echo   VTC - Configurar Inicio Automatico da API (Porta 8765)
echo ========================================================
echo.
echo   Este utilitário configura a API VTC para ligar
echo   automaticamente quando o computador for ligado.
echo.
echo   Escolha como deseja que a API inicie:
echo.
echo     [1] Ao fazer login - Em SEGUNDO PLANO (Recomendado)
echo         * Roda escondido, sem janela preta aberta.
echo         * Não precisa de permissão de Administrador.
echo.
echo     [2] Ao fazer login - Com JANELA ABERTA
echo         * Abre a janela do terminal mostrando os logs do uvicorn.
echo         * Não precisa de permissão de Administrador.
echo.
echo     [3] Ao LIGAR O PC no BOOT (Agendador de Tarefas do Windows)
echo         * Inicia o servidor assim que o PC liga, mesmo sem login.
echo         * Requer executar este arquivo como Administrador.
echo.
set "OPCAO=1"
set /p OPCAO="  Digite o numero da opcao desejada [1, 2 ou 3] (padrao: 1): "

if "%OPCAO%"=="3" goto config_boot
if "%OPCAO%"=="2" goto config_startup_janela
goto config_startup_segundo_plano

:config_startup_segundo_plano
set "ALVO=%~dp0INICIAR_API_VTC_SEGUNDO_PLANO.vbs"
set "DESCR=VTC API - Inicia em Segundo Plano"
set "ATALHO=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VTC API.lnk"
goto criar_atalho

:config_startup_janela
set "ALVO=%~dp0INICIAR_API_VTC.bat"
set "DESCR=VTC API - Inicia com Janela"
set "ATALHO=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VTC API.lnk"
goto criar_atalho

:criar_atalho
powershell -NoProfile -Command ^
    "$s = New-Object -ComObject WScript.Shell;" ^
    "$sc = $s.CreateShortcut('%ATALHO%');" ^
    "$sc.TargetPath = '%ALVO%';" ^
    "$sc.WorkingDirectory = '%~dp0';" ^
    "$sc.Description = '%DESCR%';" ^
    "$sc.Save()"

if exist "%ATALHO%" (
    echo.
    echo ========================================================
    echo   [OK] INICIO AUTOMATICO CONFIGURADO COM SUCESSO!
    echo ========================================================
    echo   Atalho salvo em:
    echo   %ATALHO%
    echo.
    echo   Toda vez que o computador ligar e o usuario entrar,
    echo   a API VTC subira automaticamente na porta 8765.
    echo.
    echo   - Para iniciar agora: execute 'INICIAR_API_VTC_SEGUNDO_PLANO.vbs'
    echo   - Para parar a API: execute 'PARAR_API_VTC.bat'
    echo   - Para desativar o inicio automatico: execute 'REMOVER_INICIO_AUTOMATICO_API.bat'
) else (
    echo.
    echo   [ERRO] Nao foi possivel criar o atalho na pasta Inicializar.
)
goto fim

:config_boot
net session >nul 2>&1
if errorlevel 1 (
    echo.
    echo ========================================================
    echo   [ATENCAO] Permissao de Administrador Necessaria
    echo ========================================================
    echo   Para configurar inicializacao no Boot do Windows (sem login),
    echo   clique com o botao DIREITO em "CONFIGURAR_INICIO_AUTOMATICO_API.bat"
    echo   e selecione "Executar como administrador".
    echo.
    goto fim
)

schtasks /Create /F /SC ONSTART /RU SYSTEM /RL HIGHEST /TN "VTC - API de Integracao" /TR "wscript.exe \"%~dp0INICIAR_API_VTC_SEGUNDO_PLANO.vbs\""
if errorlevel 1 (
    echo.
    echo   [ERRO] Falha ao criar a tarefa agendada no Windows.
) else (
    echo.
    echo ========================================================
    echo   [OK] TAREFA NO BOOT DO SISTEMA CRIADA COM SUCESSO!
    echo ========================================================
    echo   A API VTC iniciara assim que o computador ligar na tomada,
    echo   mesmo antes de qualquer usuario digitar a senha de login.
    echo.
    echo   - Para desativar: use 'REMOVER_INICIO_AUTOMATICO_API.bat' (como Admin).
)
goto fim

:fim
echo.
pause
