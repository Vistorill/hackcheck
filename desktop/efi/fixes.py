"""Correções automáticas na EFI para hardware que o OpCore Simplify não trata sozinho.

Hoje: spoof de device-id de GPUs AMD que o macOS não reconhece, mas que funcionam
fingindo ser o modelo vizinho (guia de GPUs da Dortania). Sem o spoof a tela fica
preta ou sem aceleração.
"""
import json
import plistlib
import re

# "VVVV:DDDD" real → (device-id que o macOS conhece, em little-endian; descrição).
GPU_SPOOFS = {
    "1002:6FDF": (bytes.fromhex("DF670000"), "RX 580 2048SP (6FDF) vista como RX 580 (67DF)"),
}


def norm_id(dev_id):
    """'1002-6FDF', 'VEN_1002&DEV_6FDF' ou '1002:6fdf' → '1002:6FDF'."""
    m = re.search(r"([0-9A-F]{4})\W*(?:DEV_)?([0-9A-F]{4})", (dev_id or "").upper().replace("VEN_", ""))
    return m.group(1) + ":" + m.group(2) if m else ""


def pci_path(location):
    """Caminho do Windows 'PCIROOT(0)#PCI(0100)#PCI(0000)' → 'PciRoot(0x0)/Pci(0x1,0x0)/Pci(0x0,0x0)'.
    Caminhos que já estão no formato do OpenCore voltam como estão."""
    location = (location or "").strip()
    if location.startswith("PciRoot("):
        return location
    m = re.fullmatch(r"PCIROOT\(([0-9A-F]+)\)((?:#PCI\([0-9A-F]{4}\))+)", location, re.I)
    if not m:
        return None
    parts = ["PciRoot(0x{:X})".format(int(m.group(1), 16))]
    for dev, fn in re.findall(r"PCI\(([0-9A-F]{2})([0-9A-F]{2})\)", m.group(2), re.I):
        parts.append("Pci(0x{:X},0x{:X})".format(int(dev, 16), int(fn, 16)))
    return "/".join(parts)


def gpus_from_opcore_report(path):
    """Lê as GPUs do Report.json do OpCore Simplify no formato de hw['gpudev']."""
    with open(path, encoding="utf-8") as f:
        rep = json.load(f)
    return [{"name": n, "id": g.get("Device ID", ""), "path": g.get("PCI Path", "")}
            for n, g in (rep.get("GPU") or {}).items()]


def missing(cfg, gpus):
    """Spoofs que o hardware precisa e o config.plist não tem: [(caminho, props, descrição)]."""
    add = cfg.get("DeviceProperties", {}).get("Add", {})
    out = []
    for g in gpus or []:
        spoof = GPU_SPOOFS.get(norm_id(g.get("id")))
        path = pci_path(g.get("path"))
        if not spoof or not path:
            continue
        if add.get(path, {}).get("device-id") != spoof[0]:
            out.append((path, {"device-id": spoof[0]}, spoof[1]))
    return out


def apply(cfg, gpus):
    """Adiciona ao cfg os spoofs que faltam. Retorna as descrições do que mudou."""
    todo = missing(cfg, gpus)
    add = cfg.setdefault("DeviceProperties", {}).setdefault("Add", {})
    for path, props, _ in todo:
        add.setdefault(path, {}).update(props)
    return [desc for _, _, desc in todo]


def apply_file(cfg_path, gpus):
    """Aplica as correções direto num config.plist. Retorna as descrições do que mudou."""
    with open(cfg_path, "rb") as f:
        cfg = plistlib.load(f)
    done = apply(cfg, gpus)
    if done:
        with open(cfg_path, "wb") as f:
            plistlib.dump(cfg, f, sort_keys=False)
    return done
