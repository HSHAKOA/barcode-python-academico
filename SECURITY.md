# Política de Segurança e Sanitização Acadêmica

## 1. Natureza dos Dados Publicados

Este repositório contém exclusivamente código didático e **dados estritamente fictícios de demonstração** (`20,0 kg` base, `10,0 kg` moído e `0,5 kg` pigmento em `PACOTE_MAQUINA_NOVA/config_receitas.py`).

- Não contém credenciais de produção, bancos `.db` operacionais, endereços de rede internos ou formulações reais de fábrica.
- O repositório industrial privado original permanece separado e sem vínculo com este histórico Git.

## 2. Controles Técnicos Implementados no Código

- **API HTTP local (`api_vtc.py`):** escuta exclusivamente em `127.0.0.1:8765`, exigindo cabeçalho `X-API-Key` configurado via variável de ambiente `VTC_API_KEY` (com comparação em tempo constante `secrets.compare_digest` e rejeição da chave padrão de exemplo).
- **SQLite (`core_vtc.py`):** todas as consultas e inserções usam comandos parametrizados com placeholders `?`, prevenindo injeção de SQL.
- **Scripts Windows:** evitam caminhos fixos de usuários específicos (`%~dp0`, detecção automática de `.venv`), uso de `--host 0.0.0.0` ou alterações de plano de energia (`powercfg`).

## 3. Reporte de Problemas

Caso identifique qualquer dado sensível residual ou falha de segurança neste material acadêmico, abra uma *Issue* descrevendo o arquivo e a linha afetada ou entre em contato diretamente com o mantenedor do repositório.
