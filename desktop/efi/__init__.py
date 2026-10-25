"""Validação de uma pasta EFI do OpenCore antes de gravar no pendrive."""
import plistlib
import re
from pathlib import Path

# Kext de Ethernet esperado para cada família de placa (o instalador online precisa de rede).
ETH_KEXTS = [
    (re.compile(r"I21[0-9]|I219|82579|Intel.*Ethernet", re.I), ["IntelMausi", "SmallTreeIntel82576"]),
    (re.compile(r"I22[56]", re.I), ["AppleIGC"]),
    (re.compile(r"8125|8126|2\.5G", re.I), ["LucyRTL8125Ethernet"]),
    (re.compile(r"8111|8168|RTL81|Realtek.*Gigabit|Realtek PCIe GbE", re.I), ["RealtekRTL8111"]),
    (re.compile(r"Atheros|Killer E2", re.I), ["AtherosE2200Ethernet"]),
]


def find_root(path):
    """Aceita a pasta EFI ou a pasta que contém EFI. Retorna o Path da pasta EFI."""
    p = Path(path)
    if (p / "EFI").is_dir():
        p = p / "EFI"
    return p


def validate(path, net=None):
    """Retorna {ok, root, errors, warnings, kexts, oc_files}."""
    root = find_root(path)
    errors, warnings = [], []
    res = {"ok": False, "root": str(root), "errors": errors, "warnings": warnings, "kexts": []}
    if root.name.upper() != "EFI" or not root.is_dir():
        errors.append("Selecione a pasta EFI (ela contém as pastas BOOT e OC).")
        return res
    oc = root / "OC"
    for rel in ("BOOT/BOOTx64.efi", "OC/OpenCore.efi", "OC/config.plist"):
        if not (root / rel).is_file():
            errors.append("Arquivo obrigatório ausente: EFI/" + rel)
    if errors:
        return res

    try:
        with open(oc / "config.plist", "rb") as f:
            cfg = plistlib.load(f)
    except Exception as e:
        errors.append("config.plist inválido: " + str(e))
        return res

    # Arquivos referenciados no config.plist precisam existir.
    for k in cfg.get("Kernel", {}).get("Add", []):
        if not k.get("Enabled"):
            continue
        bp = k.get("BundlePath", "")
        res["kexts"].append(Path(bp).stem)
        if not (oc / "Kexts" / bp).is_dir():
            errors.append("Kext no config.plist, mas ausente na pasta: " + bp)
        ep = k.get("ExecutablePath")
        if ep and not (oc / "Kexts" / bp / ep).is_file():
            errors.append("Executável do kext ausente: {}/{}".format(bp, ep))
    for a in cfg.get("ACPI", {}).get("Add", []):
        if a.get("Enabled") and not (oc / "ACPI" / a.get("Path", "")).is_file():
            errors.append("SSDT no config.plist, mas ausente: " + a.get("Path", ""))
    for d in cfg.get("UEFI", {}).get("Drivers", []):
        name = d.get("Path") if isinstance(d, dict) else d
        enabled = d.get("Enabled", True) if isinstance(d, dict) else True
        if enabled and name and not (oc / "Drivers" / name).is_file():
            errors.append("Driver no config.plist, mas ausente: " + name)

    kexts = set(res["kexts"])
    if "Lilu" not in kexts:
        warnings.append("Lilu.kext não está habilitado: quase toda EFI precisa dele.")
    if not {"VirtualSMC", "FakeSMC"} & kexts:
        warnings.append("VirtualSMC.kext não está habilitado: o macOS não inicia sem um emulador de SMC.")
    pi = cfg.get("PlatformInfo", {}).get("Generic", {})
    serial = pi.get("SystemSerialNumber", "")
    if not serial or set(serial) <= {"0", "W"} or serial == "W00000000001":  # valor do Sample.plist
        warnings.append("SMBIOS sem número de série gerado: gere um (GenSMBIOS/OpCore Simplify) antes de usar o iCloud.")

    # Ethernet: o instalador online baixa o macOS pela rede.
    eths = [n for n in (net or []) if not re.search(r"wi-?fi|wireless|802\.11|wlan|bluetooth|virtual|hyper-v|vpn|tap", n, re.I)]
    if eths:
        need = []
        for n in eths:
            for rx, names in ETH_KEXTS:
                if rx.search(n):
                    need.append((n, names))
                    break
        if need and not any(set(names) & kexts for _, names in need):
            n, names = need[0]
            warnings.append("Nenhum kext de Ethernet para \"{}\" (esperado: {}). O instalador online precisa de rede."
                            .format(n, " ou ".join(names)))
    res["ok"] = not errors
    return res
