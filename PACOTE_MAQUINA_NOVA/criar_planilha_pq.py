"""Utilitário opcional que cria a planilha base RELATORIO_VTC_PQ.xlsx para Power Query."""

import os

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

PASTA = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(PASTA, "dados_powerquery")
EXCEL_PQ = os.path.join(PASTA, "RELATORIO_VTC_PQ.xlsx")

REFRESH_MINUTOS = 1

FONTE = "Calibri"
AZUL = "0F3460"
VERDE = "00B894"
BRANCO = "FFFFFF"

F_TITULO = Font(name=FONTE, size=18, bold=True, color=BRANCO)
F_HEADER = Font(name=FONTE, size=11, bold=True, color=BRANCO)
F_KPI_NUM = Font(name=FONTE, size=28, bold=True, color=AZUL)
F_KPI_LBL = Font(name=FONTE, size=10, color="666666")
F_NORMAL = Font(name=FONTE, size=10)
F_BOLD = Font(name=FONTE, size=11, bold=True)

FILL_TITULO = PatternFill("solid", fgColor=AZUL)
FILL_KPI = PatternFill("solid", fgColor="F1F3F5")
CENTRO = Alignment(horizontal="center", vertical="center")

ABAS_DADOS = {
    "KPIs": ["Indicador", "Valor"],
    "Produção": [
        "ID", "DataHora", "Maquina", "Receita", "Cor", "MarfimKg",
        "MoidoKg", "PigmentoKg", "TotalKg", "Operador", "Turno", "Data", "Hora",
    ],
    "Estoque": ["Material", "Cor", "SaldoKg", "Status"],
    "Movimentações": [
        "ID", "DataHora", "Tipo", "Material", "Cor", "Kg",
        "SaldoApos", "Origem", "Data",
    ],
    "Resumo Máquina": ["Maquina", "Bips", "MarfimKg", "MoidoKg", "PigmentoKg", "TotalKg"],
    "Resumo Cor": ["Cor", "Bips", "TotalKg"],
    "Resumo Dia": ["Data", "Bips", "MarfimKg", "MoidoKg", "PigmentoKg", "TotalKg"],
}


def _montar_dashboard(wb: Workbook) -> None:
    """Cria a aba Dashboard com cartões de KPIs vinculados à aba KPIs."""
    ws = wb.create_sheet("Dashboard")
    ws.merge_cells("A1:J1")
    ws["A1"] = "BARCODE ACADÊMICO — PAINEL DE PRODUÇÃO (DADOS FICTÍCIOS)"
    ws["A1"].font = F_TITULO
    ws["A1"].fill = FILL_TITULO
    ws["A1"].alignment = CENTRO
    ws.row_dimensions[1].height = 34

    ws.merge_cells("A2:J2")
    ws["A2"] = f"Conectado aos CSVs via Power Query · Atualiza sozinho a cada {REFRESH_MINUTOS} min · Pode deixar aberto"
    ws["A2"].font = Font(name=FONTE, size=9, italic=True, color="777777")
    ws["A2"].alignment = CENTRO

    kpis = [
        ("BIPS HOJE", '=IFERROR(INDEX(KPIs!B:B,MATCH("Bips Hoje",KPIs!A:A,0)),0)'),
        ("MARFIM (kg)", '=IFERROR(INDEX(KPIs!B:B,MATCH("Marfim Hoje (kg)",KPIs!A:A,0)),0)'),
        ("MOÍDO (kg)", '=IFERROR(INDEX(KPIs!B:B,MATCH("Moído Hoje (kg)",KPIs!A:A,0)),0)'),
        ("PIGMENTO (kg)", '=IFERROR(INDEX(KPIs!B:B,MATCH("Pigmento Hoje (kg)",KPIs!A:A,0)),0)'),
        ("TOTAL HOJE (kg)", '=IFERROR(INDEX(KPIs!B:B,MATCH("Total Hoje (kg)",KPIs!A:A,0)),0)'),
    ]

    for idx, (label, formula) in enumerate(kpis):
        col = idx * 2 + 1
        left_col = get_column_letter(col)
        right_col = get_column_letter(col + 1)

        ws.merge_cells(f"{left_col}4:{right_col}4")
        ws[f"{left_col}4"] = label
        ws[f"{left_col}4"].font = F_KPI_LBL
        ws[f"{left_col}4"].alignment = CENTRO
        ws[f"{left_col}4"].fill = FILL_KPI

        ws.merge_cells(f"{left_col}5:{right_col}6")
        ws[f"{left_col}5"] = formula
        ws[f"{left_col}5"].font = F_KPI_NUM
        ws[f"{left_col}5"].alignment = CENTRO
        ws[f"{left_col}5"].fill = FILL_KPI

        ws.column_dimensions[left_col].width = 11
        ws.column_dimensions[right_col].width = 11

    ws.row_dimensions[5].height = 30
    ws.row_dimensions[6].height = 14

    ws["A8"] = "Última atualização dos dados:"
    ws["A8"].font = F_BOLD
    ws["C8"] = '=IFERROR(INDEX(KPIs!B:B,MATCH("Última Atualização",KPIs!A:A,0)),"—")'
    ws["C8"].font = Font(name=FONTE, size=11, color=VERDE, bold=True)

    ws["A10"] = "COMO USAR"
    ws["A10"].font = F_BOLD
    instrucoes = [
        "1. Deixe o INICIAR_EXPORTADOR_CSV.bat rodando (ele alimenta os dados)",
        "2. Esta planilha se atualiza SOZINHA — pode deixar aberta o tempo todo",
        f"3. Atualização automática a cada {REFRESH_MINUTOS} minuto(s)",
        "4. Pra forçar agora: aba Dados -> Atualizar Tudo (ou Ctrl+Alt+F5)",
        "5. As abas Produção, Estoque, Movimentações e Resumos têm os dados completos",
    ]
    for row_idx, texto in enumerate(instrucoes, start=11):
        ws[f"A{row_idx}"] = texto
        ws[f"A{row_idx}"].font = F_NORMAL

    ws.sheet_view.showGridLines = False


def _criar_abas_dados(wb: Workbook) -> None:
    """Cria as sete abas de dados com cabeçalhos formatados para posterior vínculo Power Query."""
    for nome, cabecalho in ABAS_DADOS.items():
        ws = wb.create_sheet(nome)
        for col_idx, titulo in enumerate(cabecalho, 1):
            cell = ws.cell(row=1, column=col_idx, value=titulo)
            cell.font = F_HEADER
            cell.fill = FILL_TITULO
            cell.alignment = CENTRO
            ws.column_dimensions[get_column_letter(col_idx)].width = max(12, len(titulo) + 4)
        ws.freeze_panes = "A2"


def criar_planilha() -> str:
    """Gera o arquivo RELATORIO_VTC_PQ.xlsx e retorna o caminho criado."""
    wb = Workbook()
    wb.remove(wb.active)
    _montar_dashboard(wb)
    _criar_abas_dados(wb)
    wb.save(EXCEL_PQ)
    return EXCEL_PQ


def main() -> None:
    print("=" * 64)
    print("  Barcode Acadêmico — Criando planilha Power Query")
    print("=" * 64)
    os.makedirs(PASTA_DADOS, exist_ok=True)
    caminho = criar_planilha()
    print(f"\n  [OK] Planilha criada: {os.path.basename(caminho)}")
    print("\n  Conecte os CSVs manualmente no Excel seguindo: COMO_CONFIGURAR_POWER_QUERY.md\n")


if __name__ == "__main__":
    main()
    input("  Pressione ENTER para fechar...")
