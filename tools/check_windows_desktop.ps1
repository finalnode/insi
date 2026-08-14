$ErrorActionPreference = 'Stop'

$application = Resolve-Path 'dist/windows/insi/insi.exe'
$diagnostics = 'dist/windows-startup-logs'
New-Item -ItemType Directory -Force $diagnostics | Out-Null
$process = Start-Process -FilePath $application -PassThru
$deadline = (Get-Date).AddSeconds(45)
$window = $null

try {
    do {
        Start-Sleep -Milliseconds 500
        $process.Refresh()
        if ($process.HasExited) {
            throw "in:si wurde vor dem Anzeigen eines Fensters beendet (Exitcode $($process.ExitCode))."
        }
        $window = Get-Process -Name 'insi' -ErrorAction SilentlyContinue |
            Where-Object { $_.MainWindowHandle -ne 0 } |
            Select-Object -First 1
    } while (-not $window -and (Get-Date) -lt $deadline)

    if (-not $window) {
        throw 'in:si hat innerhalb von 45 Sekunden kein Windows-Fenster angezeigt.'
    }

    Write-Host "Windows-Fenster erkannt: PID $($window.Id), Handle $($window.MainWindowHandle)"
}
finally {
    $logDirectory = Join-Path $HOME '.pykim/logs'
    if (Test-Path $logDirectory) {
        Copy-Item (Join-Path $logDirectory '*') $diagnostics -Force
    }
    $process.Refresh()
    if (-not $process.HasExited) {
        & taskkill.exe /PID $process.Id /T /F 2>$null | Out-Null
    }
}
