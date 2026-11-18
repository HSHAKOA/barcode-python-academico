"""Interface gráfica (Tkinter) para apontamento de produção, estoque e etiquetas."""

import csv
import datetime
import math
import os
import queue
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import core_vtc as core
from config_receitas import CORES, MAQUINAS
from scanner_vtc import ScannerListener, _char_valido

# Paleta visual e fontes da interface
BG = "#0f0f1a"
BG2 = "#1a1a2e"
ACCENT = "#0f3460"
GREEN = "#00b894"
YELLOW = "#fdcb6e"
RED = "#d63031"
WHITE = "#ffffff"
TEXT = "#dfe6e9"
BLUE = "#0984e3"
FONT = "Segoe UI"
MONO = "Consolas"


def _abrir_arquivo(caminho: str) -> None:
    """Tenta abrir o arquivo no aplicativo padrão do Windows sem falhar se não houver associação."""
    try:
        os.startfile(caminho)
    except Exception:
        pass


def _tocar_bip(frequencia: int, duracao_ms: int) -> None:
    """Emite sinal sonoro no Windows sem interromper execução em outros sistemas."""
    try:
        import winsound
        winsound.Beep(frequencia, duracao_ms)
    except Exception:
        pass


def _limpar_tabela(tree: ttk.Treeview) -> None:
    """Remove todas as linhas visíveis de um widget Treeview."""
    itens = tree.get_children()
    if itens:
        tree.delete(*itens)


def _criar_tabela(
    parent: tk.Widget,
    especificacao: list[tuple[str, int, str]],
    altura: int,
    com_scroll: bool = False,
) -> tuple[ttk.Treeview, ttk.Scrollbar | None]:
    """Cria e configura um ttk.Treeview a partir de uma lista de (id, largura, título)."""
    colunas = tuple(col_id for col_id, _, _ in especificacao)
    tree = ttk.Treeview(parent, columns=colunas, show="headings", height=altura)
    for col_id, largura, titulo in especificacao:
        tree.heading(col_id, text=titulo)
        tree.column(col_id, width=largura, anchor="center")

    scroll = None
    if com_scroll:
        scroll = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
    return tree, scroll


