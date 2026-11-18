"""Utilitário CLI para conferência rápida dos registros em barcode_vtc.db."""

import os
import sqlite3

PASTA = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PASTA, "barcode_vtc.db")


def _imprimir_producao(cursor: sqlite3.Cursor) -> None:
    try:
        cursor.execute("SELECT COUNT(*), MIN(data_hora), MAX(data_hora) FROM producao")
        total, primeiro, ultimo = cursor.fetchone()
        print("  PRODUCAO (bips registrados)")
        print(f"    Total de bips:        {total}")
        print(f"    Primeiro registro:    {primeiro}")
        print(f"    Ultimo registro:      {ultimo}")
    except Exception as exc:
        print(f"  [ERRO] Nao consegui ler a tabela 'producao': {exc}")
    print()


def _imprimir_estoque(cursor: sqlite3.Cursor) -> None:
    try:
        cursor.execute("SELECT material, cor, saldo_kg FROM estoque ORDER BY material, cor")
        linhas = cursor.fetchall()
        print("  ESTOQUE (saldo atual)")
        if not linhas:
            print("    (tabela vazia)")
        for material, cor, saldo in linhas:
            cor_txt = cor if cor else "-"
            print(f"    {material:<12} {cor_txt:<14} {saldo:>10.1f} kg")
    except Exception as exc:
        print(f"  [ERRO] Nao consegui ler a tabela 'estoque': {exc}")
    print()


def _imprimir_movimentacoes(cursor: sqlite3.Cursor) -> None:
    try:
        cursor.execute("SELECT COUNT(*) FROM mov_estoque")
        print(f"  MOVIMENTACOES registradas: {cursor.fetchone()[0]}")
    except Exception as exc:
        print(f"  [ERRO] Nao consegui ler a tabela 'mov_estoque': {exc}")
    print()


def _imprimir_ultimos_bips(cursor: sqlite3.Cursor) -> None:
    try:
        cursor.execute(
            "SELECT data_hora, maquina, receita, total_kg FROM producao ORDER BY id DESC LIMIT 5"
        )
        print("  ULTIMOS 5 BIPS:")
        for data_hora, maquina, receita, total_kg in cursor.fetchall():
            print(f"    {data_hora}  |  {maquina:<4}  |  {receita:<10}  |  {total_kg:.1f} kg")
    except Exception as exc:
        print(f"  [ERRO] Nao consegui listar os ultimos bips: {exc}")


def main() -> None:
    """Exibe resumo de produção, estoque e últimas leituras gravadas no banco local."""
    print("=" * 64)
    print("  Barcode Academico - Verificador de dados do barcode_vtc.db")
    print("=" * 64)
    print(f"  Procurando banco em: {DB_PATH}\n")

    if not os.path.exists(DB_PATH):
        print("  [X] ARQUIVO NAO ENCONTRADO NESTA PASTA.")
        input("\n  Pressione ENTER para fechar...")
        return

    print(f"  [OK] Arquivo encontrado ({os.path.getsize(DB_PATH) / 1024:.1f} KB)\n")
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        _imprimir_producao(cursor)
        _imprimir_estoque(cursor)
        _imprimir_movimentacoes(cursor)
        _imprimir_ultimos_bips(cursor)
    finally:
        conn.close()

    print("\n" + "=" * 64)
    input("\n  Pressione ENTER para fechar...")


if __name__ == "__main__":
    main()
