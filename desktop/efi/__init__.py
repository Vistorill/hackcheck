"""Validação de uma pasta EFI do OpenCore antes de gravar no pendrive.

Confere a estrutura, os arquivos referenciados no config.plist, se o SMBIOS é
aceito pela versão do macOS escolhida e se os drivers (kexts) necessários para o
hardware detectado estão presentes. Regras baseadas no guia Dortania (out/2026).
"""
import plistlib
import re
from pathlib import Path

# Índices de versão iguais a V em assets/rules.js.
VENTURA, SONOMA, SEQUOIA, TAHOE = 5, 6, 7, 8

# Modelo mínimo (família → número do modelo) aceito por cada versão do macOS, em Macs Intel.
# None = nenhum modelo Intel dessa família é aceito.
SMBIOS_MIN = {
    VENTURA: {"iMac": 18, "iMacPro": 1, "MacPro": 7, "Macmini": 8, "MacBookPro": 14, "MacBookAir": 8, "MacBook": 10},
    SONOMA: {"iMac": 19, "iMacPro": 1, "MacPro": 7, "Macmini": 8, "MacBookPro": 15, "MacBookAir": 8, "MacBook": None},
    SEQUOIA: {"iMac": 19, "iMacPro": 1, "MacPro": 7, "Macmini": 8, "MacBookPro": 15, "MacBookAir": 9, "MacBook": None},
    TAHOE: {"iMac": 20, "iMacPro": None, "MacPro": 7, "Macmini": None, "MacBookPro": 16, "MacBookAir": None, "MacBook": None},
}
SMBIOS_SUGGEST = {
    VENTURA: "iMac19,1 (com iGPU) ou iMacPro1,1/MacPro7,1 (só GPU dedicada)",
    SONOMA: "iMac19,1 (com iGPU) ou iMacPro1,1/MacPro7,1 (só GPU dedicada)",
    SEQUOIA: "iMac19,1 (com iGPU) ou iMacPro1,1/MacPro7,1 (só GPU dedicada)",
    TAHOE: "iMac20,1 (com iGPU) ou MacPro7,1 (só GPU dedicada)",
}

# Kext de Ethernet esperado para cada família de placa (o instalador online precisa de rede).
ETH_KEXTS = [
    (re.compile(r"I22[56]", re.I), ["AppleIGC"]),
    (re.compile(r"I21[0-9]|I219|82579|Intel.*Ethernet", re.I), ["IntelMausi", "SmallTreeIntel82576"]),
    # RTL812xLucy é o sucessor do LucyRTL8125Ethernet (mesmo autor, Mieze; 2026).
    (re.compile(r"8125|8126|2\.5G", re.I), ["RTL812xLucy", "LucyRTL8125Ethernet"]),
    (re.compile(r"8111|8168|RTL81|Realtek.*Gigabit|Realtek PCIe GbE", re.I), ["RealtekRTL8111"]),
    (re.compile(r"Atheros|Killer E2", re.I), ["AtherosE2200Ethernet"]),
    (re.compile(r"Aquantia|AQC", re.I), []),  # suporte nativo
]
NOT_ETH = re.compile(r"wi-?fi|wireless|802\.11|wlan|bluetooth|virtual|hyper-v|vpn|tap|miniport", re.I)


def find_root(path):
    """Aceita a pasta EFI ou a pasta que contém EFI. Retorna o Path da pasta EFI."""
    p = Path(path)
    if (p / "EFI").is_dir():
        p = p / "EFI"
    return p


def _kext_version(path):
    try:
        with open(path / "Contents" / "Info.plist", "rb") as f:
            return plistlib.load(f).get("CFBundleShortVersionString", "")
    except Exception:
        return ""


def _smbios_check(model, version):
    """Retorna None se o modelo é aceito, ou a mensagem de erro."""
    if version not in SMBIOS_MIN or not model:
        return None
    m = re.match(r"([A-Za-z]+?)(\d+),\d+$", model)
    if not m:
        return None
    fam, num = m.group(1), int(m.group(2))
    rule = SMBIOS_MIN[version]
    if fam not in rule:
        return None
    if rule[fam] is None or num < rule[fam]:
        return "O SMBIOS {} não é aceito por esta versão do macOS: o instalador vai recusar. Use {}.".format(
            model, SMBIOS_SUGGEST[version])
    return None


def _boot_args(cfg):
    nv = cfg.get("NVRAM", {}).get("Add", {}).get("7C436110-AB2A-4BBB-A880-FE41995C9F82", {})
    return str(nv.get("boot-args", ""))


def _has_layout_id(cfg):
    props = cfg.get("DeviceProperties", {}).get("Add", {})
    return any("layout-id" in v for v in props.values() if isinstance(v, dict))


