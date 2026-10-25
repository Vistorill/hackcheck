"""Geração guiada da EFI com o OpCore Simplify (lzhoang2801, BSD-3).

O OpCore Simplify é interativo (menus no console), então o HackCheck baixa a
ferramenta, abre a janela dela e acompanha a pasta Results/EFI até a EFI ficar pronta.
"""
import io
import os
import shutil
import subprocess
import threading
import time
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

ZIP_URL = "https://github.com/lzhoang2801/OpCore-Simplify/archive/refs/heads/main.zip"
SHA_URL = "https://api.github.com/repos/lzhoang2801/OpCore-Simplify/commits/main"
CREATE_NEW_CONSOLE = 0x00000010


class Generator:
    def __init__(self, tools_dir):
        self.tools = Path(tools_dir)
        self.dir = self.tools / "OpCore-Simplify-main"
        self.lock = threading.Lock()
        self.state = {"phase": "idle", "pct": 0, "message": "", "efi": None}
        self.proc = None
        self.started = 0

    def _set(self, **kw):
        with self.lock:
            self.state.update(kw)

    def results(self):
        return self.dir / "Results" / "EFI"

    def _download(self):
        self._set(phase="downloading", pct=0, message="Baixando o OpCore Simplify do GitHub...")
        req = Request(ZIP_URL, headers={"User-Agent": "HackCheck"})
        buf = io.BytesIO()
        with urlopen(req, timeout=60) as r:
            total = int(r.headers.get("Content-Length") or 0)
            while True:
                b = r.read(256 << 10)
                if not b:
                    break
                buf.write(b)
                if total:
                    self._set(pct=int(buf.tell() / total * 100))
        tmp = self.tools / "_opcore_tmp"
        shutil.rmtree(tmp, ignore_errors=True)
        with zipfile.ZipFile(buf) as z:
            z.extractall(tmp)
        shutil.rmtree(self.dir, ignore_errors=True)
        self.tools.mkdir(parents=True, exist_ok=True)
        os.replace(tmp / "OpCore-Simplify-main", self.dir)
        shutil.rmtree(tmp, ignore_errors=True)
        # O ZIP não traz o sha_version.txt; sem ele o atualizador do OpCore Simplify
        # acha que está desatualizado e tenta baixar tudo de novo.
        try:
            req = Request(SHA_URL, headers={"User-Agent": "HackCheck", "Accept": "application/vnd.github.sha"})
            with urlopen(req, timeout=30) as r:
                sha = r.read().decode().strip()
            if len(sha) == 40:
                (self.dir / "sha_version.txt").write_text(sha, "utf-8")
        except Exception:
            pass

    def _run(self):
        try:
            if not (self.dir / "OpCore-Simplify.bat").is_file():
                self._download()
            # Remove uma EFI antiga para não confundir com a nova.
            shutil.rmtree(self.dir / "Results", ignore_errors=True)
            self.started = time.time()
            self._set(phase="running", pct=0, efi=None,
                      message="Siga os passos na janela do OpCore Simplify.")
            self.proc = subprocess.Popen(["cmd", "/c", "OpCore-Simplify.bat"], cwd=str(self.dir),
                                         creationflags=CREATE_NEW_CONSOLE)
            last = None
            while True:
                time.sleep(2)
                done = self._efi_ready()
                if done:
                    # Espera os arquivos pararem de mudar (a build termina de gravar).
                    sig = done
                    if sig == last:
                        self._set(phase="done", efi=str(self.results()),
                                  message="EFI gerada! Ela já foi selecionada e validada abaixo.")
                        return
                    last = sig
                    continue
                if self.proc.poll() is not None:
                    self._set(phase="closed", message="A janela do OpCore Simplify foi fechada antes de gerar a EFI.")
                    return
        except Exception as e:
            self._set(phase="error", message="Falha: " + str(e))

    def _efi_ready(self):
        r = self.results()
        cfg = r / "OC" / "config.plist"
        # A pasta Results é apagada antes de abrir a ferramenta, então qualquer EFI aqui é nova.
        if not (cfg.is_file() and (r / "BOOT" / "BOOTx64.efi").is_file()):
            return None
        total = sum(f.stat().st_size for f in r.rglob("*") if f.is_file())
        return (total, cfg.stat().st_mtime)

    def start(self):
        with self.lock:
            if self.state["phase"] in ("downloading", "running"):
                return False
        threading.Thread(target=self._run, daemon=True).start()
        return True

    def status(self):
        with self.lock:
            st = dict(self.state)
        st["alive"] = bool(self.proc and self.proc.poll() is None)
        return st

    def open_results(self):
        p = self.dir / "Results"
        os.startfile(str(p if p.exists() else self.dir))
