"""Scanners de hardware por sistema operacional."""
import sys


def scan():
    if sys.platform == "win32":
        from .windows import scan as _scan
        return _scan()
    raise RuntimeError("Sistema operacional ainda não suportado: " + sys.platform)
