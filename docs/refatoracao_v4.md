# Refatoração de Engenharia de Software (v3 → v4)

## 1. Metodologia Utilizada

- **Ponytail (referência oficial, nível `full`):** a extensão Ponytail não estava instalada no ambiente; suas regras oficiais (`SKILL.md`) foram aplicadas manualmente buscando a menor mudança estrutural que eliminasse duplicações e reduzisse acoplamento sem criar abstrações artificiais.
- **PEP 8 e PEP 257:** padronização de imports, nomes claros, *type hints* nas assinaturas públicas e docstrings curtas em funções relevantes.
- **Martin Fowler (Refactoring):** extração de módulos coesos (`scanner_vtc.py`, `etiquetas_vtc.py`), extração de funções para eliminar duplicações (`_criar_tabela`, `_ler_material_e_qtd`, `_abrir_arquivo`, `_tocar_bip`) e substituição de blocos repetidos por tabela de dados (`CONSULTAS_CSV`).

---

## 2. Comparativo Mensurável (v3 × v4)

| Critério | Versão v3 (Baseline) | Versão v4 (Refatorada) | Evidência / Observação |
|---|---|---|---|
| Módulos Python em `PACOTE_MAQUINA_NOVA/` | `7` arquivos | `9` arquivos | Extraídos `scanner_vtc.py` (`80L`) e `etiquetas_vtc.py` (`115L`) para separar captura OS e geração de etiquetas. |
| Linhas de código da aplicação (`*.py`) | `1.772` linhas | `1.776` linhas | Praticamente estável (+4 linhas no total), porém com muito menos código repetido e docstrings/tipagem completos. |
| `barcode_vtc.py` (GUI) | `691` linhas (maior método: `_build_producao` com `94L`) | `565` linhas (maior método: `_build_estoque` com `36L`) | `-126` linhas na GUI; `_build_producao` dividido em 4 métodos claros e tabelas unificadas. |
| `core_vtc.py` (Núcleo) | `436` linhas (maior: `gerar_pdf_etiquetas` com `61L`) | `362` linhas (maior: `init_db` com `54L`) | `-74` linhas; núcleo livre de código `reportlab` e ZPL. |
| `exportador_csv.py` | `223` linhas (`exportar_tudo` com `149L`) | `202` linhas (`exportar_tudo` com `26L`) | 7 blocos `try/except` duplicados substituídos por `CONSULTAS_CSV` + laço único. |
| `criar_planilha_pq.py` | `148` linhas (`criar_planilha` com `102L`) | `150` linhas (maior: `_montar_dashboard` com `65L`) | Separação clara entre Dashboard e criação das 7 abas de dados. |
| `verificar_dados.py` | `77` linhas (`main` com `64L`, 3 níveis) | `87` linhas (`main` com `25L`, 1 nível) | Dividido em 4 funções pequenas de impressão por tabela. |
| Scripts Windows (`.bat`/`.vbs`) | `11` scripts (usavam apenas `python` global) | `11` scripts (detectam `.venv` local + `chcp 65001`) | Suporte automático a `.venv`, `python -m pip` e caminhos com espaços/acentos. |
| Testes automatizados aprovados (`.venv`) | `17/17` aprovados | `20/20` aprovados | `0` falhas; cobertura ampliada para `scanner_vtc`, `etiquetas_vtc`, arredondamento CSV, 5 abas GUI e scripts `.venv`. |

---

## 3. Problemas Encontrados na v3 e Alterações Aplicadas

1. **Acoplamento entre GUI e captura de teclado (`barcode_vtc.py`):** `ScannerListener` ficava dentro do arquivo da interface gráfica. Extraído para `scanner_vtc.py` com `_processar_tecla()` isolado e testável sem Tkinter.
2. **Acoplamento entre regras SQLite e geração de etiquetas (`core_vtc.py`):** `gerar_pdf_etiquetas` (`61L`) e `gerar_zpl_etiquetas` misturavam `reportlab` com SQLite. Extraídos para `etiquetas_vtc.py`, com helper `_desenhar_etiqueta_pdf()`.
3. **Duplicação de widgets e utilitários na GUI (`barcode_vtc.py`):** cinco `Treeview` com laços repetidos de cabeçalho substituídos por `_criar_tabela()`; quatro limpezas de tabela unificadas em `_limpar_tabela()`; parsing repetido em `_dar_entrada`/`_ajustar_saldo` unificado em `_ler_material_e_qtd()`; três `os.startfile` em `_abrir_arquivo()` e dois `winsound` em `_tocar_bip()`.
4. **Atualização redundante na interface (`barcode_vtc.py`):** `_poll()` reconfigurava `lbl_bg` a cada `100 ms`; agora só reconfigura quando `hook_ativo` muda de estado.
5. **Duplicação massiva no exportador (`exportador_csv.py`) e ruído de `float`:** sete blocos `try/except` repetidos em `exportar_tudo()` consolidados em `CONSULTAS_CSV`; `ROUND(saldo_kg, 3)` aplicado na consulta de `estoque.csv` e `movimentacoes.csv` (evitando `-0.19999999999999996`).
6. **`INSERT OR REPLACE` em `estoque` (`core_vtc.py`):** substituído por `INSERT ... ON CONFLICT(material, cor) DO UPDATE`, atualizando o saldo no próprio registro sem apagar e reinserir a linha.
7. **Detecção de `.venv` e acentuação nos `.bat`:** `INICIAR_*.bat`, `VERIFICAR_DADOS.bat` e `_api_vtc_bg.bat` passam a usar `.venv\Scripts\python.exe` quando presente e `"%PY%" -m pip`; `CONFIGURAR_INICIO_AUTOMATICO.bat` e `REMOVER_INICIO_AUTOMATICO.bat` receberam `chcp 65001 >nul`.

---

## 4. Decisões Rejeitadas (e Por Quê)

- **Rejeitada:** criar camadas `Repository`, `Service`, `Factory` ou injeção de dependências formal. **Motivo:** adicionaria boilerplate sem resolver nenhum problema real no porte deste projeto, prejudicando o estudo por alunos de 1º/2º ano.
- **Rejeitada:** dividir `barcode_vtc.py` em 5 arquivos separados (um por aba). **Motivo:** fragmentaria o estado compartilhado de `App` (`operador`, `tree_est`, `tree_res`, rodapé) criando acoplamento cruzado entre módulos pequenos.
- **Rejeitada:** trocar `sqlite3` por ORM (SQLAlchemy). **Motivo:** adicionaria dependência externa pesada e ocultaria as transações SQL explícitas importantes para a disciplina.
