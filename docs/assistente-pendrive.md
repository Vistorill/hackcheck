# Assistente de instalação e criação do pendrive: análise e especificação

> Pesquisa feita em outubro de 2026. O cenário Hackintosh muda a cada versão do macOS: revise antes de cada release.

## 1. O que a pesquisa mudou no projeto

### 1.1 Tahoe 26 não deve ser o padrão
O macOS 26 Tahoe é o último para PCs (o 27 é só para Apple Silicon), mas trouxe quebras importantes:

| Problema no Tahoe | Impacto | Fonte |
|---|---|---|
| **AppleHDA removido** | AppleALC para de funcionar: **sem som na saída analógica** (fone, caixas). HDMI/DP/USB funcionam. | Dortania |
| **Broadcom Wi-Fi** | Removido desde o Sonoma. No Tahoe só com AppleBCMWLANCompanion, **experimental**, exige VT-d e **não funciona em AMD**. | Dortania |
| **WhateverGreen** | Problemas com GPUs AMD; a recomendação atual é remover o kext. | Dortania |
| **Bluetooth Intel** | Precisa do boot-arg `-ibtcompatbeta`. | Dortania |
| **OCLP** | O oficial não suporta Tahoe; só um fork (lzhoang2801, 3.0.0). | OpCore Simplify |

**Decisão:** o assistente recomenda **Sequoia 15 por padrão** e oferece o Tahoe como opção avançada, mostrando o que se perde no hardware detectado (por exemplo: "seu áudio Realtek não terá som no fone").

### 1.2 Correções no motor de regras (`assets/rules.js`)
- **Broadcom Wi-Fi não é mais "suporte nativo"**: no Sequoia exige patch do OCLP; no Tahoe é experimental.
- **Áudio Realtek no Tahoe**: sem som analógico.
- **GPU**: RX 6650 XT e 6950 XT precisam de spoof; RX 6700/6700 XT/6750 XT dependem do NootRX e não funcionam 100%; RX 580 2048SP precisa de flash de VBIOS.
- **iGPU AMD (APU Ryzen 1000–5000)**: funciona com NootedRed, não é "sem suporte".
- **Core Ultra 200S (Arrow Lake)**: funciona com ajustes, não deve ser reprovado de cara.
- **Ethernet**: Intel I225-V e I226-V precisam de ajuste; Realtek L8200A não funciona.
- **NVMe**: incluir SK Hynix PC711 e Intel 600p na lista de discos a evitar.
- **Wi-Fi Realtek, MediaTek e adaptadores USB**: sem driver.

## 2. Estratégia de criação do pendrive no Windows

### 2.1 Instalador online (recovery) como padrão
No Windows não há como montar o instalador completo, porque faltam os drivers APFS/HFS. O caminho oficial da Dortania é o **pendrive de recovery**:

- `macrecovery.py` (OpenCorePkg) baixa o `BaseSystem.dmg` e o `.chunklist` **direto dos servidores da Apple**.
- O pendrive leva só a EFI e a pasta `com.apple.recovery.boot`, com cerca de 1 a 2 GB.
- **A instalação baixa o macOS pela internet**, então **é obrigatória uma Ethernet suportada pela EFI**, porque o Wi-Fi quase nunca funciona no instalador. O assistente precisa checar isso e avisar.

O instalador offline (UnPlugged) exige rodar um script no Terminal do recovery e tem limitações no Sonoma+. Fica como opção avançada no futuro.

### 2.2 IDs de placa para o macrecovery
| macOS | Board ID | Argumentos extras |
|---|---|---|
| Ventura 13 | `Mac-4B682C642B45593E` | |
| Sonoma 14 | `Mac-226CB3C6A851A671` | |
| Sequoia 15 | `Mac-7BA5B2D9E42DDD94` (recovery_urls.txt) ou `Mac-937A206F2EE63C01` (guia) | |
| Tahoe 26 | `Mac-CFF7D910A743CAAF` | `-os latest` |

Sempre `-m 00000000000000000`. **Validar contra o `recovery_urls.txt` do OpenCorePkg a cada release.**

O `macrecovery.py` usa só a biblioteca padrão do Python (urllib) e tem licença BSD. Dá para **embutir no executável** e chamar como módulo, sem o usuário instalar Python.

### 2.3 Versões de referência (outubro de 2026)
- **OpenCore 1.0.8** (27/09/2026). A 1.0.7 melhorou o `XhciPortLimit` no Tahoe.
- Baixar sempre a versão **RELEASE** da API do GitHub (`/repos/acidanthera/OpenCorePkg/releases/latest`).

### 2.4 Formatação: GPT + FAT32, partição de 16 GB no máximo
- **GPT**: a Dortania avisa que MBR falha em vários cenários.
- **FAT32 tem limite de 32 GB** nas ferramentas do Windows (`diskpart`, `Format-Volume`). Solução: **criar uma partição de 16 GB** (ou do tamanho do pendrive, se for menor). Assim nunca bate no limite e não precisa de Rufus.
- O espaço restante fica livre. No futuro pode virar uma partição exFAT para o instalador offline.

