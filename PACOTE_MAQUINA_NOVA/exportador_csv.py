"""Exportador contínuo do banco SQLite para CSVs consumidos pelo Excel/Power Query."""

import csv
import datetime
import os
import sqlite3
import time

INTERVALO_SEGUNDOS = 10

PASTA = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PASTA, "barcode_vtc.db")
PASTA_DADOS = os.path.join(PASTA, "dados_powerquery")

# Definição declarativa das visões exportadas: (chave, arquivo_csv, cabecalho, sql)
CONSULTAS_CSV = [
    (
        "producao",
        "producao.csv",
        ["ID", "DataHora", "Maquina", "Receita", "Cor",
         "MarfimKg", "MoidoKg", "PigmentoKg", "TotalKg",
         "Operador", "Turno", "Data", "Hora"],
        """
        SELECT id, data_hora, maquina, receita, cor,
               marfim_kg, moido_kg, pigmento_kg, total_kg,
               operador, turno,
               substr(data_hora, 1, 10) AS data,
               substr(data_hora, 12, 5) AS hora
        FROM producao ORDER BY id DESC
        """,
    ),
    (
        "estoque",
        "estoque.csv",
        ["Material", "Cor", "SaldoKg", "Status"],
        """
        SELECT material, cor, ROUND(saldo_kg, 3),
               CASE
                   WHEN saldo_kg < 0 THEN 'NEGATIVO'
                   WHEN saldo_kg < 50 THEN 'BAIXO'
                   ELSE 'OK'
               END AS status
        FROM estoque ORDER BY material, cor
        """,
    ),
    (
        "movimentacoes",
        "movimentacoes.csv",
        ["ID", "DataHora", "Tipo", "Material", "Cor", "Kg", "SaldoApos", "Origem", "Data"],
        """
        SELECT id, data_hora, tipo, material, cor, ROUND(kg, 3), ROUND(saldo_apos, 3), origem,
               substr(data_hora, 1, 10) AS data
        FROM mov_estoque ORDER BY id DESC
        """,
    ),
    (
        "resumo_maquina",
        "resumo_maquina.csv",
        ["Maquina", "Bips", "MarfimKg", "MoidoKg", "PigmentoKg", "TotalKg"],
        """
        SELECT maquina, COUNT(*) AS bips,
               ROUND(SUM(marfim_kg), 1), ROUND(SUM(moido_kg), 1),
               ROUND(SUM(pigmento_kg), 1), ROUND(SUM(total_kg), 1)
        FROM producao GROUP BY maquina ORDER BY maquina
        """,
    ),
    (
        "resumo_cor",
        "resumo_cor.csv",
        ["Cor", "Bips", "TotalKg"],
        """
        SELECT CASE WHEN cor = '' THEN 'Sem cor' ELSE cor END,
               COUNT(*) AS bips, ROUND(SUM(total_kg), 1)
        FROM producao GROUP BY cor ORDER BY cor
        """,
    ),
    (
        "resumo_dia",
        "resumo_dia.csv",
        ["Data", "Bips", "MarfimKg", "MoidoKg", "PigmentoKg", "TotalKg"],
        """
        SELECT substr(data_hora, 1, 10) AS data, COUNT(*) AS bips,
               ROUND(SUM(marfim_kg), 1), ROUND(SUM(moido_kg), 1),
               ROUND(SUM(pigmento_kg), 1), ROUND(SUM(total_kg), 1)
        FROM producao GROUP BY substr(data_hora, 1, 10) ORDER BY data DESC
        """,
    ),
]


def conectar() -> sqlite3.Connection:
    """Abre conexão SQLite preferencialmente em modo somente leitura (URI ?mode=ro)."""
    try:
        return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=5)
    except Exception:
        return sqlite3.connect(DB_PATH, timeout=5)


def exportar_csv(nome_arquivo: str, cabecalho: list[str], linhas: list[tuple] | list[list]) -> int:
    """Grava CSV via arquivo temporário + os.replace() para evitar leitura parcial."""
    caminho = os.path.join(PASTA_DADOS, nome_arquivo)
    caminho_tmp = caminho + ".tmp"
    with open(caminho_tmp, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(cabecalho)
        writer.writerows(linhas)
    os.replace(caminho_tmp, caminho)
    return len(linhas)


def _exportar_kpis(cursor: sqlite3.Cursor) -> int:
    """Calcula os indicadores resumidos da data atual e grava kpis.csv."""
    hoje = datetime.datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        """
        SELECT COUNT(*),
               ROUND(COALESCE(SUM(marfim_kg), 0), 1),
               ROUND(COALESCE(SUM(moido_kg), 0), 1),
               ROUND(COALESCE(SUM(pigmento_kg), 0), 1),
               ROUND(COALESCE(SUM(total_kg), 0), 1)
        FROM producao WHERE data_hora LIKE ?
        """,
        (f"{hoje}%",),
    )
    row = cursor.fetchone()
    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    linhas = [
        ["Bips Hoje", row[0]],
        ["Marfim Hoje (kg)", row[1]],
        ["Moído Hoje (kg)", row[2]],
        ["Pigmento Hoje (kg)", row[3]],
        ["Total Hoje (kg)", row[4]],
        ["Última Atualização", agora],
    ]
    return exportar_csv("kpis.csv", ["Indicador", "Valor"], linhas)


def exportar_tudo() -> dict | None:
    """Exporta as 7 visões CSV a partir de barcode_vtc.db. Retorna estatísticas por tabela."""
    if not os.path.exists(DB_PATH):
        return None

    os.makedirs(PASTA_DADOS, exist_ok=True)
    conn = conectar()
    stats = {}

    try:
        cursor = conn.cursor()
        for chave, arquivo, cabecalho, sql in CONSULTAS_CSV:
            try:
                cursor.execute(sql)
                stats[chave] = exportar_csv(arquivo, cabecalho, cursor.fetchall())
            except Exception as exc:
                stats[chave] = f"erro: {exc}"

        try:
            stats["kpis"] = _exportar_kpis(cursor)
        except Exception as exc:
            stats["kpis"] = f"erro: {exc}"
    finally:
        conn.close()

    return stats


def main() -> None:
    """Executa o loop contínuo de exportação a cada INTERVALO_SEGUNDOS."""
    print("=" * 64)
    print("  Barcode Acadêmico — Exportador de CSV para Power Query")
    print("=" * 64)
    print(f"  Banco:     {DB_PATH}")
    print(f"  CSVs:      {PASTA_DADOS}")
    print(f"  Intervalo: {INTERVALO_SEGUNDOS}s")
    print("=" * 64)
    print("\n  Rodando... (Ctrl+C ou feche esta janela para parar)\n")

    ciclo = 0
    while True:
        try:
            stats = exportar_tudo()
            if stats is None:
                print(f"  [{datetime.datetime.now():%H:%M:%S}] Banco não encontrado. Aguardando...", end="\r")
            else:
                ciclo += 1
                n_prod = stats.get("producao", 0)
                n_mov = stats.get("movimentacoes", 0)
                print(
                    f"  [{datetime.datetime.now():%H:%M:%S}] "
                    f"CSVs atualizados (#{ciclo}) — {n_prod} produção · {n_mov} movimentações      ",
                    end="\r",
                )
        except Exception as exc:
            print(f"\n  [ERRO] {exc}")

        time.sleep(INTERVALO_SEGUNDOS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Encerrando. Até mais.\n")
