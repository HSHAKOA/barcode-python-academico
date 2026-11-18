# Como configurar o Power Query (uma vez só)

Depois disso, você **deixa a planilha aberta o dia inteiro** e ela se atualiza sozinha. Nunca mais mexe nisso.

---

## Por que Power Query resolve o problema

| | Gravando .xlsx direto | Power Query (CSV) |
|---|---|---|
| Deixar Excel aberto | ❌ trava o arquivo, não atualiza | ✅ atualiza sozinho |
| Arquivos temporários | ❌ gerava lixo | ✅ nenhum |
| Velocidade | lenta (reescreve tudo) | rápida (CSV é leve) |

O Python escreve CSVs (leves, sem lock). O Excel **lê** esses CSVs e atualiza sozinho.

---

## PASSO 1 — Rodar o exportador

Duplo-clique em **`INICIAR_EXPORTADOR_CSV.bat`**

Deixa essa janela aberta (ela alimenta os dados). Vai criar a pasta `dados_powerquery` com 7 arquivos CSV.

---

## PASSO 2 — Criar a conexão no Excel

Abra um Excel novo (ou o `RELATORIO_VTC_PQ.xlsx` se você rodou o `criar_planilha_pq.py`).

### 2.1. Conectar na pasta de CSVs

1. Aba **Dados** → **Obter Dados** → **De Arquivo** → **De Pasta**
2. Navegue até a pasta **`dados_powerquery`** → **Abrir**
3. Vai aparecer a lista dos 7 CSVs → clique em **Transformar Dados**

> Isso abre o Editor do Power Query. Não se assuste, são 3 cliques.

### 2.2. Importar cada CSV separadamente

No Editor do Power Query, é mais simples fazer um por vez. Feche o editor e faça assim:

Para **cada** um dos 7 arquivos (producao, estoque, movimentacoes, resumo_maquina, resumo_cor, resumo_dia, kpis):

1. Aba **Dados** → **Obter Dados** → **De Arquivo** → **De Texto/CSV**
2. Selecione o arquivo (ex.: `dados_powerquery\producao.csv`)
3. Confira na prévia:
   - **Delimitador:** Ponto e vírgula
   - **Origem do arquivo:** UTF-8
4. Clique em **Carregar** → **Carregar Para...**
5. Escolha **Tabela** → **Nova planilha** (ou planilha existente, se quiser controlar onde)
6. **OK**

Repita pros 7 arquivos. Leva uns 3 minutos no total.

---

## PASSO 3 — Ligar a atualização automática

Essa é a parte que faz a mágica.

### 3.1. Atualizar a cada X minutos

1. Aba **Dados** → **Consultas e Conexões**
2. Clique com o **botão direito** em cada consulta → **Propriedades**
3. Marque:
   - ☑ **Atualizar a cada** `1` minuto(s)  ← ajuste como quiser
   - ☑ **Atualizar dados ao abrir o arquivo**
   - ☑ **Habilitar atualização em segundo plano**
4. **OK**

Faça isso pras 7 consultas.

> **Atalho:** dá pra selecionar todas e mudar de uma vez em algumas versões do Excel. Se não der, é rapidinho fazer uma a uma.

### 3.2. Salvar

**Ctrl+S**. Salve como `RELATORIO_VTC_PQ.xlsx`.

---

## Pronto! Agora é só usar

- Deixe o **`INICIAR_EXPORTADOR_CSV.bat`** rodando
- Abra o **`RELATORIO_VTC_PQ.xlsx`** e deixe aberto
- A cada minuto ele puxa os dados novos sozinho
- Pra forçar agora: **Dados → Atualizar Tudo** (ou **Ctrl+Alt+F5**)

---

## Dicas

### Montar seus próprios gráficos e dashboards
Como as tabelas atualizam sozinhas, você pode:
- Criar **Tabelas Dinâmicas** em cima delas → atualizam junto
- Criar **gráficos** ligados às tabelas → atualizam junto
- Usar **fórmulas** referenciando as tabelas → atualizam junto

Faça o dashboard do seu jeito, ele fica vivo.

### Se der erro de caminho
Se você **mover a pasta** do sistema, o Power Query vai reclamar que não acha os CSVs. Conserto:
1. Dados → Obter Dados → **Configurações da Fonte de Dados**
2. Selecione o caminho antigo → **Alterar Fonte** → aponte pra pasta nova

### Ajustar a frequência
- No **Python** (`exportador_csv.py`): `INTERVALO_SEGUNDOS = 10` → de quanto em quanto tempo os CSVs são regravados
- No **Excel** (Propriedades da consulta): de quanto em quanto tempo o Excel lê os CSVs

Não adianta o Excel atualizar a cada 1 min se o Python só grava a cada 10 min. Mantenha o Python mais rápido que o Excel.

---

## Arquivos CSV gerados

| Arquivo | Conteúdo |
|---|---|
| `kpis.csv` | Indicadores do dia (bips, kg por material, última atualização) |
| `producao.csv` | Todos os bips de receita |
| `estoque.csv` | Saldo atual + status (OK/BAIXO/NEGATIVO) |
| `movimentacoes.csv` | Entradas e saídas de estoque |
| `resumo_maquina.csv` | Produção agrupada por máquina |
| `resumo_cor.csv` | Produção agrupada por cor |
| `resumo_dia.csv` | Produção por dia (pra gráfico de tendência) |
