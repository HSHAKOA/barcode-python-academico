"""Geração de códigos e etiquetas de receita nos formatos PDF (Code 128) e ZPL."""

import datetime

from config_receitas import CORES_HEX, MAQUINAS, MARFIM_KG_POR_BIP, RECEITAS


def calcular_total_receita(receita: dict) -> float:
    """Calcula o peso total previsto (kg) somando Marfim, Moído e Pigmento."""
    total = MARFIM_KG_POR_BIP + receita["moido_kg"] + receita["pigmento_kg"]
    return round(total, 4)


def listar_codigos(maquina_cod: str | None = None) -> list[tuple[str, str, str, str, float]]:
    """Retorna lista de (codigo, maquina, receita_nome, cor, total_kg) por máquina."""
    codigos = []
    maqs = [maquina_cod] if maquina_cod else list(MAQUINAS.keys())
    for mcod in maqs:
        for rkey, rec in RECEITAS.items():
            codigo = f"{mcod}-{rkey}"
            total = calcular_total_receita(rec)
            codigos.append((codigo, MAQUINAS[mcod], rec["nome"], rec["cor"], total))
    return codigos


def _desenhar_etiqueta_pdf(pdf_canvas, slot: int, largura: float, altura: float, dados: tuple) -> None:
    """Desenha uma etiqueta (metade superior ou inferior da página A4) no canvas ReportLab."""
    from reportlab.graphics.barcode import code128
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import mm

    codigo, maquina, receita, cor, total = dados
    y_base = (altura / 2 + 10 * mm) if slot == 0 else 10 * mm
    label_h = altura / 2 - 20 * mm
    xm = 18 * mm
    cor_header = HexColor(CORES_HEX.get(cor, CORES_HEX["Sem cor"]))

    pdf_canvas.setStrokeColor(HexColor("#333333"))
    pdf_canvas.setLineWidth(2)
    pdf_canvas.roundRect(xm, y_base, largura - 2 * xm, label_h, 5 * mm)

    pdf_canvas.setFillColor(cor_header)
    pdf_canvas.roundRect(xm, y_base + label_h - 20 * mm, largura - 2 * xm, 20 * mm, 5 * mm, fill=1, stroke=0)
    pdf_canvas.rect(xm, y_base + label_h - 20 * mm, largura - 2 * xm, 12 * mm, fill=1, stroke=0)

    pdf_canvas.setFillColor(HexColor("#ffffff"))
    pdf_canvas.setFont("Helvetica-Bold", 24)
    pdf_canvas.drawCentredString(largura / 2, y_base + label_h - 15 * mm, maquina.upper())

    pdf_canvas.setFillColor(HexColor("#000000"))
    pdf_canvas.setFont("Helvetica-Bold", 20)
    pdf_canvas.drawCentredString(largura / 2, y_base + label_h - 32 * mm, receita)

    pdf_canvas.setFont("Helvetica-Bold", 30)
    pdf_canvas.drawCentredString(largura / 2, y_base + label_h - 48 * mm, cor)

    pdf_canvas.setFont("Courier-Bold", 40)
    pdf_canvas.drawCentredString(largura / 2, y_base + label_h - 68 * mm, codigo)

    barcode = code128.Code128(codigo, barWidth=0.8 * mm, barHeight=16 * mm)
    barcode.drawOn(pdf_canvas, (largura - barcode.width) / 2, y_base + 20 * mm)

    pdf_canvas.setFont("Helvetica-Bold", 22)
    pdf_canvas.setFillColor(HexColor("#006"))
    pdf_canvas.drawCentredString(largura / 2, y_base + 8 * mm, f"Total receita: {total:.1f} kg/bip")

    pdf_canvas.setFont("Helvetica", 8)
    pdf_canvas.setFillColor(HexColor("#888"))
    pdf_canvas.drawCentredString(largura / 2, y_base + 2 * mm, "Projeto Acadêmico · Receitas Fictícias de Demonstração")


def gerar_pdf_etiquetas(filepath: str, maquina_cod: str | None = None) -> None:
    """Gera arquivo PDF A4 (duas etiquetas por página) com código de barras Code 128."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    largura, altura = A4
    pdf_canvas = canvas.Canvas(filepath, pagesize=A4)
    pdf_canvas.setTitle("Barcode Acadêmico — Etiquetas de Receita")

    for indice, dados in enumerate(listar_codigos(maquina_cod)):
        if indice > 0 and indice % 2 == 0:
            pdf_canvas.showPage()
        _desenhar_etiqueta_pdf(pdf_canvas, indice % 2, largura, altura, dados)

    pdf_canvas.save()


def gerar_zpl_etiquetas(filepath: str, maquina_cod: str | None = None) -> None:
    """Gera arquivo de comandos ZPL (Zebra) em UTF-8 (^CI28)."""
    lines = [
        "; Barcode Acadêmico — Etiquetas de Receita (Fictícias)",
        f"; Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "; Formato: 100mm x 60mm (ajuste ^PW e ^LL conforme impressora)",
        "",
    ]
    for codigo, maquina, receita, cor, total in listar_codigos(maquina_cod):
        lines.extend([
            f"; -- {maquina} / {receita} / {cor} --",
            "^XA",
            "^CI28",
            "^PW800",
            "^LL480",
            f"^FO30,20^A0N,45,45^FD{maquina.upper()}^FS",
            f"^FO30,75^A0N,30,30^FD{receita}^FS",
            f"^FO30,115^A0N,45,45^FD{cor}^FS",
            "^FO30,170^GB740,2,2^FS",
            f"^FO120,185^BY3^BCN,90,Y,N,N^FD{codigo}^FS",
            f"^FO30,310^A0N,35,35^FDTotal: {total:.1f} kg/bip^FS",
            "^FO30,355^A0N,18,18^FDProjeto Academico - Demo^FS",
            "^XZ",
            "",
        ])
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
