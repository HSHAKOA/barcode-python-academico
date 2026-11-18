# Guia de Instalação, Scripts Windows e Demonstração (v4)

## 1. Instalação Reproduzível

1. Instale o **Python 3.10 a 3.13** (ou **3.15**) marcando **"Add Python to PATH"** e mantendo **Tcl/Tk (`tkinter`)** selecionado.
2. Extraia o pacote `BARCODE_ACADEMICO_v4.zip` para uma pasta local (funciona mesmo em caminhos com espaços e acentos).
3. Crie um ambiente virtual `.venv` na raiz `BARCODE_ACADEMICO_v4/` (ou dentro de `PACOTE_MAQUINA_NOVA/`):
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r PACOTE_MAQUINA_NOVA\requirements.txt
   ```

---

## 2. Como os 11 Scripts Windows Funcionam

Todos os scripts usam `%~dp0` (ou `WScript.ScriptFullName` no `.vbs`) e `chcp 65001 >nul`, funcionando em diretórios com espaços e acentos sem depender do usuário ou caminho original. Os scripts que chamam Python (`INICIAR_*.bat`, `VERIFICAR_DADOS.bat`, `_api_vtc_bg.bat`) detectam automaticamente `.venv\Scripts\python.exe` (local ou na pasta pai) e usam `"%PY%" -m pip` para manter consistência entre `python` e `pip`.

| Script | Finalidade | Atalho / Processo / Segurança |
|---|---|---|
| `INICIAR_VTC_BARCODE.bat` | Abre `barcode_vtc.py` (instala `keyboard`/`reportlab` via `"%PY%" -m pip` se faltarem) | Processo principal em janela |
| `INICIAR_EXPORTADOR_CSV.bat` | Inicia `exportador_csv.py` | Loop de 7 CSVs em `dados_powerquery/` |
| `VERIFICAR_DADOS.bat` | Executa `verificar_dados.py` | Inspeção rápida de `barcode_vtc.db` |
| `INICIAR_API_VTC.bat` | Sobe `api_vtc:app` via `uvicorn` em `127.0.0.1:8765` | Seguro por padrão (localhost); requer `$env:VTC_API_KEY` para rotas protegidas |
| `INICIAR_API_VTC_SEGUNDO_PLANO.vbs` | Inicia `_api_vtc_bg.bat` oculto (`0`) e mostra popup de 4s | Usa `WScript.ScriptFullName` |
| `_api_vtc_bg.bat` | Auxiliar do `.vbs`; sobe `uvicorn` em `127.0.0.1:8765` gravando `api_vtc.log` | Sem `powercfg` nem exposição `0.0.0.0` por padrão |
| `PARAR_API_VTC.bat` | Encerra processo escutando na porta `8765` | PowerShell `Get-NetTCPConnection` + `Stop-Process` |
| `CONFIGURAR_INICIO_AUTOMATICO.bat` | Cria `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VTC Barcode.lnk` | Aponta para `%~dp0INICIAR_VTC_BARCODE.bat` |
| `REMOVER_INICIO_AUTOMATICO.bat` | Apaga `Startup\VTC Barcode.lnk` | Limpeza do logon |
| `CONFIGURAR_INICIO_AUTOMATICO_API.bat` | Configura `Startup\VTC API.lnk` (opções 1/2) ou tarefa agendada no boot (opção 3, requer Admin) | Opção 1 aponta para `.vbs`; opção 2 para `INICIAR_API_VTC.bat`; opção 3 cria tarefa `"VTC - API de Integracao"` |
| `REMOVER_INICIO_AUTOMATICO_API.bat` | Remove `Startup\VTC API.lnk` e a tarefa `"VTC - API de Integracao"` | Limpeza da API automática |

*(Para expor a API em rede local industrial explicitamente: defina `VTC_API_KEY` com uma chave forte e altere `--host 127.0.0.1` para `--host 0.0.0.0` apenas em rede interna controlada.)*

---

## 3. Demonstração Acadêmica com Dados Fictícios

1. Rode `python barcode_vtc.py` dentro de `PACOTE_MAQUINA_NOVA/` (criará um `barcode_vtc.db` vazio de teste).
2. Na aba **Estoque**, dê entrada fictícia de `40` kg de `Marfim` e `0.8` kg de `Pigmento` `Cinza Claro`.
3. Na aba **Produção**, clique fora do campo `OPERADOR` e digite rapidamente `M2-PIG-CC` + `Enter` (ou, se `keyboard` estiver ativo, bipa mesmo sem foco na caixa de texto).
4. Repita `M2-PIG-CC` + `Enter` para ver o saldo de Pigmento ficar negativo (`-0.2 kg`) e o alerta vermelho aparecer na tela.
5. Para testar a API localmente em outro terminal:
   ```powershell
   $env:VTC_API_KEY="minha-chave-teste-123"
   .\INICIAR_API_VTC.bat
   ```
6. Para rodar os testes automatizados em pasta temporária isolada:
   ```powershell
   python -B -m unittest discover -s tests -v
   ```

---

## 4. Problemas Comuns

- **`ModuleNotFoundError` em API, PDF ou planilha:** ative o `.venv` e rode `pip install -r PACOTE_MAQUINA_NOVA\requirements.txt`.
- **`HTTP 503` ao chamar a API:** a variável `VTC_API_KEY` não foi definida (ou recebeu a chave padrão insegura). Defina uma chave própria no ambiente antes de subir o servidor.
- **Leitor não captura no modo janela:** verifique se o cursor não ficou piscando dentro da caixa de texto `OPERADOR` (por segurança, `_on_key_tk` ignora teclas dentro de `tk.Entry`).
