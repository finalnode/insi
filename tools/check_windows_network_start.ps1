$ErrorActionPreference = 'Stop'

$shareName = "insi-ci-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT"
$shareRoot = Join-Path $env:RUNNER_TEMP $shareName
$applicationRoot = Join-Path $shareRoot 'app'
$courseRoot = Join-Path $shareRoot 'course'
$window = $null

New-Item -ItemType Directory -Force $shareRoot | Out-Null
Copy-Item 'dist/windows/insi' $applicationRoot -Recurse
New-Item -ItemType Directory -Force $courseRoot | Out-Null

try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    New-SmbShare `
        -Name $shareName `
        -Path $shareRoot `
        -FullAccess $identity | Out-Null
    $uncRoot = "\\localhost\$shareName"
    $application = "$uncRoot\app\insi.exe"
    $course = "$uncRoot\course"
    $networkTest = (Resolve-Path 'tools/check_windows_network_sandbox.py').Path

    python tools/run_packaged_python.py $application -- `
        $networkTest $course
    if ($LASTEXITCODE -ne 0) {
        throw "Der interne UNC-/AppContainer-Test endete mit $LASTEXITCODE."
    }

    $sourceProcess = Start-Process -FilePath $application -PassThru
    if (-not $sourceProcess.WaitForExit(30000)) {
        throw 'Der UNC-Starter hat nicht an den lokalen Cacheprozess übergeben.'
    }
    if ($sourceProcess.ExitCode -ne 0) {
        throw "Der UNC-Starter endete mit $($sourceProcess.ExitCode)."
    }
    $deadline = (Get-Date).AddSeconds(45)
    do {
        Start-Sleep -Milliseconds 500
        $window = Get-Process -Name 'insi' -ErrorAction SilentlyContinue |
            Where-Object { $_.MainWindowHandle -ne 0 } |
            Select-Object -First 1
    } while (-not $window -and (Get-Date) -lt $deadline)
    if (-not $window) {
        throw 'Der lokale Cacheprozess hat nach dem UNC-Start kein Fenster angezeigt.'
    }
    $stagedApps = Join-Path $env:LOCALAPPDATA 'in-si/staged-apps'
    if (-not (Test-Path $stagedApps)) {
        throw 'Der versionsgebundene lokale App-Cache wurde nicht angelegt.'
    }
    Write-Host "UNC-Start und Netzwerk-AppContainer erfolgreich: $application"
}
finally {
    Get-Process -Name 'insi' -ErrorAction SilentlyContinue |
        Stop-Process -Force -ErrorAction SilentlyContinue
    Remove-SmbShare -Name $shareName -Force -ErrorAction SilentlyContinue
}
