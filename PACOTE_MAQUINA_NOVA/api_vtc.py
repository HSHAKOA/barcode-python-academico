"""API HTTP opcional (FastAPI) para consulta e lançamento integrado no mesmo SQLite."""

import os
import secrets
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

import core_vtc as core
from config_receitas import CORES, MAQUINAS

# Exige VTC_API_KEY configurada no ambiente e recusa a chave padrão conhecida
_CHAVE_PADRAO_INSEGURA = "vtc-troque-esta-chave"
API_KEY = os.environ.get("VTC_API_KEY", "").strip()


def _chave_segura_ativa() -> bool:
    """Retorna True somente quando VTC_API_KEY foi definida e difere da chave padrão."""
    return bool(API_KEY) and API_KEY != _CHAVE_PADRAO_INSEGURA


if not _chave_segura_ativa():
    print("[AVISO] VTC_API_KEY não configurada ou padrão — rotas protegidas bloqueadas.")


def checar_chave(x_api_key: Optional[str] = Header(default=None)) -> None:
    """Valida a configuração da API e compara X-API-Key em tempo constante."""
    if not _chave_segura_ativa():
        raise HTTPException(
            503,
            "API bloqueada: defina VTC_API_KEY com uma chave segura (chave padrão não é aceita).",
        )
    if not x_api_key or not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(401, "X-API-Key ausente ou inválida")


core.init_db()
app = FastAPI(title="Sistema Barcode Acadêmico — API de Integração")


class ApontamentoIn(BaseModel):
    codigo: str
    operador: str = ""


class EstoqueEntradaIn(BaseModel):
    material: str
    cor: str = ""
    kg: float
    origem: str = "API"


class EstoqueAjusteIn(BaseModel):
    material: str
    cor: str = ""
    saldo_kg: float


@app.get("/health")
def health() -> dict:
    """Informa disponibilidade da API e catálogo de máquinas/cores."""
    return {
        "status": "ok",
        "api_configurada": _chave_segura_ativa(),
        "maquinas": MAQUINAS,
        "cores": CORES,
    }


@app.get("/producao", dependencies=[Depends(checar_chave)])
def listar_producao(maquina: Optional[str] = None, data: Optional[str] = None, limite: int = 200) -> list[dict]:
    """Retorna apontamentos recentes filtrados por máquina, data e limite (1..5000)."""
    if limite < 1 or limite > 5000:
        raise HTTPException(400, "limite deve estar entre 1 e 5000")
    rows = core.buscar_producao(maquina=maquina, data=data, limite=limite)
    campos = [
        "id", "data_hora", "maquina", "receita", "cor", "marfim_kg",
        "moido_kg", "pigmento_kg", "total_kg", "operador", "turno",
    ]
    return [dict(zip(campos, r)) for r in rows]


@app.get("/estoque", dependencies=[Depends(checar_chave)])
def listar_estoque() -> list[dict]:
    """Lista os saldos atuais de todos os materiais e cores."""
    return [{"material": m, "cor": c, "saldo_kg": s} for m, c, s in core.get_todos_saldos()]


@app.get("/resumo", dependencies=[Depends(checar_chave)])
def resumo() -> dict:
    """Retorna os totalizadores do dia atual por máquina e geral."""
    por_maquina, totais = core.resumo_dia()
    return {
        "por_maquina": [
            {"maquina": m, "bips": b, "total_kg": t, "marfim_kg": mf, "moido_kg": mo, "pigmento_kg": p}
            for m, b, t, mf, mo, p in por_maquina
        ],
        "totais": {
            "bips": totais[0], "total_kg": totais[1], "marfim_kg": totais[2],
            "moido_kg": totais[3], "pigmento_kg": totais[4],
        },
    }


@app.post("/producao", dependencies=[Depends(checar_chave)])
def lancar_apontamento(body: ApontamentoIn) -> dict:
    """Decodifica e registra um apontamento utilizando a mesma transação da GUI."""
    info = core.decodificar(body.codigo)
    if not info:
        raise HTTPException(400, f"Código inválido: {body.codigo}")
    return core.registrar_producao(info, operador=body.operador)


@app.post("/estoque/entrada", dependencies=[Depends(checar_chave)])
def entrada_estoque(body: EstoqueEntradaIn) -> dict:
    """Adiciona quantidade positiva de material ao estoque."""
    try:
        novo = core.dar_entrada(body.material, body.cor, body.kg, body.origem)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return {"material": body.material, "cor": body.cor, "saldo_kg": novo}


@app.post("/estoque/ajuste", dependencies=[Depends(checar_chave)])
def ajuste_estoque(body: EstoqueAjusteIn) -> dict:
    """Ajusta manualmente o saldo exato de um material e registra a diferença."""
    try:
        novo = core.ajustar_saldo(body.material, body.cor, body.saldo_kg)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return {"material": body.material, "cor": body.cor, "saldo_kg": novo}
