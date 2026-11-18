# Guia Didático de Leitura do Código

Este guia orienta estudantes e avaliadores sobre **por onde começar a ler o projeto** e como acompanhar um apontamento completo do início ao fim.

---

## 1. Ordem Recomendada de Estudo

1. **`PACOTE_MAQUINA_NOVA/config_receitas.py` (88 linhas):** comece aqui. Contém apenas os dicionários e constantes fictícias do domínio (`MAQUINAS`, `MARFIM_KG_POR_BIP`, `CORES`, `CORES_HEX`, `RECEITAS`). Não importa nenhum outro módulo.
2. **`PACOTE_MAQUINA_NOVA/core_vtc.py` (362 linhas):** leia em seguida para entender as regras do sistema. Foque em:
   - `_db()` (`L21-L35`): como a conexão SQLite garante `commit` e `rollback`.
   - `_validar_material()` e `_validar_kg()` (`L48-L60`): validação de entradas.
   - `decodificar()` (`L216-L240`): como uma string vira uma receita com pesos.
   - `registrar_producao()` (`L243-L286`): como produção e estoque são gravados juntos.
3. **`PACOTE_MAQUINA_NOVA/etiquetas_vtc.py` (115 linhas):** veja como `listar_codigos()` gera as 36 etiquetas a partir de `config_receitas.py` e como são gravadas em PDF ou ZPL.
4. **`PACOTE_MAQUINA_NOVA/scanner_vtc.py` (80 linhas):** observe `ScannerListener._processar_tecla()` (`L32-L51`) para entender como o sistema diferencia um leitor rápido (`< 0,8s`) de teclas avulsas.
5. **`PACOTE_MAQUINA_NOVA/barcode_vtc.py` (565 linhas):** veja como `App` monta as 5 abas usando `_criar_tabela()`, consome `self.fila` no `_poll()` (`L126-L139`) e atualiza a tela em `_processar()` (`L526-L558`).
6. **Módulos opcionais:**
   - `exportador_csv.py` (`CONSULTAS_CSV` + `exportar_tudo()`)
   - `api_vtc.py` (rotas FastAPI reutilizando `core_vtc`)
   - `criar_planilha_pq.py` e `verificar_dados.py`

---

## 2. Exemplo Completo de um Apontamento (`M2-PIG-CC`)

Suponha que o operador digitou `Aluno` no campo `OPERADOR` e bipou a etiqueta **`M2-PIG-CC`** com saldo inicial fictício de `40,0 kg` de `Marfim` e `0,3 kg` de `Pigmento Cinza Claro`:

1. **Captura (`scanner_vtc.py` ou `barcode_vtc.py`):** as teclas chegam em menos de `0,8s` seguidas de `Enter` e são enviadas para `App._processar("M2-PIG-CC")`.
2. **Decodificação (`core_vtc.decodificar`):**
   - Divide `"M2-PIG-CC"` em `"M2"` e `"PIG-CC"`.
   - Encontra `"M2"` → `"Máquina 2"` em `MAQUINAS`.
   - Encontra `"PIG-CC"` em `RECEITAS` (`cor = "Cinza Claro"`, `moido_kg = 0.0`, `pigmento_kg = 0.5`).
   - Calcula `total_kg = 20.0 + 0.0 + 0.5 = 20.5`.
3. **Registro e Desconto Atômico (`core_vtc.registrar_producao`):**
   - Abre transação `BEGIN IMMEDIATE`.
   - Insere a linha na tabela `producao` com o turno retornado por `turno_atual()`.
   - Desconta `20,0 kg` de `Marfim` (`40,0 → 20,0`) e grava `SAIDA` em `mov_estoque`.
   - Como `pigmento_kg > 0`, desconta `0,5 kg` de `Pigmento Cinza Claro` (`0,3 → -0,2`) e grava `SAIDA` em `mov_estoque`.
   - Como `-0,2 < 0`, adiciona `"Pigmento Cinza Claro NEGATIVO: -0.2 kg"` em `avisos`.
   - Consulta o total de bips do dia para essa combinação e faz `commit()`.
4. **Atualização da Tela (`barcode_vtc.App._processar`):**
   - Preenche os rótulos da última receita, exibe o aviso em vermelho, insere a linha no topo de `BIPS RECENTES`, atualiza os totais de `Resumo` e `Estoque` e toca um bip agudo de confirmação (`1000 Hz`).
