@echo off
chcp 65001 >nul
title VTC - Parar API de Integracao
echo ========================================================
echo   VTC - Parar API de Integracao (Porta 8765)
echo ========================================================
echo.

powershell -NoProfile -Command ^
    "$conns = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue;" ^
    "if ($conns) {" ^
    "    $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique;" ^
    "    foreach ($p in $pids) {" ^
    "        try {" ^
    "            Stop-Process -Id $p -Force -ErrorAction Stop;" ^
    "            Write-Host ('  [OK] Processo da API (PID ' + $p + ') finalizado com sucesso.') -ForegroundColor Green;" ^
    "        } catch {" ^
    "            Write-Host ('  [ERRO] Falha ao encerrar PID ' + $p + ': ' + $_.Exception.Message) -ForegroundColor Red;" ^
    "        }" ^
    "    }" ^
    "} else {" ^
    "    Write-Host '  [INFO] A API VTC nao esta rodando no momento (porta 8765 livre).' -ForegroundColor Yellow;" ^
    "}"

echo.
pause
