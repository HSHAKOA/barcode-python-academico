"""Núcleo de regras de negócio, controle de estoque e persistência SQLite."""

import datetime
import math
import os
import sqlite3
from contextlib import contextmanager

from config_receitas import CORES, MAQUINAS, MARFIM_KG_POR_BIP, RECEITAS
from etiquetas_vtc import (
    calcular_total_receita,
    gerar_pdf_etiquetas,
    gerar_zpl_etiquetas,
    listar_codigos,
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "barcode_vtc.db")


@contextmanager
def _db(escrita: bool = False):
    """Abre conexão SQLite com commit no sucesso, rollback em falha e fechamento garantido."""
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.execute("PRAGMA busy_timeout = 15000")
    try:
        # BEGIN IMMEDIATE adquire trava de escrita antes do SELECT inicial, evitando lost update.
        if escrita:
            conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def materiais_estoque() -> list[tuple[str, str]]:
    """Retorna os pares (material, cor) controlados no estoque."""
    itens = [("Marfim", "")]
    for cor in CORES:
        itens.append(("Moído", cor))
    for cor in CORES:
        itens.append(("Pigmento", cor))
    return itens


def _validar_material(material: str, cor: str) -> None:
    """Garante que o par (material, cor) pertence ao catálogo configurado."""
    if (material, cor) not in materiais_estoque():
        cor_txt = cor if cor else "sem cor"
        raise ValueError(f"Material/cor inválido: {material} ({cor_txt})")