## 3. Ferramentas da comunidade e papel de cada uma

| Ferramenta | Uso no HackCheck | Licença | Integração |
|---|---|---|---|
| **OpenCorePkg** (acidanthera) | Bootloader e `macrecovery.py` | BSD-3 | Download automático da release |
| **OpCore Simplify** (lzhoang2801) | Gera a EFI a partir do hardware | BSD-3 | v0.2: roda em console visível. A EFI sai em `Results/EFI` |
| **Hardware Sniffer** (lzhoang2801) | Relatório de hardware e dump ACPI usado pelo OpCore Simplify | — | Chamado pelo OpCore Simplify (`-e -o SysReport`) |
| **USBToolBox** | Mapeamento de USB pós-instalação | — | Guia |
| **OCLP (fork lzhoang2801)** | Root patches (Wi-Fi Broadcom, GPUs antigas) | — | Guia pós-instalação |
| **ProperTree** | Editar o config.plist | BSD-3 | Guia |
| **AppleBCMWLANCompanion** | Broadcom no Sequoia/Tahoe sem root patch | — | Kext, experimental |
| **VoodooHDA** | Áudio no Tahoe (qualidade menor) | — | Opcional |
| **UnPlugged** (corpnewt) | Instalador offline a partir do recovery | — | Futuro |

O OpCore Simplify é **interativo** (menus com `input()`). A função `build_opencore_efi()` não pede entradas, mas depende de estado montado nas etapas anteriores. Integrar programaticamente é possível, mas frágil entre versões. **Plano:** na v0.2 abrir o OpCore Simplify em uma janela de console guiada e detectar o `Results/EFI` gerado. Na v1, avaliar a integração direta.

## 4. Fluxo do assistente (aba "Criar pendrive")

```
1. Pré-checagem ─ 2. macOS ─ 3. EFI ─ 4. Pendrive ─ 5. Confirmar ─ 6. Criar ─ 7. Próximos passos
```

### Passo 1: Pré-checagem (automática)
- Veredito do scanner: bloqueia se estiver **reprovado**.
- **Ethernet compatível detectada?** Se não houver, bloqueia, com a explicação de que o instalador online precisa de cabo.
- Internet funcionando (teste no servidor da Apple).
- Espaço livre: pelo menos 5 GB em `%LOCALAPPDATA%\HackCheck`.
- Notebook detectado: aviso extra.

### Passo 2: Escolha do macOS
- Lista só as versões permitidas pelo hardware (o `mx` do motor de regras).
- **Sequoia pré-selecionado**, com o selo "Recomendado".
- O Tahoe mostra perdas personalizadas: "Áudio Realtek: sem som no fone", "Wi-Fi Broadcom: experimental".

### Passo 3: EFI
Duas opções:
- **Gerar automaticamente** (padrão): o HackCheck baixa o OpCore Simplify, abre o console e orienta o usuário (escolher o relatório "E", a versão do passo 2 e "Build"). Depois detecta `Results/EFI`.
- **Usar uma EFI que já tenho**: seletor de pasta.

**Validação da EFI** (nas duas opções):
- existem `EFI/BOOT/BOOTx64.efi`, `EFI/OC/OpenCore.efi` e `EFI/OC/config.plist`;
- o `config.plist` é um plist válido (`plistlib`);
- os kexts listados no `config.plist` existem em `EFI/OC/Kexts`;
- avisa se a Ethernet detectada não tem kext (IntelMausi, LucyRTL8125, RealtekRTL8111...).

### Passo 4: Escolher o pendrive (input)
Um **seletor** com os discos de `Get-Disk | Where BusType -eq 'USB'`, mostrando **modelo, tamanho, letra(s) e rótulo**. Tem o botão **"Atualizar lista"**.

**Regras de segurança:**
- **Nunca listar** discos com `IsSystem` ou `IsBoot`, nem discos que não sejam USB.
- Tamanho entre **4 GB e 256 GB**. Acima de 64 GB, mostrar o aviso "isto parece um HD externo".
- Guardar o **`UniqueId` + número de série + tamanho** do disco escolhido, e não só o número.

### Passo 5: Confirmação
- Resumo: macOS, EFI, pendrive (modelo e tamanho).
- O usuário precisa **digitar o tamanho mostrado** (por exemplo "29,8 GB") ou a palavra **APAGAR** para liberar o botão **"Criar pendrive"**.

### Passo 6: Criação (barra de progresso por etapa)
A ordem foi pensada para **o pendrive só ser apagado quando tudo estiver pronto**:

1. **Baixar o recovery** (macrecovery) para o cache, com progresso em %. Pula se já estiver em cache.
2. **Verificar o recovery** pelo `.chunklist` (o macrecovery já verifica).
3. **Revalidar o disco**: o `UniqueId`, a serial e o tamanho ainda batem? O pendrive pode ter sido trocado.
4. **Formatar**, com **elevação de administrador só nesta etapa** (UAC). Um script PowerShell separado faz:
   ```powershell
   Clear-Disk -Number $n -RemoveData -RemoveOEM -Confirm:$false
   Initialize-Disk -Number $n -PartitionStyle GPT
   New-Partition -DiskNumber $n -Size $size -AssignDriveLetter |
     Format-Volume -FileSystem FAT32 -NewFileSystemLabel HACKCHECK -Confirm:$false
   ```
   Fallback com `diskpart` (`clean`, `convert gpt`, `create partition primary size=`, `format fs=fat32 quick label=HACKCHECK`, `assign`).