def drivers_for(hw, version, kexts, cfg):
    """Lista de drivers que o hardware precisa: [{name, kind, status, reason}].
    status: ok | missing | remove | info."""
    out = []
    ba = _boot_args(cfg)

    def need(names, kind, reason, required=True):
        names = names if isinstance(names, list) else [names]
        have = [n for n in names if n in kexts]
        out.append({"name": " ou ".join(names), "kind": kind, "reason": reason,
                    "status": "ok" if have else ("missing" if required else "info")})

    need("Lilu", "Base", "Base para quase todos os outros kexts.")
    need("VirtualSMC", "Base", "Emula o chip SMC; sem ele o macOS não inicia.")

    cpu = hw.get("cpu") or ""
    gpus = [g for g in hw.get("gpu") or [] if not re.search(r"Microsoft|Basic|Virtual|Remote|Parsec", g, re.I)]
    amd_dgpu = [g for g in gpus if re.search(r"RX\s*\d|Vega\s*(56|64)|Radeon VII|Radeon Pro", g, re.I)]
    # ---- Vídeo ----
    for g in amd_dgpu:
        x = re.search(r"RX\s*(\d{3,4})", g, re.I)
        x = int(x.group(1)) if x else 0
        if 6700 <= x <= 6799:
            need("NootRX", "Vídeo", g + ": a Navi 22 só funciona com o NootRX.")
            continue
        if version == TAHOE:
            if "WhateverGreen" in kexts:
                out.append({"name": "WhateverGreen", "kind": "Vídeo", "status": "remove",
                            "reason": "No Tahoe o WhateverGreen causa kernel panic com GPUs AMD: remova-o."})
        else:
            need("WhateverGreen", "Vídeo", g + ": correções de vídeo para GPU AMD.")
        if (5000 <= x <= 6999) and "agdpmod=pikera" not in ba:
            out.append({"name": "agdpmod=pikera", "kind": "Vídeo", "status": "missing",
                        "reason": g + ": sem este boot-arg a tela costuma ficar preta."})
    if re.search(r"Radeon(\(TM\))?\s+(Vega\s*\d+\s+)?Graphics", " ".join(gpus), re.I) and not amd_dgpu:
        need("NootedRed", "Vídeo", "iGPU AMD (APU Ryzen) só funciona com o NootedRed.")
    if any(re.search(r"Intel.*(UHD|HD|Iris)", g, re.I) for g in gpus) and version != TAHOE:
        need("WhateverGreen", "Vídeo", "Vídeo integrado Intel: precisa do WhateverGreen e do framebuffer.")

    # ---- Áudio ----
    analog = [a for a in hw.get("audio") or [] if re.search(r"Realtek|ALC|Conexant|IDT", a, re.I)]
    if analog:
        if version == TAHOE:
            out.append({"name": "AppleALC", "kind": "Áudio", "status": "info",
                        "reason": "No Tahoe o AppleHDA foi removido: o AppleALC não traz som analógico. "
                                  "Use áudio por HDMI/USB ou o VoodooHDA."})
        else:
            need("AppleALC", "Áudio", analog[0] + ": som analógico (fone e caixas).")
            if "AppleALC" in kexts and "alcid=" not in ba and not _has_layout_id(cfg):
                out.append({"name": "alcid / layout-id", "kind": "Áudio", "status": "missing",
                            "reason": "Sem alcid= nos boot-args nem layout-id nas DeviceProperties o AppleALC não ativa o som."})

    # ---- CPU ----
    if re.search(r"Ryzen|Threadripper", cpu, re.I):
        patches = cfg.get("Kernel", {}).get("Patch", [])
        if not any(p.get("Enabled") and re.search(r"algrey|AMD|cpuid", str(p.get("Comment", "")), re.I) for p in patches):
            out.append({"name": "Patches AMD Vanilla", "kind": "CPU", "status": "missing",
                        "reason": "CPUs AMD precisam dos patches de kernel do AMD Vanilla."})
        need("AMDRyzenCPUPowerManagement", "CPU", "Gerenciamento de energia e sensores da CPU AMD.", required=False)
    m = re.search(r"i[3579]-(\d{5})(\w*)", cpu, re.I)
    if m:
        d, suf = m.group(1), m.group(2)
        gen = int(d[:2])
        no_ecore = gen == 12 and re.match(r"12[1-6]\d0$", d) and "K" not in suf.upper()
        if gen >= 12 and not no_ecore:
            need("CpuTopologyRebuild", "CPU", "CPU híbrida (P-cores + E-cores): organiza os núcleos para o macOS.")
    if re.search(r"Intel", cpu, re.I):
        need("SMCProcessor", "CPU", "Sensores de temperatura da CPU Intel.", required=False)

    # ---- Rede ----
    eths = [n for n in hw.get("net") or [] if not NOT_ETH.search(n)]
    for n in eths:
        for rx, names in ETH_KEXTS:
            if rx.search(n):
                if names:
                    need(names, "Rede", n + ": obrigatório, o instalador baixa o macOS pela internet.")
                break
    for n in hw.get("net") or []:
        if re.search(r"wi-?fi|wireless|802\.11|wlan", n, re.I) and re.search(r"Intel", n, re.I) and "USB" not in n:
            need(["AirportItlwm", "itlwm"], "Rede", n + ": Wi-Fi Intel.", required=False)
            need(["IntelBluetoothFirmware", "BlueToolFixup"], "Rede", "Bluetooth Intel.", required=False)

    # ---- Armazenamento e USB ----
    if hw.get("disk"):
        need("NVMeFix", "Disco", "Melhora o gerenciamento de energia de SSDs NVMe.", required=False)
    need(["USBToolBox", "UTBMap", "USBMap", "USBPorts"], "USB",
         "Mapeamento USB: pode ser feito depois da instalação (aba Mapeamento USB).", required=False)
    if version >= SONOMA:
        need("RestrictEvents", "Sistema", "Necessário para atualizações OTA a partir do macOS 14.4.", required=False)
    return out


