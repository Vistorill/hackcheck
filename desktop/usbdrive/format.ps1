# Formata um pendrive para o HackCheck: GPT + uma partição FAT32 de até 16 GB.
# Roda elevado (UAC). Revalida o disco antes de apagar e grava o resultado em JSON.
param(
    [Parameter(Mandatory)][int]$Number,
    [Parameter(Mandatory)][string]$UniqueId,
    [Parameter(Mandatory)][long]$Size,
    [Parameter(Mandatory)][string]$ResultFile,
    [string]$Label = 'HACKCHECK'
)
$ErrorActionPreference = 'Stop'

function Done($ok, $msg, $letter) {
    [ordered]@{ ok = $ok; message = $msg; letter = $letter } | ConvertTo-Json -Compress |
        Out-File -Encoding utf8 -FilePath $ResultFile
    exit ([int](-not $ok))
}

try {
    $d = Get-Disk -Number $Number
    # Nunca apaga um disco que não seja exatamente o escolhido, nem disco do sistema.
    if ($d.UniqueId -ne $UniqueId -or $d.Size -ne $Size) { Done $false 'O disco não corresponde ao pendrive escolhido.' $null }
    if ($d.BusType -ne 'USB') { Done $false 'O disco não é USB.' $null }
    if ($d.IsSystem -or $d.IsBoot) { Done $false 'Disco do sistema: operação bloqueada.' $null }

    # FAT32 é limitado a 32 GB nas ferramentas do Windows; 16 GB sobra para EFI + recovery.
    $partSize = [math]::Min($Size - 64MB, 16GB)
    $letter = $null
    try {
        if ($d.IsOffline) { Set-Disk -Number $Number -IsOffline $false }
        if ($d.PartitionStyle -ne 'RAW') { Clear-Disk -Number $Number -RemoveData -RemoveOEM -Confirm:$false }
        Initialize-Disk -Number $Number -PartitionStyle GPT
        $p = New-Partition -DiskNumber $Number -Size $partSize -AssignDriveLetter
        $null = $p | Format-Volume -FileSystem FAT32 -NewFileSystemLabel $Label -Confirm:$false -Force
        $letter = [string](Get-Partition -DiskNumber $Number -PartitionNumber $p.PartitionNumber).DriveLetter
    } catch {
        # Alternativa com diskpart (alguns pendrives rejeitam os cmdlets de Storage).
        $mb = [math]::Floor($partSize / 1MB)
        $script = "select disk $Number`nclean`nconvert gpt`ncreate partition primary size=$mb`nformat fs=fat32 quick label=$Label`nassign`n"
        $tmp = [IO.Path]::GetTempFileName()
        Set-Content -Path $tmp -Value $script -Encoding ASCII
        $out = diskpart /s $tmp | Out-String
        Remove-Item $tmp
        Start-Sleep 2
        $letter = [string](Get-Partition -DiskNumber $Number | ?{ $_.DriveLetter } | Select -First 1).DriveLetter
        if (-not $letter) { Done $false ("Falha ao formatar: " + $_.Exception.Message + " | diskpart: " + $out.Trim()) $null }
    }
    if (-not $letter) { Done $false 'Formatado, mas o Windows não atribuiu letra ao pendrive.' $null }
    Done $true 'ok' $letter
} catch {
    Done $false $_.Exception.Message $null
}
