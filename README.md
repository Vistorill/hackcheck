# 🖥️ HackCheck

**Descubra se o seu PC roda macOS.** O HackCheck analisa o hardware, mostra a versão máxima do macOS compatível e guia a criação do pendrive de instalação com OpenCore.

🌐 **Site:** https://vistorill.github.io/hackcheck/

> Projeto open source em desenvolvimento (v0.1). Sem vínculo com a Apple.

## Como funciona

1. **Verifique online.** Digite a CPU e a GPU no site e veja na hora se há chance.
2. **Instale o HackCheck para Windows.** O programa lê o hardware automaticamente e gera o relatório completo. *(em desenvolvimento)*
3. **Crie o pendrive.** Ele gera a EFI (OpCore Simplify), baixa o macOS da Apple (gibMacOS) e prepara o pendrive. *(em desenvolvimento)*

## Estrutura

```
hackcheck/
├─ index.html            # landing page (GitHub Pages)
├─ dashboard/index.html  # dashboard web com análise completa
├─ assets/rules.js       # motor de regras, compartilhado
├─ LICENSE
└─ CONTRIBUTING.md
```

Planejado: `rules/*.json` (regras versionadas), `scanner/` (coleta de hardware) e `desktop/` (programa em Python + pywebview).

## Rodar localmente

São só arquivos estáticos. Abra o `index.html` no navegador ou sirva a pasta:

```bash
python -m http.server 8000
```

## Roadmap

- [x] Dashboard web com motor de regras e scanner via PowerShell
- [x] Landing page
- [ ] v0.1: programa para Windows com scanner automático
- [ ] v0.2: geração da EFI com OpCore Simplify
- [ ] v0.3: criação do pendrive (gibMacOS)
- [ ] Regras em JSON com testes
- [ ] Banco de EFIs da comunidade, Linux, inglês e espanhol

## Contribuindo

Veja o [CONTRIBUTING.md](CONTRIBUTING.md).

## Aviso

Projeto educacional. O contrato de licença da Apple restringe o macOS a hardware da Apple. O HackCheck nunca distribui o macOS: o instalador é baixado direto da Apple. Use por sua conta e risco.

Licença: [MIT](LICENSE).
