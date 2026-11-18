# Inventário de Bibliotecas e Dependências (v4)

Todas as bibliotecas abaixo foram conferidas diretamente nos `import` de `BARCODE_ACADEMICO_v4/PACOTE_MAQUINA_NOVA/` e validadas no ambiente virtual isolado (Python `3.15.2`, Windows 64-bit).

---

## 1. Classificação Geral

| Biblioteca | Classificação | Finalidade Real no Barcode | Arquivo(s) | Versão Validada | Obrigatória? |
|---|---|---|---|---|---|
| `tkinter` / `tkinter.ttk` (`messagebox`, `filedialog`) | **Nativa** (stdlib) | Janela principal, abas, tabelas (`Treeview`), diálogos e seleção de arquivos | `barcode_vtc.py` | Stdlib `3.15.2` | Sim (GUI) |
| `sqlite3` | **Nativa** (stdlib) | Banco local `barcode_vtc.db`, modo WAL e transações `BEGIN IMMEDIATE` | `core_vtc.py`, `exportador_csv.py`, `verificar_dados.py` | Stdlib `3.15.2` | Sim |
| `csv` | **Nativa** (stdlib) | Exportação de tabelas em CSV `;` com `utf-8-sig` | `barcode_vtc.py`, `exportador_csv.py` | Stdlib `3.15.2` | Sim (CSV) |
| `threading` / `queue` | **Nativa** (stdlib) | Thread daemon de escuta do teclado e fila thread-safe para a GUI | `scanner_vtc.py`, `barcode_vtc.py` | Stdlib `3.15.2` | Sim (GUI) |
| `datetime` / `time` | **Nativa** (stdlib) | Timestamps, turnos, janela temporal do leitor (`0,8s`) e pausa do exportador (`10s`) | `core_vtc.py`, `etiquetas_vtc.py`, `scanner_vtc.py`, `barcode_vtc.py`, `exportador_csv.py` | Stdlib `3.15.2` | Sim |
| `os` | **Nativa** (stdlib) | Caminhos relativos (`__file__`), `os.makedirs`, `os.replace`, `os.startfile`, `os.environ` | Todos os módulos operacionais exceto `config_receitas` e `scanner_vtc` | Stdlib `3.15.2` | Sim |
| `math` / `contextlib` | **Nativa** (stdlib) | Bloqueio de `NaN`/`Inf` (`math.isfinite`) e gerenciador `_db()` (`@contextmanager`) | `core_vtc.py`, `barcode_vtc.py` | Stdlib `3.15.2` | Sim |
| `secrets` / `typing` | **Nativa** (stdlib) | Comparação em tempo constante (`compare_digest`) e parâmetro `Optional` na API | `api_vtc.py` | Stdlib `3.15.2` | Sim (API) |
| `winsound` | **Nativa** (stdlib Windows) | Bipes sonoros de confirmação/erro dentro de `try/except` | `barcode_vtc.py` | Stdlib `3.15.2` | Não |
| `unittest`, `tempfile`, `shutil`, `subprocess`, `socket`, `json`, `urllib` | **Nativa** (stdlib) | Suíte de testes isolados em pasta temporária | `tests/test_barcode_regressao.py` | Stdlib `3.15.2` | Apenas testes |
| `keyboard` | **Direta externa** (`requirements.txt`) | Hook global de teclado em segundo plano (`kb.hook`, `kb.unhook_all`) | `scanner_vtc.py` (import sob demanda) | `0.13.5` | Não (há fallback Tkinter) |
| `reportlab` | **Direta externa** (`requirements.txt`) | Desenho de etiquetas A4 e código de barras Code 128 em PDF | `etiquetas_vtc.py` (import sob demanda) | `5.1.0` | Não (só PDF) |
| `openpyxl` | **Direta externa** (`requirements.txt`) | Criação da planilha `.xlsx` estruturada para Power Query | `criar_planilha_pq.py` | `3.1.5` | Não (só `.xlsx`) |
| `fastapi` | **Direta externa** (`requirements.txt`) | Endpoints HTTP REST e validação de header `X-API-Key` | `api_vtc.py` | `0.163.2` | Não (só API) |
| `uvicorn` | **Direta externa** (`requirements.txt`) | Servidor ASGI que executa `api_vtc:app` na porta `8765` | `INICIAR_API_VTC.bat`, `_api_vtc_bg.bat` | `0.54.0` | Não (só API) |
| `pydantic` | **Transitiva externa** (via `fastapi`) | Modelos `BaseModel` para validação JSON da API | `api_vtc.py` | `2.14.3` | Não (só API) |
| Demais transitivas | **Transitivas externas** | Dependências internas de `reportlab`, `openpyxl`, `fastapi` e `uvicorn` | Instaladas no `.venv` | `pillow 13.0.0`, `charset-normalizer 3.5.2`, `et-xmlfile 2.0.0`, `starlette 1.10.0`, `pydantic_core 2.50.4`, `anyio 4.16.0`, `click 8.5.1`, `h11 0.16.0`, `idna 3.20`, `typing_extensions 4.16.0`, `typing-inspection 0.4.5`, `annotated-doc 0.0.7`, `annotated-types 0.8.0`, `opentelemetry-api 1.45.2` | Indiretas |

---

## 2. Motivo da Escolha e Compatibilidade

- **Nativas primeiro:** usar `tkinter`, `sqlite3`, `csv`, `threading` e `queue` permite que a aplicação principal e os utilitários de dados funcionem sem dependências pesadas.
- **Externas pontuais:** nenhuma das 5 bibliotecas de `requirements.txt` está sobrando; todas têm uso real comprovado e nenhuma pôde ser removida sem perder uma funcionalidade (segundo plano, PDF, Excel `.xlsx` ou API HTTP).
- **Compatibilidade:** o projeto rodou originalmente em Python `3.12` (recomendado `3.10`–`3.13`) e foi integralmente validado nesta revisão v4 em ambiente virtual isolado com **Python `3.15.2`** (64-bit Windows), com todas as 5 bibliotecas externas instaladas via `pip` sem falhas.
