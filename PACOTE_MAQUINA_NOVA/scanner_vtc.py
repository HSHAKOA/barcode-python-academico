"""Captura de códigos de barras em segundo plano via hook global de teclado."""

import queue
import threading
import time


def _char_valido(ch: str | None) -> str | None:
    """Normaliza caractere aceito em códigos (A-Z, 0-9, '-', '_', '.'), ou retorna None."""
    if ch and (ch.isalnum() or ch in "-_."):
        return ch.upper()
    return None


class ScannerListener:
    """Escuta teclas globais em thread separada e envia leituras rápidas para a GUI."""

    def __init__(self, fila_gui: queue.Queue, max_scan: float = 0.8, idle: float = 1.5):
        self.buffer = ""
        self.first_key = 0.0
        self.last_key = 0.0
        self.fila = fila_gui
        self.ativo = True
        self.hook_ativo = False
        self.MAX_SCAN = max_scan
        self.IDLE = idle

    def start(self) -> None:
        """Inicia a thread daemon responsável pelo hook de teclado."""
        threading.Thread(target=self._run, daemon=True).start()

    def _processar_tecla(self, name: str, agora: float) -> None:
        """Acumula caracteres no buffer e envia o código se concluído dentro da janela de leitor."""
        if self.buffer and (agora - self.last_key > self.IDLE):
            self.buffer = ""

        if name == "enter":
            if self.buffer and (agora - self.first_key < self.MAX_SCAN):
                self.fila.put(self.buffer)
            self.buffer = ""
            return

        ch_raw = "-" if name == "minus" else (name if len(name) == 1 else None)
        ch = _char_valido(ch_raw) if ch_raw else None
        if ch is None:
            return

        if not self.buffer:
            self.first_key = agora
        self.buffer += ch
        self.last_key = agora

    def _run(self) -> None:
        try:
            import keyboard as kb

            def on_key(event):
                if self.ativo and event.event_type == "down":
                    self._processar_tecla(event.name, time.time())

            kb.hook(on_key)
            self.hook_ativo = True
            while self.ativo:
                time.sleep(0.1)
        except ImportError:
            self.hook_ativo = False
            print("[AVISO] 'keyboard' não instalado — segundo plano OFF (pip install keyboard)")
        except Exception as exc:
            self.hook_ativo = False
            print(f"[ERRO] scanner: {exc}")

    def stop(self) -> None:
        """Encerra a escuta e remove os hooks globais registrados."""
        self.ativo = False
        self.hook_ativo = False
        try:
            import keyboard as kb
            kb.unhook_all()
        except Exception:
            pass
