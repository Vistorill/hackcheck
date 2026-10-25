# Como contribuir

Obrigado por ajudar o HackCheck!

## Relatar um resultado de instalação

Abra uma issue com:
- o JSON gerado pelo scanner (na dashboard);
- o veredito que o HackCheck deu;
- o que aconteceu de verdade (instalou? o que não funcionou?);
- a versão do macOS e do OpenCore.

## Corrigir ou adicionar regras

As regras ficam em `assets/rules.js` (funções `cpuR`, `gpuR`, `netR`, `audR`, `dskR`).

1. Faça um fork e crie um branch.
2. Altere a regra e teste na dashboard (botões de exemplo e o seu JSON).
3. Abra um pull request **citando a fonte**: guia Dortania, documentação de kext ou relato de teste.

## Estilo

- Mensagens para o usuário em português, curtas e diretas.
- Não adicione dependências externas no site: ele precisa funcionar como arquivos estáticos.
