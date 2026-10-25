"""HackCheck Desktop: abre a dashboard numa janela nativa e faz o scan do hardware."""
import os
import sys
from pathlib import Path

import webview

import scanner

VERSION = "0.1.0"


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
