# Guia de Contribuição (`CONTRIBUTING.md`)

Contribuições acadêmicas, revisões didáticas e melhorias de testes são bem-vindas neste repositório público (`HSHAKOA/barcode-python-academico`).

---

## 1. Fluxo Recomendado

1. Faça um *Fork* deste repositório no GitHub ou clone diretamente para ambiente local de estudo:
   ```powershell
   git clone https://github.com/HSHAKOA/barcode-python-academico.git
   cd barcode-python-academico
   ```
2. Crie um ambiente virtual isolado e instale as dependências de desenvolvimento/execução:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r PACOTE_MAQUINA_NOVA\requirements.txt
   ```
3. Crie uma *branch* descritiva antes de editar:
   ```powershell
   git checkout -b melhoria/minha-alteracao
   ```

---

## 2. Regras Obrigatórias do Repositório Acadêmico

- **Proibido publicar dados reais de fábrica:** mantenha exclusivamente receitas demonstrativas fictícias em [`PACOTE_MAQUINA_NOVA/config_receitas.py`](PACOTE_MAQUINA_NOVA/config_receitas.py).
- **Não versionar arquivos gerados ou sensíveis:** nunca comite bancos `*.db*`, arquivos `.env*`, saídas `.csv`, `.xlsx`, `.pdf`, `.zpl` ou pastas `dados_powerquery/` e `.venv/`.
- **Arquitetura acíclica:** preserve a separação em camadas sem importações circulares (`config_receitas` → `core_vtc` / `etiquetas_vtc` / `scanner_vtc` → `barcode_vtc` / `api_vtc`).
- **Estilo de código:** siga **PEP 8** e **PEP 257** (*docstrings* objetivas) com funções curtas e portáteis.
- **Scripts Windows:** utilize caminhos relativos (`%~dp0`), detecção automática de `.venv` e codificação UTF-8 (`chcp 65001 >nul`), sem caminhos absolutos de usuário.

---

## 3. Validação Obrigatória Antes do Pull Request

Execute a suíte automatizada completa na raiz do repositório antes de enviar alterações:

```powershell
python -B -m unittest discover -s tests -v
```

- Todos os `20` testes devem passar em ambiente com `requirements.txt` instalado.
- Alterações em módulos principais devem continuar executando também em modo biblioteca padrão (`stdlib`, sem falhas nos 16 testes independentes de pacotes externos).
- Descreva claramente no *Pull Request* o objetivo da mudança, os arquivos alterados e o resultado da execução dos testes.
