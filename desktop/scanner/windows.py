"""Coleta de hardware no Windows via CIM/WMI (PowerShell).

Gera o mesmo formato de JSON que o script da dashboard, mais o campo "laptop".
"""
import json
import subprocess

PS_SCRIPT = r"""
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$ErrorActionPreference='SilentlyContinue'
$ch=@((Get-CimInstance Win32_SystemEnclosure).ChassisTypes)
$laptop=[bool]($ch|?{$_ -in 8,9,10,11,14,30,31,32}) -or [bool](Get-CimInstance Win32_Battery)
$o=[ordered]@{
 cpu=(Get-CimInstance Win32_Processor|Select -First 1).Name
 gpu=@(Get-CimInstance Win32_VideoController|%{$_.Name})
 board=(Get-CimInstance Win32_BaseBoard).Product
 ram=[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB)
 net=@(Get-CimInstance Win32_NetworkAdapter|?{$_.PhysicalAdapter}|%{$_.Name})
 audio=@(Get-CimInstance Win32_SoundDevice|%{$_.Name})
 disk=@(Get-CimInstance Win32_DiskDrive|?{$_.InterfaceType -ne 'USB'}|%{$_.Model})
 laptop=$laptop
}
$o|ConvertTo-Json -Compress
"""

CREATE_NO_WINDOW = 0x08000000


def scan(timeout=60):
    """Retorna um dict com o hardware detectado. Lança RuntimeError em caso de falha."""
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", PS_SCRIPT],
        capture_output=True,
        timeout=timeout,
        creationflags=CREATE_NO_WINDOW,
    )
    out = proc.stdout.decode("utf-8", errors="replace").strip().lstrip("﻿")
    if not out:
        err = proc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError("O PowerShell não retornou dados. " + err[:300])
    data = json.loads(out)
    for k in ("gpu", "net", "audio", "disk"):
        v = data.get(k)
        data[k] = [x for x in (v if isinstance(v, list) else [v]) if x]
    return data


if __name__ == "__main__":
    print(json.dumps(scan(), ensure_ascii=False, indent=2))
