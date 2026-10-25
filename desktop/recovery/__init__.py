"""Download do recovery do macOS direto dos servidores da Apple.

Usa as funções oficiais do macrecovery.py (OpenCorePkg 1.0.8, BSD-3) para obter a
sessão, os links e verificar a assinatura do chunklist. O download em si é feito
aqui para reportar progresso à interface e permitir cancelamento.
"""
import json
import os
import shutil
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from . import macrecovery as mr

# Índice = posição em V (assets/rules.js). Board IDs do recovery_urls.txt do OpenCorePkg 1.0.8.
VERSIONS = {
    0: ("High Sierra 10.13", "Mac-7BA5B2D9E42DDD94", "00000000000J80300", "default"),
    1: ("Mojave 10.14", "Mac-7BA5B2DFE22DDD8C", "00000000000KXPG00", "default"),
    2: ("Catalina 10.15", "Mac-00BE6ED71E35EB86", mr.MLB_ZERO, "default"),
    3: ("Big Sur 11", "Mac-2BD1B31983FE1663", mr.MLB_ZERO, "default"),
    4: ("Monterey 12", "Mac-E43C1C25D4880AD6", mr.MLB_ZERO, "default"),
    5: ("Ventura 13", "Mac-B4831CEBD52A0C4C", mr.MLB_ZERO, "default"),
    6: ("Sonoma 14", "Mac-827FAC58A8FDFA22", mr.MLB_ZERO, "default"),
    7: ("Sequoia 15", "Mac-7BA5B2D9E42DDD94", mr.MLB_ZERO, "default"),
    8: ("Tahoe 26", "Mac-CFF7D910A743CAAF", mr.MLB_ZERO, "latest"),
}

CHUNK = 1 << 20


class Cancelled(Exception):
    pass


def _query(fn, *args, **kw):
    # O macrecovery chama sys.exit() em erro HTTP; converte em exceção normal.
    try:
        return fn(*args, **kw)
    except SystemExit:
        raise RuntimeError("Falha ao falar com os servidores da Apple (osrecovery.apple.com). Verifique a internet.")


def _download(url, token, dest, progress, cancel):
    purl = urlparse(url)
    req = Request(url, headers={
        "Host": purl.hostname,
        "Connection": "close",
        "User-Agent": "InternetRecovery/1.0",
        "Cookie": "AssetToken=" + token,
    })
    part = dest.with_suffix(dest.suffix + ".part")
    with urlopen(req, timeout=60) as resp, open(part, "wb") as fh:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while True:
            if cancel.is_set():
                raise Cancelled()
            buf = resp.read(CHUNK)
            if not buf:
                break
            fh.write(buf)
            done += len(buf)
            progress(done, total)
    os.replace(part, dest)


def verify(dmg, cnk, progress=None):
    """Verifica o .dmg contra o chunklist assinado pela Apple. Lança RuntimeError se falhar."""
    total = os.path.getsize(dmg)
    done = 0
    try:
        with open(dmg, "rb") as f:
            for i, (size, digest) in enumerate(mr.verify_chunklist(cnk), 1):
                data = f.read(size)
                if len(data) != size or mr.hashlib.sha256(data).digest() != digest:
                    raise RuntimeError("bloco %d corrompido" % i)
                done += size
                if progress:
                    progress(done, total)
            if f.read(1):
                raise RuntimeError("imagem maior que o chunklist")
    except AssertionError:
        raise RuntimeError("chunklist inválido")


def cached(index, cache_dir):
    """Retorna o diretório em cache se o recovery dessa versão já foi baixado e verificado."""
    d = Path(cache_dir) / "recovery" / str(index)
    meta = d / "hackcheck.json"
    if meta.exists():
        info = json.loads(meta.read_text("utf-8"))
        if all((d / f).exists() for f in info["files"]):
            return d
    return None


def download(index, cache_dir, progress=lambda done, total, phase: None, cancel=None):
    """Baixa e verifica o recovery da versão `index`. Retorna o diretório com .dmg e .chunklist."""
    import threading
    cancel = cancel or threading.Event()
    hit = cached(index, cache_dir)
    if hit:
        return hit
    name, bid, mlb, os_type = VERSIONS[index]
    d = Path(cache_dir) / "recovery" / str(index)
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)

    session = _query(mr.get_session, SimpleNamespace(verbose=False))
    info = _query(mr.get_image_info, session, bid=bid, mlb=mlb, os_type=os_type)

    cnk = d / os.path.basename(urlparse(info[mr.INFO_SIGN_LINK]).path)
    dmg = d / os.path.basename(urlparse(info[mr.INFO_IMAGE_LINK]).path)
    _download(info[mr.INFO_SIGN_LINK], info[mr.INFO_SIGN_SESS], cnk, lambda a, b: None, cancel)
    _download(info[mr.INFO_IMAGE_LINK], info[mr.INFO_IMAGE_SESS], dmg, lambda a, b: progress(a, b, "download"), cancel)
    verify(dmg, cnk, lambda a, b: progress(a, b, "verify"))

    (d / "hackcheck.json").write_text(json.dumps({
        "version": name, "product": info[mr.INFO_PRODUCT], "files": [dmg.name, cnk.name],
    }), "utf-8")
    return d
