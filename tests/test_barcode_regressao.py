"""
Testes automatizados e de regressão do Sistema Barcode VTC (versão acadêmica).
Executa exclusivamente em diretório temporário com dados fictícios.

Uso:
    python -B -m unittest discover -s tests -v
"""

import importlib
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
import unittest
import urllib.error
import urllib.request

PKG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "PACOTE_MAQUINA_NOVA"))
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)

import config_receitas  # noqa: E402
import core_vtc as core  # noqa: E402
import exportador_csv as exp  # noqa: E402
import barcode_vtc as gui_mod  # noqa: E402


class BarcodeTestBase(unittest.TestCase):
    """Isola DB_PATH e PASTA_DADOS em pasta temporária a cada teste."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="vtc_acad_test_")
        self._orig_core_db = core.DB_PATH
        self._orig_exp_db = exp.DB_PATH
        self._orig_exp_dir = exp.PASTA_DADOS

        self.db_path = os.path.join(self.tmp, "barcode_vtc.db")
        core.DB_PATH = self.db_path
        exp.DB_PATH = self.db_path
        exp.PASTA_DADOS = os.path.join(self.tmp, "dados_powerquery")
        core.init_db()

    def tearDown(self):
        core.DB_PATH = self._orig_core_db
        exp.DB_PATH = self._orig_exp_db
        exp.PASTA_DADOS = self._orig_exp_dir
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestCoreFluxos(BarcodeTestBase):
    def test_init_db_cria_estrutura_wal_e_materiais(self):
        conn = sqlite3.connect(self.db_path)
        try:
            jm = conn.execute("PRAGMA journal_mode").fetchone()[0]
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            conn.close()
        self.assertEqual(jm.lower(), "wal")
        self.assertTrue({"producao", "estoque", "mov_estoque"}.issubset(tables))
        self.assertEqual(len(core.get_todos_saldos()), 9)

    def test_decodificar_validos_e_calculo_quantidades(self):
        info = core.decodificar("  m2-pig-cc ")
        self.assertIsNotNone(info)
        self.assertEqual(info["codigo"], "M2-PIG-CC")
        self.assertEqual(info["maquina"], "Máquina 2")
        self.assertEqual(info["cor"], "Cinza Claro")
        self.assertEqual(info["marfim_kg"], 20.0)
        self.assertEqual(info["moido_kg"], 0.0)
        self.assertEqual(info["pigmento_kg"], 0.5)
        self.assertAlmostEqual(info["total_kg"], 20.5)

        info_moi = core.decodificar("M4-MOI-AZ")
        self.assertAlmostEqual(info_moi["total_kg"], 30.5)

    def test_decodificar_invalidos(self):
        for cod in ("", "   ", "M2", "M9-PURO", "M1-NAOEXISTE", "PURO", "M1-PURO-X", None):
            with self.subTest(cod=cod):
                self.assertIsNone(core.decodificar(cod))

    def test_listar_codigos_associacao_maquina_receita(self):
        todos = core.listar_codigos()
        self.assertEqual(len(todos), len(config_receitas.MAQUINAS) * len(config_receitas.RECEITAS))
        m2 = core.listar_codigos("M2")
        self.assertEqual(len(m2), len(config_receitas.RECEITAS))

    def test_producao_desconto_e_aviso_negativo(self):
        saldo_m = core.dar_entrada("Marfim", "", 30.0, "NF-Teste")
        self.assertAlmostEqual(saldo_m, 30.0)
        core.dar_entrada("Pigmento", "Cinza Claro", 0.4, "NF-Teste")

        res1 = core.registrar_producao(core.decodificar("M2-PIG-CC"), operador="Op1")
        self.assertEqual(res1["bips"], 1)
        self.assertEqual(res1["avisos"], ["Pigmento Cinza Claro NEGATIVO: -0.1 kg"])
        self.assertAlmostEqual(core.get_saldo("Marfim", ""), 10.0)
        self.assertAlmostEqual(core.get_saldo("Pigmento", "Cinza Claro"), -0.1)

        res2 = core.registrar_producao(core.decodificar("M2-PIG-CC"), operador="Op1")
        self.assertEqual(res2["bips"], 2)
        self.assertTrue(any("Marfim NEGATIVO" in a for a in res2["avisos"]))
        self.assertAlmostEqual(core.get_saldo("Marfim", ""), -10.0)

    def test_ajustar_saldo_e_rollback_transacional(self):
        novo = core.ajustar_saldo("Marfim", "", 100.0)
        self.assertAlmostEqual(novo, 100.0)
        antes_prod = len(core.buscar_producao(limite=100))

        with self.assertRaises(RuntimeError):
            with core._db(escrita=True) as conn:
                conn.execute(
                    "INSERT INTO producao (codigo, maquina, receita, data_hora) VALUES ('X', 'M1', 'R', '2026-11-18 09:00:00')"
                )
                conn.execute("UPDATE estoque SET saldo_kg = -999 WHERE material='Marfim' AND cor=''")
                raise RuntimeError("Erro simulado")

        self.assertEqual(len(core.buscar_producao(limite=100)), antes_prod)
        self.assertAlmostEqual(core.get_saldo("Marfim", ""), 100.0)

    def test_consultas_historico_e_resumo_dia(self):
        core.registrar_producao(core.decodificar("M1-PURO"), operador="OpA")
        core.registrar_producao(core.decodificar("M2-PIG-CC"), operador="OpB")

        hoje = core.datetime.datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(len(core.buscar_producao(maquina="Todas", data=hoje)), 2)
        self.assertEqual(len(core.buscar_producao(maquina="Máquina 1", data=hoje)), 1)
        self.assertEqual(len(core.buscar_producao(maquina="Máquina 3", data=hoje)), 0)

        por_maq, totais = core.resumo_dia()
        self.assertEqual(len(por_maq), 2)
        self.assertEqual(totais[0], 2)
        self.assertAlmostEqual(totais[1], 40.5)

    def test_validacao_entradas_invalidas_e_nan(self):
        for ruim in (0, -5.0, float("nan"), float("inf"), float("-inf")):
            with self.subTest(kg=ruim):
                with self.assertRaises(ValueError):
                    core.dar_entrada("Marfim", "", ruim)
        for ruim in (float("nan"), float("inf")):
            with self.subTest(ajuste=ruim):
                with self.assertRaises(ValueError):
                    core.ajustar_saldo("Marfim", "", ruim)
        with self.assertRaises(ValueError):
            core.dar_entrada("MaterialInexistente", "", 10.0)
        with self.assertRaises(ValueError):
            core.dar_entrada("Marfim", "Preto", 10.0)

    def test_etiquetas_zpl_e_exportador_csv(self):
        zpl_path = os.path.join(self.tmp, "etiquetas.zpl")
        core.gerar_zpl_etiquetas(zpl_path, maquina_cod="M1")
        with open(zpl_path, "r", encoding="utf-8") as fh:
            zpl = fh.read()
        self.assertEqual(zpl.count("^XA"), 9)
        self.assertEqual(zpl.count("^XZ"), 9)
        self.assertIn("^CI28", zpl)

        core.registrar_producao(core.decodificar("M1-PURO"), operador="OpCSV")
        stats = exp.exportar_tudo()
        self.assertEqual(stats["producao"], 1)
        self.assertEqual(stats["estoque"], 9)
        gerados = sorted(os.listdir(exp.PASTA_DADOS))
        self.assertEqual(len(gerados), 7)
        self.assertFalse(any(fn.endswith(".tmp") for fn in gerados))

        # Limite negativo não deve quebrar nem ignorar teto
        self.assertEqual(len(core.buscar_producao(limite=-1)), 1)

    def test_concorrencia_dar_entrada_e_registrar_producao(self):
        # 10 threads x 10 entradas de 10 kg = 1000 kg esperados
        barrier = threading.Barrier(10)
        erros = []

        def w_entrada():
            barrier.wait()
            for _ in range(10):
                try:
                    core.dar_entrada("Marfim", "", 10.0, "Conc")
                except Exception as exc:
                    erros.append(exc)

        ts = [threading.Thread(target=w_entrada) for _ in range(10)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()

        self.assertEqual(erros, [])
        self.assertAlmostEqual(core.get_saldo("Marfim", ""), 1000.0)

        # 10 threads x 2 producoes M1-PURO = -400 kg -> saldo esperado 600.0 kg
        info = core.decodificar("M1-PURO")
        barrier2 = threading.Barrier(10)

        def w_prod():
            barrier2.wait()
            for _ in range(2):
                try:
                    core.registrar_producao(info, operador="Conc")
                except Exception as exc:
                    erros.append(exc)

        ts2 = [threading.Thread(target=w_prod) for _ in range(10)]
        for t in ts2:
            t.start()
        for t in ts2:
            t.join()

        self.assertEqual(erros, [])
        self.assertAlmostEqual(core.get_saldo("Marfim", ""), 600.0)


class TestGuiDeduplicacao(BarcodeTestBase):
    def test_fallback_tk_inativo_quando_hook_global_ativo(self):
        root = tk.Tk()
        root.withdraw()
        try:
            app = gui_mod.App(root)
            chamadas = []
            app._processar = lambda cod: chamadas.append(cod)

            # Simula hook global ativo + chegada via fila + eventos Tk simultâneos
            app.listener.hook_ativo = True
            app.fila.put("M2-PIG-CC")
            for ch in "M2-PIG-CC":
                app._on_key_tk(type("Ev", (), {"char": ch})())
            app._on_enter_tk(type("Ev", (), {})())
            while not app.fila.empty():
                app._processar(app.fila.get_nowait())

            self.assertEqual(chamadas, ["M2-PIG-CC"])

            # Simula hook global inativo -> fallback Tk deve funcionar e rótulo refletir estado
            chamadas.clear()
            app.listener.hook_ativo = False
            app._poll()
            self.assertIn("MODO JANELA", app.lbl_bg.cget("text"))
            for ch in "M1-PURO":
                app._on_key_tk(type("Ev", (), {"char": ch})())
            app._on_enter_tk(type("Ev", (), {})())
            self.assertEqual(chamadas, ["M1-PURO"])
        finally:
            app.listener.stop()
            root.update()
            root.destroy()


@unittest.skipUnless(
    importlib.util.find_spec("fastapi") is not None and importlib.util.find_spec("uvicorn") is not None,
    "fastapi/uvicorn não instalados no ambiente",
)
class TestApiOpcional(BarcodeTestBase):
    def _iniciar_uvicorn(self, workdir, api_key=None):
        for fn in os.listdir(PKG_DIR):
            if fn.endswith(".py"):
                shutil.copy2(os.path.join(PKG_DIR, fn), os.path.join(workdir, fn))
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()

        env = os.environ.copy()
        env["PYTHONPATH"] = workdir
        if api_key is None:
            env.pop("VTC_API_KEY", None)
        else:
            env["VTC_API_KEY"] = api_key

        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api_vtc:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=workdir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        base = f"http://127.0.0.1:{port}"
        for _ in range(40):
            try:
                with urllib.request.urlopen(f"{base}/health", timeout=1) as resp:
                    if resp.status == 200:
                        return proc, base
            except Exception:
                time.sleep(0.15)
        proc.terminate()
        raise RuntimeError("Uvicorn não respondeu a tempo no teste")

    def _req(self, url, method="GET", body=None, headers=None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        hdrs = dict(headers or {})
        if data is not None:
            hdrs["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            try:
                return err.code, json.loads(err.read().decode("utf-8"))
            finally:
                err.close()

    def _parar_uvicorn(self, proc):
        proc.terminate()
        proc.wait(timeout=5)
        if proc.stdout:
            proc.stdout.close()
        if proc.stderr:
            proc.stderr.close()

    def test_api_bloqueia_sem_chave_e_recusa_chave_padrao(self):
        # 1. Sem VTC_API_KEY: /health responde, rotas protegidas recusam inclusive a chave padrão
        proc, base = self._iniciar_uvicorn(self.tmp, api_key=None)
        try:
            st, data = self._req(f"{base}/health")
            self.assertEqual(st, 200)
            self.assertFalse(data["api_configurada"])
            st_padrao, _ = self._req(f"{base}/producao", headers={"X-API-Key": "vtc-troque-esta-chave"})
            self.assertEqual(st_padrao, 503)
            st_post, _ = self._req(
                f"{base}/producao",
                method="POST",
                body={"codigo": "M1-PURO"},
                headers={"X-API-Key": "vtc-troque-esta-chave"},
            )
            self.assertEqual(st_post, 503)
        finally:
            self._parar_uvicorn(proc)

    def test_api_autenticacao_e_validacao_com_uvicorn(self):
        # 2. Com VTC_API_KEY segura: recusa sem chave/chave padrão; aceita válida e valida entradas
        chave = "chave-academica-validacao-2026"
        proc, base = self._iniciar_uvicorn(self.tmp, api_key=chave)
        try:
            st_sem, _ = self._req(f"{base}/producao")
            self.assertEqual(st_sem, 401)
            st_padrao, _ = self._req(f"{base}/estoque", headers={"X-API-Key": "vtc-troque-esta-chave"})
            self.assertEqual(st_padrao, 401)

            hdr = {"X-API-Key": chave}
            st_est, est = self._req(f"{base}/estoque", headers=hdr)
            self.assertEqual(st_est, 200)
            self.assertEqual(len(est), 9)

            st_ent_bad, _ = self._req(
                f"{base}/estoque/entrada",
                method="POST",
                body={"material": "Invalido", "cor": "", "kg": 10},
                headers=hdr,
            )
            self.assertEqual(st_ent_bad, 400)

            st_ent_ok, ent_ok = self._req(
                f"{base}/estoque/entrada",
                method="POST",
                body={"material": "Marfim", "cor": "", "kg": 30.0, "origem": "TesteAPI"},
                headers=hdr,
            )
            self.assertEqual(st_ent_ok, 200)
            self.assertAlmostEqual(ent_ok["saldo_kg"], 30.0)

            st_prod_bad, _ = self._req(
                f"{base}/producao",
                method="POST",
                body={"codigo": "M9-INEXISTENTE", "operador": "ApiTest"},
                headers=hdr,
            )
            self.assertEqual(st_prod_bad, 400)

            st_prod_ok, prod_ok = self._req(
                f"{base}/producao",
                method="POST",
                body={"codigo": "M2-PIG-CC", "operador": "ApiTest"},
                headers=hdr,
            )
            self.assertEqual(st_prod_ok, 200)
            self.assertEqual(prod_ok["bips"], 1)
        finally:
            self._parar_uvicorn(proc)


@unittest.skipUnless(
    all(importlib.util.find_spec(m) is not None for m in ("reportlab", "openpyxl", "keyboard")),
    "reportlab/openpyxl/keyboard não instalados no ambiente",
)
class TestRecursosExtrasInstalados(BarcodeTestBase):
    def test_pdf_reportlab_e_xlsx_openpyxl(self):
        import openpyxl
        import criar_planilha_pq as pq

        pdf_path = os.path.join(self.tmp, "etiquetas_m1.pdf")
        core.gerar_pdf_etiquetas(pdf_path, maquina_cod="M1")
        self.assertTrue(os.path.exists(pdf_path))
        with open(pdf_path, "rb") as fh:
            self.assertTrue(fh.read(5).startswith(b"%PDF-"))

        orig_xlsx = pq.EXCEL_PQ
        orig_pasta = pq.PASTA_DADOS
        pq.EXCEL_PQ = os.path.join(self.tmp, "RELATORIO_VTC_PQ.xlsx")
        pq.PASTA_DADOS = os.path.join(self.tmp, "dados_powerquery")
        try:
            gerado = pq.criar_planilha()
            wb = openpyxl.load_workbook(gerado)
            self.assertIn("Dashboard", wb.sheetnames)
            self.assertEqual(len(wb.sheetnames), 8)
            wb.close()
        finally:
            pq.EXCEL_PQ = orig_xlsx
            pq.PASTA_DADOS = orig_pasta

    def test_keyboard_hook_ativo_uma_leitura_um_apontamento(self):
        root = tk.Tk()
        root.withdraw()
        app = gui_mod.App(root)
        try:
            # Aguarda thread do listener registrar o hook real do pacote keyboard
            for _ in range(20):
                if app.listener.hook_ativo:
                    break
                time.sleep(0.05)
            self.assertTrue(app.listener.hook_ativo)

            core.dar_entrada("Marfim", "", 50.0, "TesteHook")
            # Simula chegada do código via fila (hook) + teclas simultâneas no Tkinter
            app.fila.put("M1-PURO")
            for ch in "M1-PURO":
                app._on_key_tk(type("Ev", (), {"char": ch})())
            app._on_enter_tk(type("Ev", (), {})())
            app._poll()

            # Deve existir exatamente 1 apontamento e apenas 1 desconto de 20 kg
            self.assertEqual(len(core.buscar_producao(limite=10)), 1)
            self.assertAlmostEqual(core.get_saldo("Marfim", ""), 30.0)
        finally:
            app._on_close()


class TestScriptsWindowsERequisitos(unittest.TestCase):
    """Verifica integridade, portabilidade e segurança estática dos scripts Windows."""

    SCRIPTS = [
        "INICIAR_VTC_BARCODE.bat",
        "INICIAR_EXPORTADOR_CSV.bat",
        "INICIAR_API_VTC.bat",
        "VERIFICAR_DADOS.bat",
        "CONFIGURAR_INICIO_AUTOMATICO.bat",
        "REMOVER_INICIO_AUTOMATICO.bat",
        "CONFIGURAR_INICIO_AUTOMATICO_API.bat",
        "INICIAR_API_VTC_SEGUNDO_PLANO.vbs",
        "PARAR_API_VTC.bat",
        "REMOVER_INICIO_AUTOMATICO_API.bat",
        "_api_vtc_bg.bat",
    ]

    def test_todos_scripts_presentes_e_portaveis(self):
        for nome in self.SCRIPTS:
            caminho = os.path.join(PKG_DIR, nome)
            self.assertTrue(os.path.exists(caminho), f"Script ausente: {nome}")
            with open(caminho, "r", encoding="utf-8", errors="replace") as fh:
                conteudo = fh.read()
            self.assertNotIn("OneDrive", conteudo)
            self.assertNotIn("joao.passos", conteudo.lower())

        # Confirma que os scripts da API não sobem em 0.0.0.0 nem alteram powercfg por padrão
        for api_bat in ("INICIAR_API_VTC.bat", "_api_vtc_bg.bat"):
            with open(os.path.join(PKG_DIR, api_bat), "r", encoding="utf-8") as fh:
                linhas_ativas = [
                    ln.strip().lower()
                    for ln in fh
                    if ln.strip() and not ln.strip().lower().startswith("rem ")
                ]
            self.assertFalse(any("--host 0.0.0.0" in ln for ln in linhas_ativas), api_bat)
            self.assertFalse(any("powercfg" in ln for ln in linhas_ativas), api_bat)

        # Confirma vínculos entre scripts e suporte a .venv / python -m pip
        with open(os.path.join(PKG_DIR, "INICIAR_API_VTC_SEGUNDO_PLANO.vbs"), "r", encoding="utf-8") as fh:
            self.assertIn("_api_vtc_bg.bat", fh.read())

        for bat_py in (
            "INICIAR_VTC_BARCODE.bat",
            "INICIAR_EXPORTADOR_CSV.bat",
            "INICIAR_API_VTC.bat",
            "VERIFICAR_DADOS.bat",
            "_api_vtc_bg.bat",
        ):
            with open(os.path.join(PKG_DIR, bat_py), "r", encoding="utf-8") as fh:
                txt = fh.read()
            self.assertIn(".venv\\Scripts\\python.exe", txt, bat_py)
            self.assertIn("chcp 65001", txt, bat_py)

    def test_requirements_txt_contem_pacotes_esperados(self):
        req = os.path.join(PKG_DIR, "requirements.txt")
        with open(req, "r", encoding="utf-8") as fh:
            itens = [ln.strip() for ln in fh if ln.strip() and not ln.strip().startswith("#")]
        self.assertEqual(itens, ["keyboard", "reportlab", "openpyxl", "fastapi", "uvicorn"])


class TestRefatoracaoV4ModulosENavegacao(BarcodeTestBase):
    """Testes adicionais de desacoplamento (scanner_vtc, etiquetas_vtc), GUI e verificar_dados."""

    def test_scanner_listener_desacoplado_e_janela_temporal(self):
        import queue
        import scanner_vtc

        fila = queue.Queue()
        sl = scanner_vtc.ScannerListener(fila, max_scan=0.8, idle=1.5)

        # Leitura rápida de leitor (<= 0.8s) deve enfileirar código normalizado
        t = 100.0
        for tecla in ("m", "2", "minus", "p", "i", "g", "minus", "c", "c"):
            sl._processar_tecla(tecla, t)
            t += 0.02
        sl._processar_tecla("enter", t)
        self.assertEqual(fila.get_nowait(), "M2-PIG-CC")

        # Digitação lenta (> 0.8s) deve ser descartada ao pressionar enter
        t = 200.0
        for tecla in ("m", "1", "minus", "p", "u", "r", "o"):
            sl._processar_tecla(tecla, t)
            t += 0.25
        sl._processar_tecla("enter", t)
        self.assertTrue(fila.empty())

        # Reexportação em barcode_vtc preservada
        self.assertIs(gui_mod.ScannerListener, scanner_vtc.ScannerListener)

    def test_etiquetas_vtc_e_arredondamento_csv(self):
        import etiquetas_vtc
        import verificar_dados as vd
        from unittest import mock

        self.assertIs(core.listar_codigos, etiquetas_vtc.listar_codigos)
        self.assertIs(core.gerar_zpl_etiquetas, etiquetas_vtc.gerar_zpl_etiquetas)

        core.dar_entrada("Marfim", "", 40.0, "TesteV4")
        core.dar_entrada("Pigmento", "Cinza Claro", 0.8, "TesteV4")
        core.registrar_producao(core.decodificar("M2-PIG-CC"), operador="OpV4")
        core.registrar_producao(core.decodificar("M2-PIG-CC"), operador="OpV4")
        exp.exportar_tudo()

        with open(os.path.join(exp.PASTA_DADOS, "estoque.csv"), "r", encoding="utf-8-sig") as fh:
            conteudo = fh.read()
        self.assertIn("Pigmento;Cinza Claro;-0.2;NEGATIVO", conteudo)

        orig_vd_db = vd.DB_PATH
        vd.DB_PATH = self.db_path
        try:
            with mock.patch("builtins.input", return_value=""), mock.patch("builtins.print") as p:
                vd.main()
            self.assertTrue(p.called)
        finally:
            vd.DB_PATH = orig_vd_db

    def test_gui_cinco_abas_navegacao_e_processamento(self):
        from tkinter import ttk

        root = tk.Tk()
        root.withdraw()
        app = gui_mod.App(root)
        try:
            nb = [w for w in root.winfo_children() if isinstance(w, ttk.Notebook)][0]
            self.assertEqual(len(nb.tabs()), 5)
            for idx in range(len(nb.tabs())):
                nb.select(idx)
                root.update()

            core.dar_entrada("Marfim", "", 30.0, "GuiV4")
            app.operador.set("Aluno V4")
            app._processar("M2-PIG-CC")
            app._buscar_hist()
            self.assertEqual(len(app.tree_h.get_children()), 1)
            self.assertIn("Bip #1", app.d_bips.cget("text"))
        finally:
            app._on_close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
