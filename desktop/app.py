"""HackCheck Desktop: abre a dashboard numa janela nativa e faz o scan do hardware."""
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import webview

import creator
import efi
import recovery
import scanner
import usbdrive as usb
from efi.opcore import Generator

VERSION = "0.3.2"
GEN = Generator(creator.data_dir() / "tools")


def base_dir():
    # No executável do PyInstaller os arquivos ficam em sys._MEIPASS; no código-fonte, na raiz do repositório.
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


class Api:
    """Funções chamadas pela dashboard via window.pywebview.api."""

    def scan(self):
        try:
            return {"ok": True, "data": scanner.scan()}
        except Exception as e:  # o erro é mostrado na interface
            return {"ok": False, "error": str(e)}

    def info(self):
        return {"version": VERSION, "platform": sys.platform}

    # ---- criação do pendrive ----
    def list_disks(self):
        try:
            return {"ok": True, "disks": usb.list_disks()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def recovery_cached(self, version):
        return bool(recovery.cached(int(version), creator.data_dir() / "cache"))

    def choose_efi(self):
        r = webview.windows[0].create_file_dialog(webview.FileDialog.FOLDER)
        return r[0] if r else None

    def validate_efi(self, path, net=None, version=None, hw=None):
        try:
            r = efi.validate(path, net, version, hw)
        except Exception as e:
            r = {"ok": False, "errors": [str(e)], "warnings": [], "drivers": [], "kexts": [], "smbios": ""}
        self._log_validation(path, version, r)
        return r

    def _log_validation(self, path, version, r):
        lines = ["EFI: " + str(path),
                 "macOS: " + (recovery.VERSIONS[int(version)][0] if version is not None else "?"),
                 "SMBIOS: " + r.get("smbios", ""),
                 "Resultado: " + ("VÁLIDA" if r["ok"] else "INVÁLIDA")]
        lines += ["ERRO: " + e for e in r["errors"]]
        lines += ["AVISO: " + w for w in r["warnings"]]
        lines += ["Driver [{}] {}: {}".format(d["status"], d["name"], d["reason"]) for d in r.get("drivers", [])]
        lines += ["Kexts: " + ", ".join(r.get("kexts", []))]
        r["report"] = "\n".join(lines)
        with open(creator.data_dir() / "logs" / "validacao-efi.log", "a", encoding="utf-8") as f:
            f.write(time.strftime("==== %Y-%m-%d %H:%M:%S ====\n") + r["report"] + "\n\n")

    def copy_text(self, text):
        # Área de transferência do Windows (a WebView não permite copiar de páginas file://).
        # Passa por arquivo UTF-8: pela entrada padrão o PowerShell 5.1 estraga os acentos.
        tmp = creator.data_dir() / "clipboard.txt"
        tmp.write_text(text, encoding="utf-8")
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-Content -Raw -Encoding UTF8 -LiteralPath '{}' | Set-Clipboard".format(tmp)],
                       creationflags=0x08000000)
        tmp.unlink()
        return True

    def efi_generate(self):
        return GEN.start()

    def efi_generate_status(self):
        return GEN.status()

    def efi_open_results(self):
        GEN.open_results()

    def open_url(self, url):
        # Só links do GitHub/Dortania usados pela interface.
        if url.startswith(("https://github.com/", "https://dortania.github.io/")):
            webbrowser.open(url)

    def create_usb(self, params):
        return creator.start(params)

    def job_status(self, job_id):
        return creator.status(job_id)

    def cancel_job(self, job_id):
        return creator.cancel(job_id)

    def open_logs(self):
        os.startfile(str(creator.data_dir() / "logs"))


def main():
    page = base_dir() / "dashboard" / "index.html"
    if not page.exists():
        sys.exit("Interface não encontrada: " + str(page))
    webview.create_window(
        "HackCheck " + VERSION,
        # file:// para que ../assets/rules.js seja resolvido a partir da raiz.
        url=page.as_uri(),
        js_api=Api(),
        width=1180,
        height=800,
        min_size=(760, 560),
    )
    webview.start(debug=bool(os.environ.get("HACKCHECK_DEBUG")))


if __name__ == "__main__":
    main()
