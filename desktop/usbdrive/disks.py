"""Lista pendrives USB no Windows (sem precisar de administrador)."""
import json
import subprocess

CREATE_NO_WINDOW = 0x08000000

PS_LIST = r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$ErrorActionPreference='SilentlyContinue'
$r=@(Get-Disk | ?{ $_.BusType -eq 'USB' -and -not $_.IsSystem -and -not $_.IsBoot } | %{
  $d=$_
  $vols=@($d | Get-Partition | ?{ $_.DriveLetter } | %{ $v=$_ | Get-Volume; [ordered]@{ letter=[string]$_.DriveLetter; label=$v.FileSystemLabel; fs=$v.FileSystem } })
  [ordered]@{ number=$d.Number; name=$d.FriendlyName; serial=$d.SerialNumber; uid=$d.UniqueId; size=$d.Size;
              style=[string]$d.PartitionStyle; readonly=$d.IsReadOnly; offline=$d.IsOffline; volumes=$vols }
})
ConvertTo-Json -InputObject $r -Depth 4 -Compress
"""

MIN_SIZE = 4 * 10**9          # 4 GB
MAX_SIZE = 256 * 2**30        # acima disso quase certamente é um HD externo
BIG_WARN = 64 * 2**30


def _ps(script, timeout=60):
    p = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                       capture_output=True, timeout=timeout, creationflags=CREATE_NO_WINDOW)
    return p.stdout.decode("utf-8", errors="replace").strip().lstrip("﻿")


def list_disks():
    """Retorna os discos USB elegíveis, com avisos. Discos do sistema nunca aparecem."""
    out = _ps(PS_LIST)
    disks = json.loads(out) if out else []
    if isinstance(disks, dict):
        disks = [disks]
    for d in disks:
        d["volumes"] = d.get("volumes") or []
        size = d.get("size") or 0
        d["gb"] = round(size / 2**30, 2)
        d["blocked"] = None
        d["warning"] = None
        if d.get("readonly"):
            d["blocked"] = "Disco protegido contra gravação."
        elif size < MIN_SIZE:
            d["blocked"] = "Pequeno demais (mínimo 4 GB)."
        elif size > MAX_SIZE:
            d["blocked"] = "Grande demais para um pendrive (parece um HD externo)."
        elif size > BIG_WARN:
            d["warning"] = "Disco grande: confirme que não é um HD externo com arquivos."
    return disks


def find(number, uid, size):
    """Revalida que o disco `number` ainda é o mesmo escolhido pelo usuário."""
    for d in list_disks():
        if d["number"] == number:
            if d["uid"] != uid or d["size"] != size:
                raise RuntimeError("O pendrive mudou desde a escolha. Escolha de novo.")
            if d["blocked"]:
                raise RuntimeError(d["blocked"])
            return d
    raise RuntimeError("O pendrive escolhido não foi encontrado. Ele foi removido?")
