param(
    [string]$TargetPython = "",
    [switch]$InstallCoreDeps
)

$ErrorActionPreference = "Stop"

function Resolve-Python312 {
    param([string]$Explicit)

    if ($Explicit) {
        if (-not (Test-Path $Explicit)) {
            throw "Angegebener Python-Pfad existiert nicht: $Explicit"
        }
        return (Resolve-Path $Explicit).Path
    }

    $candidates = @(
        "C:\Python312\python.exe",
        "C:\Program Files\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    throw "Python 3.12 wurde nicht gefunden. Installiere Python 3.12 und starte dieses Script erneut mit -TargetPython <pfad\\python.exe>."
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Resolve-Path (Join-Path $scriptRoot "..")).Path
$venvPath = Join-Path $projectRoot ".venv-chat"
$python312 = Resolve-Python312 -Explicit $TargetPython

Write-Host "Nutze Python: $python312"

if (-not (Test-Path $venvPath)) {
    & $python312 -m venv $venvPath
    Write-Host "Virtuelle Umgebung erstellt: $venvPath"
} else {
    Write-Host "Virtuelle Umgebung existiert bereits: $venvPath"
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
& $venvPython -m pip install --upgrade pip setuptools wheel

if ($InstallCoreDeps.IsPresent) {
    & $venvPython -m pip install -r (Join-Path $projectRoot "requirements.txt")
    & $venvPython -m pip install onnxruntime-gpu
    Write-Host "Core-Abhaengigkeiten installiert."
}

Write-Host "Fertig. Backend-Interpreter: $venvPython"
