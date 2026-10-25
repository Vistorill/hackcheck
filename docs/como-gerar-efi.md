# Como gerar a EFI do seu PC com o HackCheck

A **EFI** é a pasta do OpenCore que faz o PC dar boot no macOS. Ela leva os drivers (kexts) e as configurações da combinação **exata** do seu processador, placa-mãe, placa de vídeo, rede e áudio. Por isso não existe uma EFI "universal" para baixar: ela precisa ser gerada para o seu PC.

O HackCheck faz isso com o [OpCore Simplify](https://github.com/lzhoang2801/OpCore-Simplify) e depois confere se a EFI tem tudo o que o seu hardware precisa.

> ⏱️ Leva de 5 a 15 minutos. Você precisa de internet.

---

## Antes de começar

1. Baixe e abra o [HackCheck.exe](https://github.com/Vistorill/hackcheck/releases/latest/download/HackCheck.exe).
   Se o Windows mostrar *"O Windows protegeu o computador"*, clique em **Mais informações → Executar assim mesmo**.
2. Espere o **scan do hardware** terminar no **Painel**. O veredito precisa ser *aprovado* ou *aprovado com ressalvas*.
3. Vá para a aba **💾 Criar pendrive**.
4. No **passo 2**, confira a versão do macOS. O recomendado é o **Sequoia 15**. **Anote a versão escolhida**, porque você vai usar a mesma no OpCore Simplify.

---

## Passo a passo

### 1. Abra o gerador
No **passo 3** do assistente, deixe marcada a opção **"Gerar a EFI para este PC"** e clique em **⚙️ Gerar EFI para este PC**.

O HackCheck baixa o OpCore Simplify e abre uma **janela preta** (o console dele). Todos os passos abaixo acontecem **nessa janela**.

### 2. Tela "Check for Updates"
Se aparecer:
```
Do you want to skip the update process? (yes/No):
```
Digite **`yes`** e Enter. O HackCheck já baixou a versão mais recente.

Se ele perguntar sobre **instalar o Python**, digite **`y`** e Enter.

### 3. Menu principal: selecione o relatório de hardware
```
  Hardware Report: Not selected

1. Select Hardware Report
...
6. Build OpenCore EFI
```
Digite **`1`** e Enter.

### 4. Leia o hardware do PC
Quando ele pedir o caminho do relatório, digite **`E`** e Enter.
Ele baixa o *Hardware Sniffer* e lê o seu PC. Aguarde.

Na tela de **compatibilidade**, confira o resultado e pressione **Enter**.

### 5. Escolha a versão do macOS
```
   23. macOS Sonoma 14
   24. macOS Sequoia 15
   25. macOS Tahoe 26

Please enter the macOS version you want to use (default: macOS Tahoe 26):
```
Digite o **número da mesma versão escolhida no HackCheck** e Enter. Para o Sequoia 15, é **`24`**.

> ⚠️ **Não aperte só Enter aqui.** O padrão costuma ser o Tahoe 26, que **não tem som** em placas Realtek (a Apple removeu o driver de áudio) e tem problemas com placas de vídeo AMD.

### 6. Modo UEFI
Se aparecer:
```
*** BIOS Firmware Type is not UEFI
Build EFI for UEFI? (Yes/no):
```
Digite **`yes`** e Enter. O aviso aparece quando o Windows foi instalado no modo antigo (Legacy). O OpenCore funciona melhor em UEFI. Veja a seção [Atenção: Windows em modo Legacy](#atenção-windows-em-modo-legacy).

### 7. Layout de áudio (Codec Layout ID)
```
ID   Comment
11   Custom ALC897 by Sergey_Galan  for GIGABYTE Z590M
...
Enter the ID of the codec layout you want to use (default: 22):
```
Escolha um layout **para o seu chip de áudio e para placa desktop** (ou notebook, se for o caso). **Não aceite o padrão sem ler o comentário**: às vezes ele é de outro chip ou de um notebook.

| Chip de áudio | Layouts para testar primeiro (desktop) |
|---|---|
| ALC897 | 11, 12, 98, 66 |
| ALC887 / ALC888 | 1, 7, 11 |
| ALC892 | 1, 7, 12 |
| ALC1220 | 1, 7, 11 |

Se depois da instalação não sair som, dá para trocar o número no boot-arg `alcid=` do `config.plist`, sem gerar a EFI de novo.

### 8. Outras perguntas
Nas demais telas (ACPI, kexts, SMBIOS), pressione **Enter** para aceitar o padrão.

### 9. Confira o menu e gere a EFI
De volta ao menu principal, o topo deve mostrar o seu hardware:
```
  Hardware Report: ...\SysReport\Report.json
  macOS Version:   macOS Sequoia 15
  SMBIOS:          iMacPro1,1
```
Confira se a **versão do macOS** é a mesma escolhida no HackCheck. Depois digite **`6`** (*Build OpenCore EFI*) e Enter.

Ele baixa o OpenCore e os drivers. Aguarde alguns minutos, até aparecer **"OpenCore EFI build complete"**.

### 10. Tela "Before Using EFI": anote os ajustes da BIOS
```
* BIOS/UEFI Settings Required:
    - Enable UEFI mode (disable Legacy/CSM)
    - Enable Above 4G Decoding
    - Disable Resizable BAR/Smart Access Memory
```
📸 **Tire um print ou anote.** Você vai precisar desses ajustes para dar boot no pendrive.

A parte de **USB Mapping** é feita **depois** de instalar o macOS. Não remova o `UTBDefault.kext` agora.

Pressione **Enter**. A pasta *Results* abre sozinha. Na tela **"Result"**, pressione **Enter** de novo. Pode fechar a janela.

### 11. Volte ao HackCheck
O HackCheck detecta a EFI sozinho e mostra no **passo 3**:
- ✅ **"EFI válida para o Sequoia 15"**;
- a tabela **"Drivers para o seu hardware"**, com cada driver marcado como *Incluído*, *Faltando*, *Remover* ou *Opcional*.

Pronto: siga para o **passo 4** (escolher o pendrive).

---

## Se algo der errado

Clique em **📋 Copiar relatório da EFI** e cole o texto ao pedir ajuda (por exemplo, em uma [issue no GitHub](https://github.com/Vistorill/hackcheck/issues)). O histórico das validações fica em `%LOCALAPPDATA%\HackCheck\logs\validacao-efi.log`.

| Mensagem no HackCheck | O que fazer |
|---|---|
| **"EFI incompleta: o config.plist ainda é o exemplo do OpenCore"** | A geração não terminou. Volte à janela do OpCore Simplify e conclua a opção **6**. Se ela mostrou um erro, copie o texto dele. |
| **"O SMBIOS ... não é aceito por esta versão do macOS"** | A versão escolhida no OpCore Simplify é diferente da do HackCheck. Use a mesma nos dois e gere de novo. |
| **"Falta ... (Rede)"** | Sem driver de rede, o instalador não consegue baixar o macOS. Gere de novo ou adicione o kext indicado. |
| **"Remova WhateverGreen"** (Tahoe) | No Tahoe esse driver causa kernel panic com GPUs AMD. Prefira o Sequoia ou remova o kext. |
| **"Falta agdpmod=pikera"** | Placas AMD RX 5000/6000 costumam dar tela preta sem esse boot-arg. Adicione-o em `boot-args` no `config.plist`. |
| A janela do OpCore Simplify fechou sozinha | Clique em **Gerar EFI** de novo. A EFI anterior fica guardada em `Results-anterior`. |

### Já gerei a EFI e reabri o HackCheck
**Não clique em "Gerar EFI" de novo.** Escolha **"Usar uma EFI que já tenho"**, clique em **Escolher pasta EFI** e cole na barra de endereço:
```
%LOCALAPPDATA%\HackCheck\tools\OpCore-Simplify-main\Results\EFI
```

---

## Atenção: Windows em modo Legacy

Se o OpCore Simplify avisou *"BIOS Firmware Type is not UEFI"*, o seu Windows está em modo **Legacy** (disco MBR). Para dar boot no pendrive você vai **desativar o CSM** na BIOS, e com o CSM desativado **esse Windows não inicia**. Para voltar a ele, basta **reativar o CSM**: nada é apagado.

## Atenção: onde instalar o macOS

A instalação do macOS **apaga o disco escolhido**. Se o seu PC só tem um SSD, com o Windows, use um **segundo SSD ou HD** para o macOS, ou faça backup de tudo antes.

---

## Outras opções do passo 3

- **Usar uma EFI que já tenho**: para quem já tem uma EFI pronta. O HackCheck valida da mesma forma.
- **Procurar EFIs prontas da comunidade**: abre buscas no GitHub com o modelo da sua placa-mãe, o chipset e a CPU. Só use uma EFI de outra pessoa se o hardware for **igual** ao seu, se ela for recente (OpenCore 1.0.x) e **nunca com o número de série de outra pessoa**.

## Referências
- [OpCore Simplify](https://github.com/lzhoang2801/OpCore-Simplify)
- [Guia Dortania: OpenCore Install Guide](https://dortania.github.io/OpenCore-Install-Guide/)
- [Guia Dortania: macOS 26 Tahoe](https://dortania.github.io/OpenCore-Install-Guide/extras/tahoe.html)
- [AppleALC: lista de layouts por codec](https://github.com/acidanthera/AppleALC/wiki/Supported-codecs)