def validate(path, net=None, version=None, hw=None):
    """Retorna {ok, root, errors, warnings, kexts, smbios, drivers}."""
    hw = dict(hw or {})
    if net and not hw.get("net"):
        hw["net"] = net
    root = find_root(path)
    errors, warnings = [], []
    res = {"ok": False, "root": str(root), "errors": errors, "warnings": warnings,
           "kexts": [], "smbios": "", "drivers": []}
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

    # O config de exemplo do OpenCore (Sample.plist) indica uma EFI inacabada: o OpCore
    # Simplify copia esse arquivo no começo da geração e só grava o definitivo no final.
    gen = cfg.get("PlatformInfo", {}).get("Generic", {})
    ba = _boot_args(cfg)
    if gen.get("SystemSerialNumber") == "W00000000001" and ba.strip() == "-v keepsyms=1":
        res["smbios"] = gen.get("SystemProductName", "")
        errors.append("EFI incompleta: o config.plist ainda é o exemplo do OpenCore. A geração no OpCore "
                      "Simplify não terminou (ou parou com erro). Conclua a opção 6 (Build) na janela dele.")
        return res

    # Arquivos referenciados no config.plist precisam existir.
    kexts = {}
    for k in cfg.get("Kernel", {}).get("Add", []):
        if not k.get("Enabled"):
            continue
        bp = k.get("BundlePath", "")
        name = Path(bp).stem
        kexts[name] = _kext_version(oc / "Kexts" / bp)
        if not (oc / "Kexts" / bp).is_dir():
            errors.append("Kext no config.plist, mas ausente na pasta: " + bp)
        ep = k.get("ExecutablePath")
        if ep and not (oc / "Kexts" / bp / ep).is_file():
            errors.append("Executável do kext ausente: {}/{}".format(bp, ep))
    res["kexts"] = ["{} {}".format(n, v).strip() for n, v in kexts.items()]
    for a in cfg.get("ACPI", {}).get("Add", []):
        if a.get("Enabled") and not (oc / "ACPI" / a.get("Path", "")).is_file():
            errors.append("SSDT no config.plist, mas ausente: " + a.get("Path", ""))
    for d in cfg.get("UEFI", {}).get("Drivers", []):
        name = d.get("Path") if isinstance(d, dict) else d
        enabled = d.get("Enabled", True) if isinstance(d, dict) else True
        if enabled and name and not (oc / "Drivers" / name).is_file():
            errors.append("Driver no config.plist, mas ausente: " + name)

    # SMBIOS: o modelo de Mac simulado precisa ser aceito pela versão escolhida.
    gen = cfg.get("PlatformInfo", {}).get("Generic", {})
    model = gen.get("SystemProductName", "")
    res["smbios"] = model
    if version is not None:
        e = _smbios_check(model, int(version))
        if e:
            errors.append(e)
    serial = gen.get("SystemSerialNumber", "")
    if not serial or set(serial) <= {"0", "W"} or serial == "W00000000001":  # valor do Sample.plist
        warnings.append("SMBIOS sem número de série gerado: gere um (GenSMBIOS/OpCore Simplify) antes de usar o iCloud.")
    if version == TAHOE and cfg.get("Misc", {}).get("Security", {}).get("SecureBootModel") not in ("Disabled", None):
        warnings.append("No Tahoe, o SecureBootModel deve ser Disabled para as atualizações funcionarem (Dortania).")

    # Drivers necessários para o hardware detectado.
    res["drivers"] = drivers_for(hw, int(version) if version is not None else SEQUOIA, kexts, cfg)
    for d in res["drivers"]:
        if d["status"] == "missing":
            # Sem Ethernet o instalador online não funciona: isso bloqueia.
            (errors if d["kind"] in ("Base", "Rede") else warnings).append(
                "Falta {} ({}): {}".format(d["name"], d["kind"], d["reason"]))
        elif d["status"] == "remove":
            errors.append("Remova {}: {}".format(d["name"], d["reason"]))
    res["ok"] = not errors
    return res
