# 🖥️ HackCheck

**Descubra se o seu PC roda macOS.** O HackCheck analisa o hardware, mostra a versão máxima do macOS compatível e guia a criação do pendrive de instalação com OpenCore.

🌐 **Site:** https://vistorill.github.io/hackcheck/

> Projeto open source em desenvolvimento (v0.1). Sem vínculo com a Apple.

## Como funciona

1. **Verifique online.** Digite a CPU e a GPU no site e veja na hora se há chance.
2. **Instale o HackCheck para Windows.** O programa lê o hardware automaticamente e gera o relatório completo. *(em desenvolvimento)*
3. **Crie o pendrive.** Ele gera a EFI (OpCore Simplify), baixa o macOS da Apple (gibMacOS) e prepara o pendrive. *(em desenvolvimento)*

📘 **Guia:** [Como gerar a EFI do seu PC](docs/como-gerar-efi.md) (passo a passo com o OpCore Simplify)

## Estrutura

```
hackcheck/
├─ index.html            # landing page (GitHub Pages)
├─ dashboard/index.html  # dashboard web com análise completa
├─ assets/rules.js       # motor de regras, compartilhado
├─ docs/                 # análises e especificações
├─ desktop/              # programa para Windows (Python + pywebview)
│  ├─ app.py
│  ├─ scanner/           # coleta de hardware
│  ├─ recovery/          # download do recovery (macrecovery do OpenCorePkg)
│  ├─ usbdrive/          # listar e formatar o pendrive
│  ├─ efi/               # validação da EFI
│  ├─ creator.py         # orquestra a criação do pendrive
│  └─ build.ps1          # gera o HackCheck.exe
├─ LICENSE
└─ CONTRIBUTING.md
```

Planejado: `rules/*.json` (regras versionadas) e scanners para Linux e macOS.

## Programa para Windows (desktop/)

App em Python 3.9 + [pywebview](https://pywebview.flowrl.com/) que abre a dashboard numa janela e lê o hardware automaticamente.

```bash
cd desktop
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python app.py
```

Gerar o executável (`desktop\dist\HackCheck.exe`):

```bash
powershell -ExecutionPolicy Bypass -File desktop\build.ps1
```

Ao enviar uma tag `v*` (ex.: `v0.1.0`), o GitHub Actions gera o `.exe` e publica em **Releases**.

## Rodar o site localmente

São só arquivos estáticos. Abra o `index.html` no navegador ou sirva a pasta:

```bash
python -m http.server 8000
```

## Roadmap

- [x] Dashboard web com motor de regras e scanner via PowerShell
- [x] Landing page
- [x] v0.1: programa para Windows com scanner automático
- [x] v0.2: assistente de criação do pendrive (recovery da Apple + EFI escolhida pelo usuário)
- [x] v0.3: geração guiada da EFI com OpCore Simplify e busca de EFIs da comunidade
- [ ] v0.4: geração da EFI sem interação (sem o console do OpCore Simplify)
- [ ] Regras em JSON com testes
- [ ] Banco de EFIs da comunidade, Linux, inglês e espanhol

## Contribuindo

Veja o [CONTRIBUTING.md](CONTRIBUTING.md).

## Aviso

Projeto educacional. O contrato de licença da Apple restringe o macOS a hardware da Apple. O HackCheck nunca distribui o macOS: o instalador é baixado direto da Apple. Use por sua conta e risco.

Licença: [MIT](LICENSE).