class App:
    """Aplicação principal Tkinter com cinco abas e captura por leitor ou teclado."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Sistema Barcode Acadêmico — Produção por Receita")
        self.root.geometry("1360x870")
        self.root.configure(bg=BG)
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        self.operador = tk.StringVar(value="")
        self.fila: queue.Queue[str] = queue.Queue()
        self.listener = ScannerListener(self.fila)
        self.listener.start()
        self._ultimo_hook_ativo: bool | None = None

        self.buf_tk = ""
        self.buf_timer = None

        self._styles()
        self._construir_abas()

        root.bind("<Key>", self._on_key_tk)
        root.bind("<Return>", self._on_enter_tk)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._refresh_estoque()
        self._refresh_resumo()
        self._poll()

    def _construir_abas(self) -> None:
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=4, pady=4)

        abas = [
            ("  🔍  PRODUÇÃO  ", self._build_producao),
            ("  📦  ESTOQUE  ", self._build_estoque),
            ("  🏷️  ETIQUETAS  ", self._build_etiquetas),
            ("  📋  HISTÓRICO  ", self._build_historico),
            ("  📊  RESUMO  ", self._build_resumo),
        ]
        for titulo, builder in abas:
            frame = tk.Frame(nb, bg=BG)
            nb.add(frame, text=titulo)
            builder(frame)

    def _on_close(self) -> None:
        self.listener.stop()
        self.root.destroy()

    def _poll(self) -> None:
        if hasattr(self, "lbl_bg") and self.listener.hook_ativo != self._ultimo_hook_ativo:
            self._ultimo_hook_ativo = self.listener.hook_ativo
            if self._ultimo_hook_ativo:
                self.lbl_bg.config(text="🟢 SEGUNDO PLANO ATIVO", fg=GREEN)
            else:
                self.lbl_bg.config(text="🟡 MODO JANELA (foco necessário)", fg=YELLOW)

        try:
            while not self.fila.empty():
                self._processar(self.fila.get_nowait())
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _styles(self) -> None:
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TNotebook", background=BG)
        s.configure("TNotebook.Tab", background=ACCENT, foreground=TEXT, padding=[18, 8], font=(FONT, 11, "bold"))
        s.map("TNotebook.Tab", background=[("selected", GREEN)], foreground=[("selected", "#000")])
        s.configure("Treeview", background=BG2, foreground=TEXT, rowheight=27, fieldbackground=BG2, font=(MONO, 10))
        s.configure("Treeview.Heading", background=ACCENT, foreground=TEXT, font=(FONT, 10, "bold"))
        s.map("Treeview", background=[("selected", ACCENT)])

    # ── Aba Produção ────────────────────────────────────────────────────────────

    def _build_producao(self, f: tk.Frame) -> None:
        self._build_barra_producao(f)
        centro = tk.Frame(f, bg=BG)
        centro.pack(fill="both", expand=True, padx=20, pady=8)
        self._build_painel_receita(centro)
        self._build_lista_recentes(centro)
        self._build_rodape_producao(f)

    def _build_barra_producao(self, f: tk.Frame) -> None:
        top = tk.Frame(f, bg=BG)
        top.pack(fill="x", padx=20, pady=(12, 4))
        tk.Label(top, text="OPERADOR:", bg=BG, fg=TEXT, font=(FONT, 11, "bold")).pack(side="left")
        tk.Entry(
            top, textvariable=self.operador, bg=BG2, fg=WHITE, font=(FONT, 12),
            insertbackground=WHITE, width=20, relief="flat",
        ).pack(side="left", padx=(8, 0), ipady=4)

        self.lbl_bg = tk.Label(top, text="🟡 INICIANDO LEITOR...", bg=BG, fg=YELLOW, font=(FONT, 10, "bold"))
        self.lbl_bg.pack(side="left", padx=20)
        self.lbl_status = tk.Label(top, text="●  AGUARDANDO BIP", bg=BG, fg=YELLOW, font=(FONT, 11, "bold"))
        self.lbl_status.pack(side="right")

    def _build_painel_receita(self, centro: tk.Frame) -> None:
        left = tk.Frame(centro, bg=BG2)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        tk.Label(left, text="ÚLTIMA RECEITA", bg=BG2, fg=TEXT, font=(FONT, 13, "bold")).pack(pady=(16, 2))
        self.d_maq = tk.Label(left, text="  —  ", bg=ACCENT, fg=WHITE, font=(FONT, 18, "bold"), padx=18, pady=4)
        self.d_maq.pack(pady=(6, 4))
        self.d_receita = tk.Label(left, text="aguardando bip...", bg=BG2, fg="#636e72", font=(FONT, 22, "bold"))
        self.d_receita.pack(pady=(4, 0))
        self.d_cor = tk.Label(left, text="", bg=BG2, fg=TEXT, font=(FONT, 18))
        self.d_cor.pack(pady=2)
        self.d_codigo = tk.Label(left, text="", bg=BG2, fg="#636e72", font=(MONO, 16))
        self.d_codigo.pack(pady=2)

        tk.Frame(left, bg=ACCENT, height=2).pack(fill="x", padx=60, pady=8)

        comp = tk.Frame(left, bg=BG2)
        comp.pack(pady=4)
        self.d_marfim = tk.Label(comp, text="Marfim\n—", bg=BG2, fg=BLUE, font=(FONT, 14, "bold"), width=12)
        self.d_marfim.grid(row=0, column=0, padx=8)
        self.d_moido = tk.Label(comp, text="Moído\n—", bg=BG2, fg=GREEN, font=(FONT, 14, "bold"), width=12)
        self.d_moido.grid(row=0, column=1, padx=8)
        self.d_pigmento = tk.Label(comp, text="Pigmento\n—", bg=BG2, fg=YELLOW, font=(FONT, 14, "bold"), width=12)
        self.d_pigmento.grid(row=0, column=2, padx=8)

        self.d_total = tk.Label(left, text="0.0 kg", bg=BG2, fg=GREEN, font=(FONT, 64, "bold"))
        self.d_total.pack(pady=(10, 0))
        tk.Label(left, text="total da receita", bg=BG2, fg=TEXT, font=(FONT, 11)).pack()

        self.d_bips = tk.Label(left, text="", bg=BG2, fg=YELLOW, font=(FONT, 13))
        self.d_bips.pack(pady=(8, 2))
        self.d_aviso = tk.Label(left, text="", bg=BG2, fg=RED, font=(FONT, 12, "bold"))
        self.d_aviso.pack(pady=(0, 14))

    def _build_lista_recentes(self, centro: tk.Frame) -> None:
        right = tk.Frame(centro, bg=BG2, width=440)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        tk.Label(right, text="BIPS RECENTES", bg=BG2, fg=TEXT, font=(FONT, 11, "bold")).pack(pady=(12, 4))

        espec = [("hora", 58, "Hora"), ("maq", 70, "Máquina"), ("receita", 130, "Receita"), ("cor", 90, "Cor"), ("kg", 60, "kg")]
        self.tree_rec, _ = _criar_tabela(right, espec, altura=22)
        self.tree_rec.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _build_rodape_producao(self, f: tk.Frame) -> None:
        foot = tk.Frame(f, bg=ACCENT)
        foot.pack(fill="x", padx=20, pady=(0, 8))
        self.ft_bips = tk.Label(foot, text="Bips hoje: 0", bg=ACCENT, fg=WHITE, font=(FONT, 11, "bold"))
        self.ft_bips.pack(side="left", padx=16, pady=6)
        self.ft_marfim = tk.Label(foot, text="Marfim: 0 kg", bg=ACCENT, fg=BLUE, font=(FONT, 11, "bold"))
        self.ft_marfim.pack(side="left", padx=16, pady=6)
        self.ft_moido = tk.Label(foot, text="Moído: 0 kg", bg=ACCENT, fg=GREEN, font=(FONT, 11, "bold"))
        self.ft_moido.pack(side="left", padx=16, pady=6)
        self.ft_pig = tk.Label(foot, text="Pigmento: 0 kg", bg=ACCENT, fg=YELLOW, font=(FONT, 11, "bold"))
        self.ft_pig.pack(side="left", padx=16, pady=6)
        self.ft_total = tk.Label(foot, text="TOTAL: 0 kg", bg=ACCENT, fg=WHITE, font=(FONT, 11, "bold"))
        self.ft_total.pack(side="right", padx=16, pady=6)

    # ── Aba Estoque ─────────────────────────────────────────────────────────────

    def _build_estoque(self, f: tk.Frame) -> None:
        tk.Label(f, text="ESTOQUE DE MATERIAIS", bg=BG, fg=GREEN, font=(FONT, 16, "bold")).pack(pady=(16, 4))
        tk.Label(
            f, text="Dê entrada do estoque inicial ou reposição. Cada bip de receita desconta automaticamente.",
            bg=BG, fg=TEXT, font=(FONT, 11),
        ).pack(pady=(0, 10))

        entrada = tk.LabelFrame(f, text="  ENTRADA DE ESTOQUE  ", bg=BG2, fg=GREEN, font=(FONT, 12, "bold"), relief="flat")
        entrada.pack(fill="x", padx=30, pady=(0, 10))
        row = tk.Frame(entrada, bg=BG2)
        row.pack(fill="x", padx=16, pady=12)

        tk.Label(row, text="Material:", bg=BG2, fg=TEXT, font=(FONT, 11)).pack(side="left")
        self.e_material = tk.StringVar(value="Marfim")
        cb_mat = ttk.Combobox(row, textvariable=self.e_material, state="readonly", width=12, values=["Marfim", "Moído", "Pigmento"])
        cb_mat.pack(side="left", padx=6)
        cb_mat.bind("<<ComboboxSelected>>", self._on_material_change)

        tk.Label(row, text="Cor:", bg=BG2, fg=TEXT, font=(FONT, 11)).pack(side="left", padx=(12, 0))
        self.e_cor = tk.StringVar(value="—")
        self.cb_cor = ttk.Combobox(row, textvariable=self.e_cor, state="readonly", width=14, values=["—"])
        self.cb_cor.pack(side="left", padx=6)

        tk.Label(row, text="Qtd (kg):", bg=BG2, fg=TEXT, font=(FONT, 11)).pack(side="left", padx=(12, 0))
        self.e_qtd = tk.StringVar(value="1000")
        tk.Entry(row, textvariable=self.e_qtd, bg=BG, fg=WHITE, font=(MONO, 13), width=10, relief="flat", insertbackground=WHITE).pack(side="left", padx=6, ipady=3)

        tk.Button(row, text="➕ DAR ENTRADA", bg=GREEN, fg="#000", font=(FONT, 11, "bold"), relief="flat", cursor="hand2", padx=16, pady=4, command=self._dar_entrada).pack(side="left", padx=12)
        tk.Button(row, text="✏️ AJUSTAR SALDO", bg=YELLOW, fg="#000", font=(FONT, 11, "bold"), relief="flat", cursor="hand2", padx=16, pady=4, command=self._ajustar_saldo).pack(side="left", padx=4)

        tk.Label(f, text="SALDO ATUAL", bg=BG, fg=TEXT, font=(FONT, 12, "bold")).pack(pady=(8, 4))
        espec = [("material", 200, "Material"), ("cor", 200, "Cor"), ("saldo", 200, "Saldo (kg)")]
        self.tree_est, _ = _criar_tabela(f, espec, altura=13)
        self.tree_est.pack(padx=40, pady=(0, 8))

        tk.Button(f, text="🔄 ATUALIZAR", bg=ACCENT, fg=TEXT, font=(FONT, 11, "bold"), relief="flat", cursor="hand2", padx=18, pady=4, command=self._refresh_estoque).pack(pady=6)

    def _on_material_change(self, event=None) -> None:
        if self.e_material.get() == "Marfim":
            self.cb_cor.config(values=["—"])
            self.e_cor.set("—")
        else:
            self.cb_cor.config(values=CORES)
            self.e_cor.set(CORES[0])

    def _ler_material_e_qtd(self, exigir_positivo: bool = True) -> tuple[str, str, float] | None:
        """Lê e valida material, cor e quantidade digitada nos campos da aba Estoque."""
        mat = self.e_material.get()
        cor = "" if mat == "Marfim" else self.e_cor.get()
        try:
            kg = float(self.e_qtd.get().replace(",", "."))
            if not math.isfinite(kg):
                raise ValueError("Valor inválido.")
            if exigir_positivo and kg <= 0:
                raise ValueError("Quantidade deve ser positiva.")
        except ValueError as exc:
            messagebox.showerror("Erro", str(exc) if exigir_positivo else "Valor inválido.")
            return None
        return mat, cor, kg

    def _dar_entrada(self) -> None:
        dados = self._ler_material_e_qtd(exigir_positivo=True)
        if not dados:
            return
        mat, cor, kg = dados
        try:
            novo = core.dar_entrada(mat, cor, kg)
        except ValueError as exc:
            messagebox.showerror("Erro", str(exc))
            return
        cor_txt = f" {cor}" if cor else ""
        messagebox.showinfo("OK", f"Entrada: +{kg:.1f} kg de {mat}{cor_txt}\nNovo saldo: {novo:.1f} kg")
        self._refresh_estoque()

    def _ajustar_saldo(self) -> None:
        dados = self._ler_material_e_qtd(exigir_positivo=False)
        if not dados:
            return
        mat, cor, kg = dados
        cor_txt = f" {cor}" if cor else ""
        if not messagebox.askyesno("Confirmar", f"Definir saldo de {mat}{cor_txt} para EXATAMENTE {kg:.1f} kg?"):
            return
        try:
            novo = core.ajustar_saldo(mat, cor, kg)
        except ValueError as exc:
            messagebox.showerror("Erro", str(exc))
            return
        messagebox.showinfo("OK", f"Saldo de {mat}{cor_txt} ajustado para {novo:.1f} kg")
        self._refresh_estoque()

    def _refresh_estoque(self) -> None:
        _limpar_tabela(self.tree_est)
        for mat, cor, saldo in core.get_todos_saldos():
            cor_txt = cor if cor else "—"
            tag = "neg" if saldo < 0 else ""
            self.tree_est.insert("", "end", values=(mat, cor_txt, f"{saldo:.1f}"), tags=(tag,))
        self.tree_est.tag_configure("neg", foreground=RED)

    # ── Aba Etiquetas ───────────────────────────────────────────────────────────

    def _build_etiquetas(self, f: tk.Frame) -> None:
        tk.Label(f, text="ETIQUETAS DE RECEITA", bg=BG, fg=GREEN, font=(FONT, 16, "bold")).pack(pady=(16, 4))
        tk.Label(f, text="Uma etiqueta por máquina × receita. Imprima, plastifique e pregue na estrutura.", bg=BG, fg=TEXT, font=(FONT, 11)).pack(pady=(0, 12))

        sel = tk.Frame(f, bg=BG2)
        sel.pack(fill="x", padx=30, pady=(0, 10))
        row = tk.Frame(sel, bg=BG2)
        row.pack(padx=16, pady=12)

        tk.Label(row, text="Gerar para:", bg=BG2, fg=TEXT, font=(FONT, 11)).pack(side="left")
        self.et_maq = tk.StringVar(value="Todas")
        vals = ["Todas"] + [MAQUINAS[k] for k in MAQUINAS]
        ttk.Combobox(row, textvariable=self.et_maq, state="readonly", width=16, values=vals).pack(side="left", padx=8)

        tk.Button(row, text="📄 EXPORTAR PDF", bg=GREEN, fg="#000", font=(FONT, 11, "bold"), relief="flat", cursor="hand2", padx=18, pady=5, command=self._export_pdf).pack(side="left", padx=8)
        tk.Button(row, text="🖨️ EXPORTAR ZPL", bg=YELLOW, fg="#000", font=(FONT, 11, "bold"), relief="flat", cursor="hand2", padx=18, pady=5, command=self._export_zpl).pack(side="left", padx=4)

        tk.Label(f, text="CÓDIGOS", bg=BG, fg=TEXT, font=(FONT, 12, "bold")).pack(pady=(8, 4))
        espec = [("codigo", 120, "Código"), ("maquina", 130, "Máquina"), ("receita", 220, "Receita"), ("cor", 130, "Cor"), ("total", 120, "Total kg/bip")]
        self.tree_cod, sc = _criar_tabela(f, espec, altura=15, com_scroll=True)
        self.tree_cod.pack(side="left", fill="both", expand=True, padx=(40, 0), pady=(0, 12))
        sc.pack(side="right", fill="y", padx=(0, 40), pady=(0, 12))

        self._refresh_codigos()

    def _refresh_codigos(self) -> None:
        _limpar_tabela(self.tree_cod)
        for codigo, maq, receita, cor, total in core.listar_codigos():
            self.tree_cod.insert("", "end", values=(codigo, maq, receita, cor, f"{total:.1f}"))

    def _maq_cod_selecionada(self) -> str | None:
        sel = self.et_maq.get()
        if sel == "Todas":
            return None
        for cod, nome in MAQUINAS.items():
            if nome == sel:
                return cod
        return None

    def _export_pdf(self) -> None:
        fp = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], title="Salvar PDF", initialfile="VTC_Etiquetas_Receitas.pdf")
        if not fp:
            return
        try:
            core.gerar_pdf_etiquetas(fp, self._maq_cod_selecionada())
            messagebox.showinfo("OK", f"PDF salvo:\n{fp}")
            _abrir_arquivo(fp)
        except ImportError:
            messagebox.showerror("Erro", "Instale reportlab:\npip install reportlab")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def _export_zpl(self) -> None:
        fp = filedialog.asksaveasfilename(defaultextension=".zpl", filetypes=[("ZPL", "*.zpl")], title="Salvar ZPL", initialfile="VTC_Etiquetas_Receitas.zpl")
        if not fp:
            return
        try:
            core.gerar_zpl_etiquetas(fp, self._maq_cod_selecionada())
            messagebox.showinfo("OK", f"ZPL salvo:\n{fp}\n\nAbra no Zebra Designer.")
            _abrir_arquivo(fp)
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    # ── Aba Histórico ───────────────────────────────────────────────────────────

    def _build_historico(self, f: tk.Frame) -> None:
        bar = tk.Frame(f, bg=BG)
        bar.pack(fill="x", padx=20, pady=(12, 4))
        tk.Label(bar, text="Máquina:", bg=BG, fg=TEXT, font=(FONT, 10)).pack(side="left")
        self.h_maq = tk.StringVar(value="Todas")
        vals = ["Todas"] + [MAQUINAS[k] for k in MAQUINAS]
        ttk.Combobox(bar, textvariable=self.h_maq, state="readonly", width=14, values=vals).pack(side="left", padx=4)

        tk.Label(bar, text="Data:", bg=BG, fg=TEXT, font=(FONT, 10)).pack(side="left", padx=(12, 0))
        self.h_data = tk.StringVar(value=datetime.datetime.now().strftime("%Y-%m-%d"))
        tk.Entry(bar, textvariable=self.h_data, bg=BG2, fg=WHITE, font=(MONO, 11), width=12, relief="flat", insertbackground=WHITE).pack(side="left", padx=4, ipady=2)

        tk.Button(bar, text="🔍 BUSCAR", bg=GREEN, fg="#000", font=(FONT, 10, "bold"), relief="flat", cursor="hand2", padx=12, command=self._buscar_hist).pack(side="left", padx=8)
        tk.Button(bar, text="📊 EXPORTAR CSV", bg=ACCENT, fg=TEXT, font=(FONT, 10, "bold"), relief="flat", cursor="hand2", padx=12, command=self._export_csv).pack(side="left", padx=4)

        espec = [
            ("id", 40, "ID"), ("data", 125, "Data/Hora"), ("maq", 80, "Máquina"),
            ("receita", 150, "Receita"), ("cor", 90, "Cor"), ("marfim", 60, "Marf"),
            ("moido", 55, "Moído"), ("pig", 55, "Pig"), ("total", 60, "Total"),
            ("op", 80, "Oper"), ("turno", 70, "Turno"),
        ]
        self.tree_h, sc = _criar_tabela(f, espec, altura=24, com_scroll=True)
        self.tree_h.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=(4, 12))
        sc.pack(side="right", fill="y", padx=(0, 20), pady=(4, 12))

    def _maq_hist(self) -> str | None:
        sel = self.h_maq.get()
        return None if sel == "Todas" else sel

    def _buscar_hist(self) -> None:
        _limpar_tabela(self.tree_h)
        rows = core.buscar_producao(maquina=self._maq_hist(), data=self.h_data.get().strip() or None)
        for r in rows:
            self.tree_h.insert("", "end", values=(
                r[0], r[1], r[2], r[3], r[4] or "—",
                f"{r[5]:.1f}", f"{r[6]:.1f}", f"{r[7]:.1f}", f"{r[8]:.1f}", r[9], r[10],
            ))

    def _export_csv(self) -> None:
        rows = core.buscar_producao(maquina=self._maq_hist(), data=self.h_data.get().strip() or None, limite=50000)
        if not rows:
            messagebox.showwarning("Aviso", "Sem dados.")
            return
        fp = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not fp:
            return
        with open(fp, "w", newline="", encoding="utf-8-sig") as file:
            w = csv.writer(file, delimiter=";")
            w.writerow(["ID", "Data/Hora", "Máquina", "Receita", "Cor", "Marfim kg", "Moído kg", "Pigmento kg", "Total kg", "Operador", "Turno"])
            w.writerows(rows)
        messagebox.showinfo("OK", f"Exportado:\n{fp}")
        _abrir_arquivo(fp)

    # ── Aba Resumo ──────────────────────────────────────────────────────────────

    def _build_resumo(self, f: tk.Frame) -> None:
        tk.Label(f, text="RESUMO DO DIA", bg=BG, fg=GREEN, font=(FONT, 18, "bold")).pack(pady=(18, 2))
        self.lbl_data_resumo = tk.Label(f, text=datetime.datetime.now().strftime("%d/%m/%Y"), bg=BG, fg=TEXT, font=(FONT, 13))
        self.lbl_data_resumo.pack(pady=(0, 12))

        cards = tk.Frame(f, bg=BG)
        cards.pack(fill="x", padx=40, pady=6)
        self.card_marfim = self._card(cards, "MARFIM", BLUE)
        self.card_moido = self._card(cards, "MOÍDO", GREEN)
        self.card_pig = self._card(cards, "PIGMENTO", YELLOW)
        self.card_tot = self._card(cards, "TOTAL", WHITE)
        for card in (self.card_marfim, self.card_moido, self.card_pig, self.card_tot):
            card.pack(side="left", fill="both", expand=True, padx=4)

        tk.Label(f, text="PRODUÇÃO POR MÁQUINA", bg=BG, fg=TEXT, font=(FONT, 12, "bold")).pack(pady=(16, 4))
        espec = [("maq", 140, "Máquina"), ("bips", 90, "Bips"), ("marfim", 110, "Marfim kg"), ("moido", 110, "Moído kg"), ("pig", 110, "Pigmento kg"), ("total", 120, "Total kg")]
        self.tree_res, _ = _criar_tabela(f, espec, altura=8)
        self.tree_res.pack(padx=40, pady=(0, 8))

        tk.Button(f, text="🔄 ATUALIZAR", bg=GREEN, fg="#000", font=(FONT, 12, "bold"), relief="flat", cursor="hand2", padx=20, pady=4, command=self._refresh_resumo).pack(pady=8)

    def _card(self, parent: tk.Frame, titulo: str, cor: str) -> tk.Frame:
        c = tk.Frame(parent, bg=BG2)
        tk.Label(c, text=titulo, bg=BG2, fg=cor, font=(FONT, 13, "bold")).pack(pady=(16, 4))
        lbl_kg = tk.Label(c, text="0.0", bg=BG2, fg=WHITE, font=(FONT, 32, "bold"))
        lbl_kg.pack()
        tk.Label(c, text="kg hoje", bg=BG2, fg=TEXT, font=(FONT, 10)).pack(pady=(0, 16))
        c._kg = lbl_kg
        return c

    def _refresh_resumo(self) -> None:
        if hasattr(self, "lbl_data_resumo"):
            self.lbl_data_resumo.config(text=datetime.datetime.now().strftime("%d/%m/%Y"))
        por_maq, tot = core.resumo_dia()
        _limpar_tabela(self.tree_res)
        for maq, bips, total, marfim, moido, pig in por_maq:
            self.tree_res.insert("", "end", values=(maq, bips, f"{marfim:.1f}", f"{moido:.1f}", f"{pig:.1f}", f"{total:.1f}"))

        n, total, marfim, moido, pig = tot
        self.card_marfim._kg.config(text=f"{marfim:.0f}")
        self.card_moido._kg.config(text=f"{moido:.0f}")
        self.card_pig._kg.config(text=f"{pig:.1f}")
        self.card_tot._kg.config(text=f"{total:.0f}")

        self.ft_bips.config(text=f"Bips hoje: {n}")
        self.ft_marfim.config(text=f"Marfim: {marfim:.0f} kg")
        self.ft_moido.config(text=f"Moído: {moido:.0f} kg")
        self.ft_pig.config(text=f"Pigmento: {pig:.1f} kg")
        self.ft_total.config(text=f"TOTAL: {total:.0f} kg")

    # ── Captura Tkinter (fallback quando hook global está inativo) ──────────────

    def _on_key_tk(self, event) -> None:
        if self.listener.hook_ativo or isinstance(self.root.focus_get(), tk.Entry):
            return
        ch = _char_valido(event.char)
        if ch:
            self.buf_tk += ch
            if self.buf_timer:
                self.root.after_cancel(self.buf_timer)
            self.buf_timer = self.root.after(500, lambda: setattr(self, "buf_tk", ""))

    def _on_enter_tk(self, event) -> None:
        if self.listener.hook_ativo or isinstance(self.root.focus_get(), tk.Entry):
            return
        if self.buf_tk:
            self._processar(self.buf_tk)
        self.buf_tk = ""

    # ── Processamento do bip ────────────────────────────────────────────────────

    def _processar(self, codigo: str) -> None:
        info = core.decodificar(codigo)
        if not info:
            self.lbl_status.config(text=f"✖ Código inválido: {codigo}", fg=RED)
            self.root.after(4000, lambda: self.lbl_status.config(text="●  AGUARDANDO BIP", fg=YELLOW))
            _tocar_bip(400, 400)
            return

        res = core.registrar_producao(info, operador=self.operador.get())

        self.d_maq.config(text=f"  {info['maquina']}  ")
        self.d_receita.config(text=info["receita"], fg=WHITE)
        self.d_cor.config(text=info["cor"])
        self.d_codigo.config(text=info["codigo"])
        self.d_marfim.config(text=f"Marfim\n{info['marfim_kg']:.1f} kg")
        self.d_moido.config(text=f"Moído\n{info['moido_kg']:.1f} kg")
        self.d_pigmento.config(text=f"Pigmento\n{info['pigmento_kg']:.1f} kg")
        self.d_total.config(text=f"{info['total_kg']:.1f} kg")
        self.d_bips.config(text=f"Bip #{res['bips']} — {info['maquina']} {info['receita']} {info['cor']}")
        self.d_aviso.config(text=("⚠️ " + " | ".join(res["avisos"])) if res["avisos"] else "")

        self.lbl_status.config(text="●  RECEITA OK", fg=GREEN)
        self.root.after(3000, lambda: self.lbl_status.config(text="●  AGUARDANDO BIP", fg=YELLOW))

        hora = datetime.datetime.now().strftime("%H:%M:%S")
        self.tree_rec.insert("", 0, values=(hora, info["maquina_cod"], info["receita"], info["cor"] or "—", f"{info['total_kg']:.1f}"))
        ch = self.tree_rec.get_children()
        if len(ch) > 50:
            self.tree_rec.delete(ch[-1])

        self._refresh_resumo()
        self._refresh_estoque()
        _tocar_bip(1000, 120)


if __name__ == "__main__":
    core.init_db()
    root = tk.Tk()
    app = App(root)
    root.mainloop()
