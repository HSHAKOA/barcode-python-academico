# Testes Executados, Evidências e Limitações (v4)

**Ambiente validado:** Windows 64-bit · Python `3.15.2` em `.venv` isolado com `requirements.txt` instalado (`keyboard 0.13.5`, `reportlab 5.1.0`, `openpyxl 3.1.5`, `fastapi 0.163.2`, `uvicorn 0.54.0`, `pydantic 2.14.3`). Todos os testes executam em diretórios temporários (`tempfile.mkdtemp()`) com dados exclusivamente fictícios.

---

## 1. Casos de Teste Executados (`tests/test_barcode_regressao.py`)

| Grupo | Casos | O que foi comprovado | Resultado (.venv) |
|---|---|---|---|
| **Núcleo (`TestCoreFluxos`)** | 10 testes | Criação de tabelas e WAL; decodificação válida/inválida (incluindo `None`); 36 combinações; desconto e alerta negativo; ajuste e rollback completo após exceção; histórico e resumo; rejeição de `NaN`/`Inf`/material inválido; ZPL `^CI28` e 7 CSVs atômicos; concorrência de 10 threads em `dar_entrada` (`1000,0 kg`) e `registrar_producao` (`600,0 kg`). | **10/10 OK** |
| **Deduplicação GUI (`TestGuiDeduplicacao`)** | 1 teste | Com `hook_ativo=True`, fila + evento Tk disparam apenas 1 chamada; com `False`, fallback Tk e rótulo `MODO JANELA` funcionam. | **1/1 OK** |
| **API HTTP (`TestApiOpcional`)** | 2 testes | Servidor `uvicorn` real em `127.0.0.1` recusa chave padrão (`503` sem `VTC_API_KEY`), retorna `401` sem chave válida e valida entradas (`200`/`400`) com chave configurada. | **2/2 OK** |
| **Extras PyPI (`TestRecursosExtrasInstalados`)** | 2 testes | `reportlab` gera PDF `%PDF-1.4` válido; `openpyxl` gera `.xlsx` com 8 abas; `keyboard` ativa hook real e 1 leitura resulta em 1 apontamento e 1 desconto. | **2/2 OK** |
| **Refatoração v4 (`TestRefatoracaoV4ModulosENavegacao`)** | 3 testes | `ScannerListener._processar_tecla()` desacoplado rejeita digitação lenta (`> 0.8s`); `etiquetas_vtc` + reexportações preservadas; `estoque.csv` arredonda para `-0.2`; `verificar_dados.main()` executa limpo; `App` navega pelas 5 abas e grava no histórico. | **3/3 OK** |
| **Scripts e Requisitos (`TestScriptsWindowsERequisitos`)** | 2 testes | Todos os 11 scripts `.bat`/`.vbs` presentes, portáveis (`%~dp0`), com `chcp 65001` e suporte a `.venv`, sem `0.0.0.0` ou `powercfg` ativos; `requirements.txt` íntegro. | **2/2 OK** |

Total: **`20` métodos de teste executados** (`Ran 20 tests — OK`, 0 falhas, 0 ignorados no `.venv` completo).

Em execução complementar com Python stdlib puro (sem pacotes PyPI): `16` aprovados e `4` ignorados automaticamente via `@unittest.skipUnless`.

---

## 2. Limitações Não Testadas em Campo / Hardware

1. **Leitor de código de barras físico USB HID:** validação feita via hook `keyboard` e eventos simulados; sem hardware óptico físico conectado.
2. **Impressora térmica Zebra:** arquivo `.zpl` validado textualmente (`^XA`, `^CI28`, `^BCN`, `^XZ`), sem impressão física.
3. **Excel / Power Query ao vivo:** `.xlsx` e 7 CSVs gerados e lidos em teste; atualização automática periódica dentro do Microsoft Excel depende de configuração manual pelo usuário.
4. **Registro real de Startup e Tarefa Agendada (`CONFIGURAR_INICIO_AUTOMATICO*.bat`):** validado estaticamente quanto a `%~dp0` e `%APPDATA%`, sem criar atalhos `.lnk` ou tarefas no computador operacional.
5. **Captura visual de tela em sessão não interativa:** os testes da GUI validam criação de widgets, troca das 5 abas e atualização dos valores de tela em Python; captura GDI de desktop não pôde ser executada nesta sessão sem monitor interativo.
