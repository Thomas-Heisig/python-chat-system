param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [string]$BackendHost = "0.0.0.0",
    [string]$FrontendHost = "0.0.0.0",
    [switch]$NoReload,
    [switch]$StopExisting
)

$ErrorActionPreference = "Stop"

function Assert-CommandAvailable {
    param([string]$CommandName)
    if (-not (Get-Command $CommandName -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $CommandName"
    }
}

function Resolve-ShellExecutable {
    foreach ($candidate in @("pwsh", "powershell")) {
        if (Get-Command $candidate -ErrorAction SilentlyContinue) {
            return $candidate
        }
    }

    throw "Required shell not found. Expected 'pwsh' or 'powershell'."
}

function Resolve-NpmCommand {
    $npmCommand = Get-Command "npm" -ErrorAction SilentlyContinue
    if ($null -eq $npmCommand) {
        throw "Required command not found: npm"
    }

    $npmDir = Split-Path -Parent $npmCommand.Source
    $npmCmd = Join-Path $npmDir "npm.cmd"
    if (Test-Path $npmCmd) {
        return $npmCmd
    }

    return $npmCommand.Source
}

function Resolve-BackendPython {
    param([string]$ProjectRoot)

    $candidates = @(
        (Join-Path $ProjectRoot ".venv-chat\Scripts\python.exe"),
        (Join-Path $ProjectRoot ".venv-training\Scripts\python.exe"),
        (Join-Path $ProjectRoot ".venv\Scripts\python.exe")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        return "python"
    }

    throw "Required Python runtime not found. Erwartet wurde .venv-chat, .venv-training, .venv oder ein globales 'python'."
}

function Test-PortInUse {
    param([int]$Port)
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $Port)
        $listener.Start()
        $listener.Stop()
        return $false
    }
    catch {
        return $true
    }
}

function Get-PidsByPort {
    param([int]$Port)

    $pids = @()
    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($connections) {
        $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    }

    return @($pids | Where-Object { $_ -and $_ -gt 0 } | Select-Object -Unique)
}

function Test-ProcessAlive {
    param([int]$ProcessId)

    $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
    return $null -ne $proc
}

function Stop-ProcessRobust {
    param([int]$ProcessId, [string]$Name, [int]$Port)

    try {
        Stop-Process -Id $ProcessId -Force -ErrorAction Stop
        Wait-Process -Id $ProcessId -Timeout 2 -ErrorAction SilentlyContinue
    }
    catch {
    }

    if (-not (Test-ProcessAlive -ProcessId $ProcessId)) {
        Write-Host "$Name process stopped (PID=$ProcessId, Port=$Port)."
        return $true
    }

    taskkill /PID $ProcessId /F | Out-Null
    if ($LASTEXITCODE -eq 0 -and -not (Test-ProcessAlive -ProcessId $ProcessId)) {
        Write-Host "$Name process force-stopped via taskkill (PID=$ProcessId, Port=$Port)."
        return $true
    }

    $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
    if ($null -ne $proc) {
        $termination = $proc | Invoke-CimMethod -MethodName Terminate -ErrorAction SilentlyContinue
        if ($termination -and $termination.ReturnValue -eq 0 -and -not (Test-ProcessAlive -ProcessId $ProcessId)) {
            Write-Host "$Name process force-stopped via CIM terminate (PID=$ProcessId, Port=$Port)."
            return $true
        }
    }

    Write-Warning "Konnte $Name process mit PID=$ProcessId auf Port $Port nicht beenden."
    return $false
}

function Stop-ProcessesByPort {
    param([int]$Port, [string]$Name)

    for ($attempt = 1; $attempt -le 4; $attempt++) {
        $pids = Get-PidsByPort -Port $Port
        if ($pids.Count -eq 0) {
            return $true
        }

        $allStopped = $true
        foreach ($procId in $pids) {
            $stopped = Stop-ProcessRobust -ProcessId $procId -Name $Name -Port $Port
            if (-not $stopped) {
                $allStopped = $false
            }
        }

        if ($allStopped) {
            Start-Sleep -Milliseconds 400
        }
    }

    if (Test-PortInUse -Port $Port) {
        $remaining = Get-PidsByPort -Port $Port
        if ($remaining.Count -gt 0) {
            Write-Warning "$Name-Port $Port ist weiter belegt durch PID(s): $($remaining -join ', ')."
        }
        else {
            Write-Warning "$Name-Port $Port ist weiter belegt."
        }
        return $false
    }

    return $true
}

function Wait-BackendReady {
    param(
        [string]$BackendHostName,
        [int]$Port,
        [int]$TimeoutSeconds = 30
    )

    $healthUrl = "http://127.0.0.1:$Port/api/health/live"
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $healthUrl -Method Get -TimeoutSec 3 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                return $true
            }
        }
        catch {
        }

        Start-Sleep -Milliseconds 500
    }

    return $false
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Resolve-Path (Join-Path $scriptRoot "..")).Path
$frontendRoot = Join-Path $projectRoot "frontend"

Assert-CommandAvailable -CommandName "npm"

$reloadFlag = "--reload"
if ($NoReload.IsPresent) {
    $reloadFlag = ""
}

$backendPython = Resolve-BackendPython -ProjectRoot $projectRoot
$backendCommand = "Set-Location '$projectRoot'; & '$backendPython' start.py --host $BackendHost --port $BackendPort $reloadFlag"
$frontendBackendTarget = "http://127.0.0.1:$BackendPort"
$npmCommandPath = Resolve-NpmCommand
$shellExecutable = Resolve-ShellExecutable

if ($StopExisting.IsPresent) {
    $backendStopped = Stop-ProcessesByPort -Port $BackendPort -Name "Backend"
    $frontendStopped = Stop-ProcessesByPort -Port $FrontendPort -Name "Frontend"

    if (-not $backendStopped -or -not $frontendStopped) {
        throw "Neustart abgebrochen: Backend und Frontend muessen zuerst gestoppt werden."
    }
}

if (Test-PortInUse -Port $BackendPort) {
    Write-Warning "Backend-Port $BackendPort ist bereits belegt. Backend wird nicht erneut gestartet."
}
else {
    Start-Process -FilePath $shellExecutable -ArgumentList "-NoExit", "-Command", $backendCommand | Out-Null
    Write-Host "Backend started in new terminal: http://localhost:$BackendPort"

    if (Wait-BackendReady -BackendHostName $BackendHost -Port $BackendPort -TimeoutSeconds 30) {
        Write-Host "Backend ready: http://127.0.0.1:$BackendPort/api/health/live"
    }
    else {
        Write-Warning "Backend meldet sich nicht auf /api/health/live. Pruefe das Backend-Terminal auf Fehler."
    }
}

if (Test-PortInUse -Port $FrontendPort) {
    Write-Warning "Frontend-Port $FrontendPort ist bereits belegt. Frontend wird nicht erneut gestartet."
}
else {
    if (-not (Test-Path (Join-Path $frontendRoot "node_modules"))) {
        & $npmCommandPath install
    }

    Start-Process -FilePath $npmCommandPath -ArgumentList @("run", "dev", "--", "--host", $FrontendHost, "--port", $FrontendPort) -WorkingDirectory $frontendRoot -Environment @{ VITE_DEV_BACKEND_TARGET = $frontendBackendTarget } | Out-Null
    Write-Host "Frontend started in new terminal: http://localhost:$FrontendPort"
}
