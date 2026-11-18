# Algoritmos e Conceitos de Python no Código (v4)

Este documento mapeia os conceitos da disciplina **Algoritmos e Linguagem de Programação** presentes no código refatorado de `BARCODE_ACADEMICO_v4/PACOTE_MAQUINA_NOVA/`, com referências exatas de arquivo, função e intervalo de linhas.

---

## 1. Variáveis e Tipos de Dados

- **`config_receitas.py` (`L17`):** `MARFIM_KG_POR_BIP = 20.0` (`float`), `MAQUINAS` (`dict`), `CORES` (`list`).
- **`scanner_vtc.py` (`L18-L26`):** `self.buffer = ""` (`str`), `self.first_key = 0.0` (`float`), `self.ativo = True` (`bool`), `self.hook_ativo = False` (`bool`), `self.MAX_SCAN = 0.8` (`float`).

## 2. Operadores Matemáticos, Relacionais e Lógicos

- **Comparação encadeada (`core_vtc.py`, `turno_atual`, `L119-L126`):** `if 6 <= hora < 14:` e `if 14 <= hora < 22:`.
- **Cálculo de receita (`etiquetas_vtc.py`, `calcular_total_receita`, `L8-L11`):** `MARFIM_KG_POR_BIP + receita["moido_kg"] + receita["pigmento_kg"]`.
- **Expressão lógica (`scanner_vtc.py`, `_char_valido`, `L8-L12`):** `if ch and (ch.isalnum() or ch in "-_."):`.

## 3. Estruturas Condicionais

- **Validação antecipada (`core_vtc.py`, `decodificar`, `L216-L240`):** verifica `isinstance(codigo, str)`, presença de `"-"` e existência nas tabelas `MAQUINAS` e `RECEITAS` com retorno antecipado (`None`).
- **Consumo condicional e alerta (`core_vtc.py`, `registrar_producao`, `L261-L270`):** inclui `Moído` e `Pigmento` somente se `> 0` e adiciona alerta quando `saldo < 0`.

## 4. Laços de Repetição (`for` e `while`)

- **`for` (`core_vtc.py`, `materiais_estoque`, `L38-L45`; `etiquetas_vtc.py`, `listar_codigos`, `L14-L23`):** geração dos 9 materiais iniciais e das 36 combinações de etiquetas.
- **`for` declarativo (`exportador_csv.py`, `exportar_tudo`, `L149-L154`):** percorre a lista `CONSULTAS_CSV` para exportar as 6 visões SQL sem repetir código.
- **`while` (`barcode_vtc.py`, `App._poll`, `L134-L137`; `exportador_csv.py`, `main`, `L177-L195`):** drena a fila de códigos lidos na interface e mantém o loop de exportação periódica.

## 5. Listas, Tuplas e Dicionários

- **Dicionários (`config_receitas.py`, `L4-L83`):** `MAQUINAS`, `CORES_HEX` e `RECEITAS` (aninhado) permitem busca $O(1)$ na decodificação.
- **Listas de tuplas (`exportador_csv.py`, `CONSULTAS_CSV`, `L16-L88`; `barcode_vtc.py`, `espec`, `L204-L205`):** definem colunas de CSV e especificações de `Treeview` de forma declarativa.

## 6. Funções, Parâmetros e Modularização

- **`core_vtc.py` (`L289`):** `buscar_producao(maquina=None, data=None, limite=200)` usa parâmetros opcionais com padrão.
- **`barcode_vtc.py` (`L53-L70`):** `_criar_tabela(parent, especificacao, altura, com_scroll=False)` elimina a repetição de configuração das cinco tabelas `Treeview`.
- **Separação modular:** `config_receitas.py` (dados), `core_vtc.py` (regras + SQLite), `etiquetas_vtc.py` (PDF/ZPL), `scanner_vtc.py` (hook/fila) e `barcode_vtc.py` (GUI).

## 7. Classes e Orientação a Objetos

- **`ScannerListener` (`scanner_vtc.py`, `L15-L80`):** encapsula buffer, janela de tempo, thread daemon e estado `hook_ativo`.
- **`App` (`barcode_vtc.py`, `L73-L558`):** encapsula a janela Tkinter, variáveis de controle e eventos das cinco abas.
- **Modelos Pydantic (`api_vtc.py`, `L42-L57`):** `ApontamentoIn`, `EstoqueEntradaIn` e `EstoqueAjusteIn` validam JSON automaticamente.

## 8. Tratamento de Exceções e Manipulação de Arquivos

- **Transacional (`core_vtc.py`, `_db`, `L21-L35`):** `@contextmanager` garante `commit`, `rollback` e `close`.
- **Arquivos seguros (`exportador_csv.py`, `exportar_csv`, `L99-L108`; `etiquetas_vtc.py`, `gerar_zpl_etiquetas`, `L89-L115`):** `with open(...)` com UTF-8 / `utf-8-sig` e troca atômica `.tmp` + `os.replace()`.
- **Degradação graciosa (`scanner_vtc.py`, `_run`, `L64-L70`):** captura `ImportError` se `keyboard` não estiver instalado.

## 9. Persistência de Dados e Algoritmos Principais

| Algoritmo | Arquivo e Linhas | Entrada → Processamento → Saída |
|---|---|---|
| **Decodificação** | `core_vtc.py` (`L216-L240`) | String bruta → `strip().upper()`, `split("-", 1)`, busca em `MAQUINAS`/`RECEITAS`, soma de pesos → `dict` ou `None`. |
| **Filtro temporal de leitor** | `scanner_vtc.py` (`L32-L51`) | Tecla + timestamp → limpa buffer se `> 1.5s`; envia à fila no `enter` se duração `< 0.8s` → string na `queue.Queue`. |
| **Transação de produção** | `core_vtc.py` (`L243-L286`) | `info` + `operador` → `BEGIN IMMEDIATE`, `INSERT producao`, baixas em `estoque`/`mov_estoque`, consulta bips do dia → `{"bips", "acum_kg", "avisos"}`. |
| **Filtro SQL dinâmico** | `core_vtc.py` (`L289-L313`) | `maquina`, `data`, `limite` → listas `wh` e `params` com `?` → lista de tuplas ordenadas. |
