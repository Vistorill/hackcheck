# Gera desktop\dist\HackCheck.exe
# Uso (na pasta desktop):  powershell -ExecutionPolicy Bypass -File build.ps1
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not (Test-Path .venv)) {
    python -m venv .venv
    .venv\Scripts\python -m pip install --upgrade pip
    .venv\Scripts\python -m pip install -r requirements.txt
}

.venv\Scripts\pyinstaller app.py `
    --name HackCheck `
    --onefile `
    --windowed `
    --noconfirm `
    --clean `
    --add-data "..\dashboard;dashboard" `
    --add-data "..\assets;assets" `
    --add-data "usbdrive\format.ps1;usbdrive" `
    --add-data "recovery\LICENSE-OpenCorePkg.txt;recovery"

if ($LASTEXITCODE -ne 0) { throw "Falha no PyInstaller (código $LASTEXITCODE)" }
Write-Host "Pronto: $PSScriptRoot\dist\HackCheck.exe"