def _validar_kg(valor: float, exigir_positivo: bool = True) -> None:
    """Rejeita valores booleanos, não numéricos, NaN, infinito e valores não positivos."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor):
        raise ValueError("Quantidade deve ser um número finito.")
    if exigir_positivo and valor <= 0:
        raise ValueError("Quantidade deve ser positiva.")


def init_db() -> None:
    """Inicializa tabelas, índices, modo WAL e saldos iniciais no banco SQLite."""
    # PRAGMA journal_mode=WAL precisa rodar fora de BEGIN IMMEDIATE.
    with _db() as conn:
        c = conn.cursor()
        c.execute("PRAGMA journal_mode=WAL")

        c.execute("""
            CREATE TABLE IF NOT EXISTS producao (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo       TEXT NOT NULL,
                maquina      TEXT NOT NULL,
                receita      TEXT NOT NULL,
                cor          TEXT DEFAULT '',
                marfim_kg    REAL DEFAULT 0,
                moido_kg     REAL DEFAULT 0,
                pigmento_kg  REAL DEFAULT 0,
                total_kg     REAL DEFAULT 0,
                operador     TEXT DEFAULT '',
                turno        TEXT DEFAULT '',
                data_hora    TEXT NOT NULL
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS estoque (
                material  TEXT NOT NULL,
                cor       TEXT DEFAULT '',
                saldo_kg  REAL DEFAULT 0,
                PRIMARY KEY (material, cor)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS mov_estoque (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo       TEXT NOT NULL,
                material   TEXT NOT NULL,
                cor        TEXT DEFAULT '',
                kg         REAL NOT NULL,
                saldo_apos REAL DEFAULT 0,
                origem     TEXT DEFAULT '',
                data_hora  TEXT NOT NULL
            )
        """)

        c.execute("CREATE INDEX IF NOT EXISTS idx_prod_dt ON producao(data_hora)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_prod_maq ON producao(maquina)")

        for material, cor in materiais_estoque():
            c.execute(
                "INSERT OR IGNORE INTO estoque (material, cor, saldo_kg) VALUES (?, ?, 0)",
                (material, cor),
            )


def turno_atual() -> str:
    """Classifica o turno industrial conforme a hora atual do sistema."""
    hora = datetime.datetime.now().hour
    if 6 <= hora < 14:
        return "1º Turno"
    if 14 <= hora < 22:
        return "2º Turno"
    return "3º Turno"


def get_saldo(material: str, cor: str = "") -> float:
    """Consulta o saldo atual (kg) de um material e cor."""
    with _db() as conn:
        c = conn.cursor()
        c.execute("SELECT saldo_kg FROM estoque WHERE material=? AND cor=?", (material, cor))
        row = c.fetchone()
    return row[0] if row else 0.0


def get_todos_saldos() -> list[tuple[str, str, float]]:
    """Retorna lista ordenada de (material, cor, saldo_kg)."""
    with _db() as conn:
        c = conn.cursor()
        c.execute("SELECT material, cor, saldo_kg FROM estoque ORDER BY material, cor")
        return c.fetchall()


def _aplicar_movimento(
    cursor: sqlite3.Cursor,
    material: str,
    cor: str,
    delta_kg: float,
    tipo: str,
    origem: str,
    agora: str,
    kg_registro: float | None = None,
) -> float:
    """Atualiza o saldo na tabela estoque e grava a movimentação correspondente."""
    cursor.execute("SELECT saldo_kg FROM estoque WHERE material=? AND cor=?", (material, cor))
    row = cursor.fetchone()
    atual = row[0] if row else 0.0
    novo = atual + delta_kg

    cursor.execute(
        """
        INSERT INTO estoque (material, cor, saldo_kg) VALUES (?, ?, ?)
        ON CONFLICT(material, cor) DO UPDATE SET saldo_kg = excluded.saldo_kg
        """,
        (material, cor, novo),
    )
    valor_log = abs(delta_kg) if kg_registro is None else kg_registro
    cursor.execute(
        """
        INSERT INTO mov_estoque (tipo, material, cor, kg, saldo_apos, origem, data_hora)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (tipo, material, cor, valor_log, novo, origem, agora),
    )
    return novo


def _mover_estoque(material: str, cor: str, kg: float, tipo: str, origem: str) -> tuple[float, bool]:
    """Executa entrada ou saída isolada e retorna (novo_saldo, ficou_negativo)."""
    _validar_material(material, cor)
    _validar_kg(kg, exigir_positivo=True)
    sinal = 1 if tipo == "ENTRADA" else -1
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _db(escrita=True) as conn:
        novo = _aplicar_movimento(conn.cursor(), material, cor, sinal * kg, tipo, origem, agora)
    return novo, novo < 0


def dar_entrada(material: str, cor: str, kg: float, origem: str = "Manual") -> float:
    """Adiciona kg positivos ao estoque e retorna o saldo atualizado."""
    novo, _ = _mover_estoque(material, cor, kg, "ENTRADA", origem)
    return novo


def consumir(material: str, cor: str, kg: float, origem: str = "") -> tuple[float, bool]:
    """Desconta kg positivos do estoque e retorna (novo_saldo, ficou_negativo)."""
    return _mover_estoque(material, cor, kg, "SAIDA", origem)


def ajustar_saldo(material: str, cor: str, novo_saldo: float) -> float:
    """Define o saldo exato de um material e registra a diferença como 'AJUSTE'."""
    _validar_material(material, cor)
    _validar_kg(novo_saldo, exigir_positivo=False)
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _db(escrita=True) as conn:
        c = conn.cursor()
        c.execute("SELECT saldo_kg FROM estoque WHERE material=? AND cor=?", (material, cor))
        row = c.fetchone()
        diff = novo_saldo - (row[0] if row else 0.0)
        _aplicar_movimento(c, material, cor, diff, "AJUSTE", "Ajuste manual", agora, kg_registro=diff)
    return novo_saldo


def decodificar(codigo: str | None) -> dict | None:
    """Valida e decodifica '{MAQ}-{RECEITA}' retornando um dicionário com as quantidades, ou None."""
    if not isinstance(codigo, str):
        return None
    codigo = codigo.strip().upper()
    if "-" not in codigo:
        return None

    maq_cod, receita_key = codigo.split("-", 1)
    if maq_cod not in MAQUINAS or receita_key not in RECEITAS:
        return None

    rec = RECEITAS[receita_key]
    return {
        "codigo":      codigo,
        "maquina_cod": maq_cod,
        "maquina":     MAQUINAS[maq_cod],
        "receita_key": receita_key,
        "receita":     rec["nome"],
        "cor":         rec["cor"],
        "marfim_kg":   MARFIM_KG_POR_BIP,
        "moido_kg":    rec["moido_kg"],
        "pigmento_kg": rec["pigmento_kg"],
        "total_kg":    calcular_total_receita(rec),
    }


def registrar_producao(info: dict, operador: str = "") -> dict:
    """Registra apontamento e desconta materiais em transação única, retornando bips, acumulado e avisos."""
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    origem = info["codigo"]
    operador_limpo = operador.strip() if isinstance(operador, str) else ""
    avisos = []

    with _db(escrita=True) as conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO producao (codigo, maquina, receita, cor, marfim_kg, moido_kg,
                                  pigmento_kg, total_kg, operador, turno, data_hora)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                info["codigo"], info["maquina"], info["receita"], info["cor"],
                info["marfim_kg"], info["moido_kg"], info["pigmento_kg"],
                info["total_kg"], operador_limpo, turno_atual(), agora,
            ),
        )

        consumos = [("Marfim", "", info["marfim_kg"], "Marfim")]
        if info["moido_kg"] > 0:
            consumos.append(("Moído", info["cor"], info["moido_kg"], f"Moído {info['cor']}"))
        if info["pigmento_kg"] > 0:
            consumos.append(("Pigmento", info["cor"], info["pigmento_kg"], f"Pigmento {info['cor']}"))

        for material, cor, kg, rotulo in consumos:
            saldo = _aplicar_movimento(c, material, cor, -kg, "SAIDA", origem, agora)
            if saldo < 0:
                avisos.append(f"{rotulo} NEGATIVO: {saldo:.1f} kg")

        hoje = agora[:10]
        c.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(total_kg), 0) FROM producao
            WHERE maquina=? AND receita=? AND cor=? AND data_hora LIKE ?
            """,
            (info["maquina"], info["receita"], info["cor"], f"{hoje}%"),
        )
        bips, acum = c.fetchone()

    return {"bips": bips, "acum_kg": acum, "avisos": avisos}


def buscar_producao(maquina: str | None = None, data: str | None = None, limite: int = 200) -> list[tuple]:
    """Consulta apontamentos recentes com filtros opcionais de máquina, data e limite."""
    if not isinstance(limite, int) or isinstance(limite, bool) or limite <= 0:
        limite = 200
    limite = min(limite, 50000)

    with _db() as conn:
        c = conn.cursor()
        q = (
            "SELECT id, data_hora, maquina, receita, cor, marfim_kg, moido_kg, "
            "pigmento_kg, total_kg, operador, turno FROM producao"
        )
        wh, params = [], []
        if maquina and maquina != "Todas":
            wh.append("maquina=?")
            params.append(maquina)
        if data:
            wh.append("data_hora LIKE ?")
            params.append(f"{data}%")
        if wh:
            q += " WHERE " + " AND ".join(wh)
        q += " ORDER BY id DESC LIMIT ?"
        params.append(limite)
        c.execute(q, params)
        return c.fetchall()


def resumo_dia() -> tuple[list[tuple], tuple]:
    """Retorna (por_maquina, totais) agregados para a data atual."""
    with _db() as conn:
        c = conn.cursor()
        hoje = datetime.datetime.now().strftime("%Y-%m-%d")

        c.execute(
            """
            SELECT maquina, COUNT(*), SUM(total_kg), SUM(marfim_kg), SUM(moido_kg), SUM(pigmento_kg)
            FROM producao WHERE data_hora LIKE ?
            GROUP BY maquina ORDER BY maquina
            """,
            (f"{hoje}%",),
        )
        por_maquina = c.fetchall()

        c.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(total_kg), 0), COALESCE(SUM(marfim_kg), 0),
                   COALESCE(SUM(moido_kg), 0), COALESCE(SUM(pigmento_kg), 0)
            FROM producao WHERE data_hora LIKE ?
            """,
            (f"{hoje}%",),
        )
        totais = c.fetchone()
    return por_maquina, totais


__all__ = [
    "DB_PATH",
    "ajustar_saldo",
    "buscar_producao",
    "calcular_total_receita",
    "consumir",
    "dar_entrada",
    "decodificar",
    "gerar_pdf_etiquetas",
    "gerar_zpl_etiquetas",
    "get_saldo",
    "get_todos_saldos",
    "init_db",
    "listar_codigos",
    "materiais_estoque",
    "registrar_producao",
    "resumo_dia",
    "turno_atual",
]
