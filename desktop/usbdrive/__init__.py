"""Pendrive: listar, formatar (elevado) e gravar."""
import json
import os
import subprocess
import tempfile
from pathlib import Path

from .disks import list_disks, find  # noqa: F401

CREATE_NO_WINDOW = 0x08000000


def script_path():
    return Path(__file__).with_name("format.ps1")


def format_disk(number, uid, size, label="HACKCHECK"):
    """Formata o disco pedindo elevação (UAC). Retorna a letra da unidade."""
    fd, result = tempfile.mkstemp(suffix=".json", prefix="hackcheck-")
    os.close(fd)
    os.remove(result)
    args = ("-NoProfile -ExecutionPolicy Bypass -File \"{s}\" -Number {n} -UniqueId \"{u}\" -Size {z} "
            "-ResultFile \"{r}\" -Label {l}").format(s=script_path(), n=int(number), u=uid.replace('"', ''),
                                                      z=int(size), r=result, l=label)
    # Start-Process -Verb RunAs abre o UAC; -Wait espera a formatação terminar.
    launcher = "Start-Process powershell -Verb RunAs -WindowStyle Hidden -Wait -ArgumentList '{}'".format(
        args.replace("'", "''"))
    p = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", launcher],
                       capture_output=True, creationflags=CREATE_NO_WINDOW, timeout=900)
    if not os.path.exists(result):
        err = p.stderr.decode("utf-8", errors="replace")
        if "cancel" in err.lower() or "cancelad" in err.lower():
            raise RuntimeError("Permissão de administrador negada. A formatação foi cancelada; nada foi apagado.")
        raise RuntimeError("A formatação não retornou resultado. " + err.strip()[:300])
    with open(result, encoding="utf-8-sig") as f:
        r = json.load(f)
    os.remove(result)
    if not r.get("ok"):
        raise RuntimeError(r.get("message") or "Falha ao formatar.")
    return r["letter"]


def eject(letter):
    """Ejeta com segurança (melhor esforço)."""
    ps = ("$s=New-Object -ComObject Shell.Application;"
          "$s.Namespace(17).ParseName('{}:').InvokeVerb('Eject')").format(letter)
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                   capture_output=True, creationflags=CREATE_NO_WINDOW, timeout=60)