5. **Copiar** `com.apple.recovery.boot/` (`.dmg` + `.chunklist`) e `EFI/` para a raiz.
6. **Verificar a cópia** comparando o tamanho e o hash de cada arquivo.
7. **Ejetar com segurança.**

Se falhar: mensagem clara, log salvo em `%LOCALAPPDATA%\HackCheck\logs` e a opção "Tentar de novo" (o recovery fica em cache).

### Passo 7: Próximos passos (personalizado)
- **BIOS**: checklist gerado do hardware (CSM off, Secure Boot off, Above 4G on, VT-d off ou DisableIoMapper, XHCI Hand-off on, CFG Lock off se existir). O `check_bios_requirements()` do OpCore Simplify também gera itens específicos.
- **Boot**: tecla do menu de boot por fabricante (ASUS F8, Gigabyte F12, MSI F11, ASRock F11...).
- **Instalação**: Utilitário de Disco → apagar como APFS/GUID → Reinstalar (com cabo de rede).
- **Pós-instalação**: copiar a EFI para o SSD, mapear USB (USBToolBox), gerar SMBIOS único, OCLP se necessário.
- **Problemas comuns** (Dortania): travou em `EndRandomSeed` ou `EXITBS:START` → quirks/CFG Lock; `Buffer Too Small` → ativar Above 4G; "Waiting for Root Device" → mapeamento USB ou SATA; `This version of Mac OS X is not supported` → SMBIOS antigo.

## 5. Arquitetura no app desktop

```
desktop/
├─ app.py               # janela + API exposta à dashboard
├─ scanner/windows.py   # já existe
├─ usb/
│  ├─ disks.py          # lista e revalida pendrives (Get-Disk, sem admin)
│  ├─ format.ps1        # formatação (roda elevado)
│  └─ writer.py         # orquestra: download → revalida → formata → copia → verifica
├─ recovery/
│  ├─ macrecovery.py    # vendorizado do OpenCorePkg (BSD-3)
│  └─ versions.py       # tabela de board IDs
├─ efi/
│  ├─ opcore.py         # baixa e abre o OpCore Simplify, detecta Results/EFI
│  └─ validate.py       # valida a estrutura e o config.plist
└─ jobs.py              # tarefas em segundo plano com progresso para a UI
```

**Comunicação com a UI**: as tarefas longas rodam em uma thread. A UI consulta `api.job_status(id)` a cada 500 ms (percentual, etapa atual, log), e `api.cancel(id)` cancela antes da formatação.

**Elevação**: o app roda **sem admin**. Só a formatação chama `format.ps1` com `Start-Process -Verb RunAs`, passando o número do disco e o `UniqueId` esperado. O script **revalida o disco por conta própria** antes de apagar.

## 6. Roadmap de implementação

| Versão | Entrega |
|---|---|
| **0.2** | Correções no `rules.js` (seção 1.2); seletor de pendrive; download do recovery; formatação; cópia de uma **EFI escolhida pelo usuário**; validação da EFI |
| **0.3** | Integração com o OpCore Simplify (geração da EFI); checklist de BIOS personalizado |
| **0.4** | Pós-instalação guiada; logs; relatório para issue |
| **Futuro** | Instalador offline (UnPlugged); Linux; banco de EFIs da comunidade |

## Fontes
- [Dortania: Criando o pendrive no Windows](https://dortania.github.io/OpenCore-Install-Guide/installer-guide/windows-install.html)
- [Dortania: macOS 26 Tahoe](https://dortania.github.io/OpenCore-Install-Guide/extras/tahoe.html)
- [Dortania: Kernel issues (troubleshooting)](https://dortania.github.io/OpenCore-Install-Guide/troubleshooting/extended/kernel-issues.html)
- [OpenCorePkg: recovery_urls.txt](https://github.com/acidanthera/OpenCorePkg/blob/master/Utilities/macrecovery/recovery_urls.txt)
- [OpenCorePkg: releases](https://github.com/acidanthera/OpenCorePkg/releases)
- [OpCore Simplify](https://github.com/lzhoang2801/OpCore-Simplify)
- [UnPlugged (corpnewt)](https://github.com/corpnewt/UnPlugged)
- [Hackintosh Hardware Compatibility, setembro de 2026 (chaosyn)](https://blog.chaosyn.com/en/posts/hackintosh-hardware-compatibility-2026-09/)
- [tonymacx86: macOS 26 Tahoe com OpenCore 1.0.5](https://www.tonymacx86.com/threads/howto-macos-26-tahoe-with-opencore-1-0-5-z390-i9-9900-rx-6600-xt.332345/)
- [Pureinfotech: limite de 32 GB do FAT32 no Windows](https://pureinfotech.com/format-drive-fat32-windows/)
