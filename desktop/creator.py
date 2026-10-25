"""Criação do pendrive em segundo plano, com progresso por etapa.

Ordem pensada para só apagar o pendrive quando tudo estiver pronto:
download → valida EFI → revalida disco → formata → copia → verifica → ejeta.
"""
import os
import shutil
import threading
import time
import traceback
import uuid
from pathlib import Path

import efi
import recovery
import usbdrive as usb

STEPS = [
    ("download", "Baixar o recovery da Apple"),
    ("efi", "Validar a EFI"),
    ("disk", "Conferir o pendrive"),
    ("format", "Formatar o pendrive (GPT + FAT32)"),
    ("copy", "Copiar EFI e recovery"),
    ("verify", "Verificar os arquivos no pendrive"),
    ("eject", "Ejetar o pendrive"),
]

JOBS = {}


def data_dir():
    d = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "HackCheck"
    (d / "logs").mkdir(parents=True, exist_ok=True)
    return d


class Job:
    def __init__(self, params):
        self.id = uuid.uuid4().hex[:8]
        self.params = params
        self.cancel = threading.Event()
        self.state = {
            "id": self.id, "status": "running", "message": "", "letter": None,
            "steps": [{"key": k, "label": l, "status": "pending", "pct": 0} for k, l in STEPS],
            "log": [],
        }
        self.cancellable = True
        self.lock = threading.Lock()
        self.logfile = data_dir() / "logs" / time.strftime("pendrive-%Y%m%d-%H%M%S.log")

    # ---- estado ----
    def log(self, msg):
        line = time.strftime("%H:%M:%S ") + msg
        with self.lock:
            self.state["log"].append(line)
        with open(self.logfile, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def step(self, key, status=None, pct=None):
        with self.lock:
            for s in self.state["steps"]:
                if s["key"] == key:
                    if status:
                        s["status"] = status
                    if pct is not None:
                        s["pct"] = max(0, min(100, int(pct)))

    def snapshot(self):
        with self.lock:
            st = dict(self.state)
            st["steps"] = [dict(s) for s in self.state["steps"]]
            st["log"] = self.state["log"][-30:]
            st["cancellable"] = self.cancellable
            return st

    def check_cancel(self):
        if self.cancel.is_set():
            raise recovery.Cancelled()

    # ---- execução ----
    def run(self):
        p = self.params
        cur = None
        try:
            cur = "download"
            self.step(cur, "running")
            name = recovery.VERSIONS[p["version"]][0]
            self.log("macOS escolhido: " + name)
            last = [0]

            def prog(a, b, phase):
                if b:
                    # download = 0-90%, verificação = 90-100%
                    self.step("download", pct=(a / b * 90) if phase == "download" else 90 + a / b * 10)
                if time.time() - last[0] > 3:
                    last[0] = time.time()
                    self.log("{}: {:.0f}/{:.0f} MB".format("Baixando" if phase == "download" else "Verificando",
                                                           a / 2**20, b / 2**20))
            if recovery.cached(p["version"], data_dir() / "cache"):
                self.log("Recovery já está em cache, verificado.")
            rec = recovery.download(p["version"], data_dir() / "cache", prog, self.cancel)
            self.step(cur, "done", 100)

            cur = "efi"
            self.step(cur, "running")
            v = efi.validate(p["efi"], p.get("net"), p["version"], p.get("hw"))
            if not v["ok"]:
                raise RuntimeError("EFI inválida: " + "; ".join(v["errors"]))
            for w in v["warnings"]:
                self.log("Aviso: " + w)
            efi_root = Path(v["root"])
            self.step(cur, "done", 100)

            cur = "disk"
            self.step(cur, "running")
            self.check_cancel()
            d = usb.find(p["disk"]["number"], p["disk"]["uid"], p["disk"]["size"])
            self.log("Pendrive confirmado: disco {} ({}, {} GB)".format(d["number"], d["name"], d["gb"]))
            self.step(cur, "done", 100)

            cur = "format"
            self.check_cancel()
            self.cancellable = False  # a partir daqui o pendrive é alterado
            self.step(cur, "running")
            self.log("Aguardando permissão de administrador (UAC)...")
            letter = usb.format_disk(d["number"], d["uid"], d["size"])
            self.state["letter"] = letter
            self.log("Pendrive formatado como {}:".format(letter))
            self.step(cur, "done", 100)

            cur = "copy"
            self.step(cur, "running")
            dst = Path(letter + ":\\")
            files = [(f, dst / "com.apple.recovery.boot" / f.name) for f in rec.iterdir()
                     if f.suffix.lower() in (".dmg", ".chunklist")]
            files += [(f, dst / "EFI" / f.relative_to(efi_root)) for f in efi_root.rglob("*") if f.is_file()]
            total = sum(f.stat().st_size for f, _ in files) or 1
            done = 0
            for src, out in files:
                out.parent.mkdir(parents=True, exist_ok=True)
                with open(src, "rb") as fi, open(out, "wb") as fo:
                    while True:
                        buf = fi.read(4 << 20)
                        if not buf:
                            break
                        fo.write(buf)
                        done += len(buf)
                        self.step(cur, pct=done / total * 100)
                    fo.flush()
                    os.fsync(fo.fileno())
            self.log("{} arquivos copiados ({:.0f} MB).".format(len(files), total / 2**20))
            self.step(cur, "done", 100)

            cur = "verify"
            self.step(cur, "running")
            for src, out in files:
                if not out.is_file() or out.stat().st_size != src.stat().st_size:
                    raise RuntimeError("Arquivo incompleto no pendrive: " + str(out))
            dmg = next(o for s, o in files if o.suffix.lower() == ".dmg")
            cnk = next(o for s, o in files if o.suffix.lower() == ".chunklist")
            # Relê a imagem direto do pendrive (sem cache) e confere com a assinatura da Apple.
            self.log("Relendo a imagem direto do pendrive para conferir a gravação...")
            t0 = time.time()
            recovery.verify(dmg, cnk, lambda a, b: self.step("verify", pct=a / b * 100), unbuffered=True)
            self.log("Imagem no pendrive conferida com a assinatura da Apple ({:.0f} s).".format(time.time() - t0))
            self.step(cur, "done", 100)

            cur = "eject"
            self.step(cur, "running")
            try:
                usb.eject(letter)
                self.log("Pendrive ejetado. Pode remover.")
                self.step(cur, "done", 100)
            except Exception as e:
                self.log("Não foi possível ejetar automaticamente ({}). Use \"Remover hardware com segurança\".".format(e))
                self.step(cur, "skipped", 100)
            self.state["status"] = "done"
            self.state["message"] = "Pendrive criado com sucesso."
        except recovery.Cancelled:
            self.step(cur, "error")
            self.state["status"] = "cancelled"
            self.state["message"] = "Cancelado. O pendrive não foi alterado."
            self.log(self.state["message"])
        except Exception as e:
            self.step(cur, "error")
            self.state["status"] = "error"
            self.state["message"] = str(e)
            self.log("ERRO: " + str(e))
            with open(self.logfile, "a", encoding="utf-8") as f:
                f.write(traceback.format_exc())


def start(params):
    job = Job(params)
    JOBS[job.id] = job
    threading.Thread(target=job.run, daemon=True).start()
    return job.id


def status(job_id):
    job = JOBS.get(job_id)
    return job.snapshot() if job else None


def cancel(job_id):
    job = JOBS.get(job_id)
    if job and job.cancellable:
        job.cancel.set()
        return True
    return False
