param(
    [Parameter(Position = 0)]
    [string]$Target,
    [string]$Port,
    [string]$IdentityFile,
    [string]$RemoteRoot,
    [string]$ConsolePort,
    [string]$Domain,
    [switch]$DryRun,
    [switch]$Yes
)

$ErrorActionPreference = "Stop"
$ProvidedParameters = @{} + $PSBoundParameters

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Bootstrap = Join-Path $PSScriptRoot "remote\bootstrap.sh"
$Control = Join-Path $PSScriptRoot "remote\consolectl.sh"
$RemoteBootstrap = "/tmp/nanobot-console-bootstrap.sh"
$RemoteControl = "/tmp/nanobot-console-consolectl.sh"
$RemoteAppTmp = "/tmp/nanobot-console-app-upload"
$SudoPassword = $null
$DEFAULT_PORT = "22"
$DEFAULT_REMOTE_ROOT = "/opt/nanobot-console"
$DEFAULT_CONSOLE_PORT = "8787"

function RemoteQuote([string]$Value) {
    return "'" + ($Value -replace "'", "'\''") + "'"
}

function Prompt-Value([string]$Label, [string]$Default = "") {
    $suffix = ""
    if ($Default) {
        $suffix = " [$Default]"
    }
    $value = Read-Host "$Label$suffix"
    if ($value.Trim()) {
        return $value.Trim()
    }
    return $Default
}

function Configure-Interactive {
    if ($Yes) {
        return
    }
    if (-not $ProvidedParameters.ContainsKey("Target")) {
        Write-Host "Interactive deployer"
        $script:Target = Prompt-Value "SSH target, for example <user>@<vm-ip>"
    }
    if (-not $ProvidedParameters.ContainsKey("Port")) {
        $script:Port = Prompt-Value "SSH port" $DEFAULT_PORT
    }
    if (-not $ProvidedParameters.ContainsKey("RemoteRoot")) {
        $script:RemoteRoot = Prompt-Value "Remote deploy root on the VM" $DEFAULT_REMOTE_ROOT
    }
    if (-not $ProvidedParameters.ContainsKey("ConsolePort")) {
        $script:ConsolePort = Prompt-Value "Console port" $DEFAULT_CONSOLE_PORT
    }
    if (-not $ProvidedParameters.ContainsKey("Domain")) {
        $script:Domain = Prompt-Value "Console HTTPS domain, or press Enter for HTTP-only access" ""
    }
}

function SshArgs {
    $cmdArgs = @("-p", $Port, "-o", "ConnectTimeout=10", "-o", "ConnectionAttempts=1", "-o", "StrictHostKeyChecking=accept-new")
    if ($Yes) {
        $cmdArgs += @("-o", "BatchMode=yes", "-o", "NumberOfPasswordPrompts=0")
    } else {
        $cmdArgs += @("-o", "BatchMode=no", "-o", "NumberOfPasswordPrompts=3")
    }
    if ($IdentityFile) {
        $cmdArgs += @("-i", $IdentityFile)
    }
    $cmdArgs += $Target
    return $cmdArgs
}

function ScpArgs {
    $cmdArgs = @("-P", $Port, "-o", "ConnectTimeout=10", "-o", "ConnectionAttempts=1", "-o", "StrictHostKeyChecking=accept-new")
    if ($Yes) {
        $cmdArgs += @("-o", "BatchMode=yes", "-o", "NumberOfPasswordPrompts=0")
    } else {
        $cmdArgs += @("-o", "BatchMode=no", "-o", "NumberOfPasswordPrompts=3")
    }
    if ($IdentityFile) {
        $cmdArgs += @("-i", $IdentityFile)
    }
    return $cmdArgs
}

function Invoke-Remote([string]$Command, [switch]$Tty) {
    $cmdArgs = @()
    if ($Tty) {
        $cmdArgs += "-t"
    }
    $cmdArgs += (SshArgs)
    $cmdArgs += $Command
    & ssh @cmdArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Remote command failed with exit code $LASTEXITCODE"
    }
}

function Invoke-RemoteInput([string]$Command, [string]$InputText) {
    $cmdArgs = (SshArgs)
    $cmdArgs += $Command
    $InputText | & ssh @cmdArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Remote command failed with exit code $LASTEXITCODE"
    }
}

function Read-SudoPasswordOnce {
    if ($script:SudoPassword -ne $null) {
        return
    }
    $secure = Read-Host "Remote Linux sudo password for the target user" -AsSecureString
    if ($secure.Length -eq 0) {
        Write-Error "Aborted: sudo password was not provided."
    }
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        $script:SudoPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

function Invoke-RemoteSudo([string]$Command) {
    if ($Yes) {
        Invoke-Remote ("sudo -n bash -lc " + (RemoteQuote $Command))
    } else {
        Read-SudoPasswordOnce
        Invoke-RemoteInput ("sudo -S -p '' bash -lc " + (RemoteQuote $Command)) ($script:SudoPassword + "`n")
    }
}

function Copy-Remote([string[]]$Sources, [string]$Destination, [switch]$Recurse) {
    $cmdArgs = (ScpArgs)
    if ($Recurse) {
        $cmdArgs = @("-r") + $cmdArgs
    }
    $cmdArgs += $Sources
    $cmdArgs += "$Target`:$Destination"
    & scp @cmdArgs
    if ($LASTEXITCODE -ne 0) {
        throw "SCP failed with exit code $LASTEXITCODE"
    }
}

function Copy-FilteredTree([string]$Source, [string]$Destination) {
    $sourcePath = (Resolve-Path $Source).Path.TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    $sourcePrefix = $sourcePath + [System.IO.Path]::DirectorySeparatorChar
    Get-ChildItem -LiteralPath $sourcePath -Recurse -Force | ForEach-Object {
        $relative = $_.FullName.Substring($sourcePrefix.Length)
        $parts = $relative -split '[\\/]'
        if ($parts -contains "__pycache__" -or $parts -contains ".pytest_cache") {
            return
        }
        if (-not $_.PSIsContainer -and ($_.Name -like "*.pyc" -or $_.Name -like "*.pyo")) {
            return
        }
        $target = Join-Path $Destination $relative
        if ($_.PSIsContainer) {
            New-Item -ItemType Directory -Force -Path $target | Out-Null
        } else {
            New-Item -ItemType Directory -Force -Path (Split-Path $target -Parent) | Out-Null
            Copy-Item -LiteralPath $_.FullName -Destination $target -Force
        }
    }
}

function New-AppUploadStaging {
    $staging = Join-Path ([System.IO.Path]::GetTempPath()) ("nanobot-console-upload-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $staging | Out-Null
    Copy-FilteredTree (Join-Path $RepoRoot "console") (Join-Path $staging "console")
    Copy-FilteredTree (Join-Path $RepoRoot "docker") (Join-Path $staging "docker")
    Copy-Item -LiteralPath (Join-Path $RepoRoot "Dockerfile") -Destination (Join-Path $staging "Dockerfile") -Force
    return $staging
}

function ConsoleUrl {
    $domain = $Domain.Trim().TrimEnd("/")
    $domain = $domain -replace "^https?://", ""
    if ($domain) {
        return "https://$domain/"
    }
    $hostPart = ($Target -split "@")[-1]
    return "http://$hostPart`:$ConsolePort/"
}

Configure-Interactive

if (-not $Port) {
    $Port = $DEFAULT_PORT
}
if (-not $RemoteRoot) {
    $RemoteRoot = $DEFAULT_REMOTE_ROOT
}
if (-not $ConsolePort) {
    $ConsolePort = $DEFAULT_CONSOLE_PORT
}
if ($null -eq $Domain) {
    $Domain = ""
}

if (-not $Target) {
    if ($Yes) {
        Write-Error "Missing SSH target. Non-interactive mode requires <user>@<vm-ip>."
    }
    Write-Error "Missing SSH target."
}

if (-not (Test-Path $Bootstrap)) {
    Write-Error "Missing remote bootstrap script: $Bootstrap"
}
if (-not (Test-Path $Control)) {
    Write-Error "Missing remote control script: $Control"
}

$Domain = ($Domain.Trim().TrimEnd("/") -replace "^https?://", "")
$RemoteRootQ = RemoteQuote $RemoteRoot
$ConsolePortQ = RemoteQuote $ConsolePort
$DomainQ = RemoteQuote $Domain
$RemoteBootstrapQ = RemoteQuote $RemoteBootstrap
$RemoteControlQ = RemoteQuote $RemoteControl
$RemoteAppTmpQ = RemoteQuote $RemoteAppTmp

Write-Host "Target: $Target"
Write-Host "Remote root: $RemoteRoot"
Write-Host "Checking SSH connectivity..."
Invoke-Remote "printf 'ssh=ok\n'"

Write-Host "Uploading remote deploy scripts..."
Copy-Remote @($Bootstrap) $RemoteBootstrap
Copy-Remote @($Control) $RemoteControl

Write-Host "Probing remote prerequisites..."
Invoke-Remote "bash $RemoteBootstrapQ probe $RemoteRootQ $ConsolePortQ $DomainQ"

if ($DryRun) {
    Write-Host ""
    Write-Host "Dry-run only. No host changes applied."
    return
}

if (-not $Yes) {
    Write-Host ""
    Write-Host "Planned host changes:"
    Write-Host "  - create/update $RemoteRoot"
    Write-Host "  - upload deployer-controlled scaffold files"
    Write-Host "  - upload app files"
    if ($Domain) {
        Write-Host "  - configure HTTPS reverse proxy for $Domain"
    }
    $answer = Read-Host "Approve these host changes? Type 'yes' to continue"
    if ($answer.Trim().ToLowerInvariant() -ne "yes") {
        Write-Host "Host changes were not approved. Exiting."
        exit 1
    }
}

Write-Host "Applying remote bootstrap..."
Invoke-RemoteSudo "bash $RemoteBootstrapQ apply $RemoteRootQ $ConsolePortQ $DomainQ"

Write-Host "Installing remote scaffold..."
Invoke-RemoteSudo "mkdir -p $RemoteRootQ && install -m 0755 $RemoteBootstrapQ $RemoteRootQ/bootstrap.sh && install -m 0755 $RemoteControlQ $RemoteRootQ/consolectl && printf '%s\n' 'nanobot-console' > $RemoteRootQ/VERSION && rm -f $RemoteBootstrapQ $RemoteControlQ"

Write-Host "Uploading app files..."
Invoke-Remote "rm -rf $RemoteAppTmpQ && mkdir -p $RemoteAppTmpQ"
$appStaging = New-AppUploadStaging
try {
    $appSources = @(
        (Join-Path $appStaging "console"),
        (Join-Path $appStaging "docker"),
        (Join-Path $appStaging "Dockerfile")
    )
    Copy-Remote $appSources "$RemoteAppTmp/" -Recurse
} finally {
    if ($appStaging -and (Test-Path $appStaging)) {
        Remove-Item -Recurse -Force -LiteralPath $appStaging
    }
}
Invoke-RemoteSudo "mkdir -p $RemoteRootQ/app && cp -R $RemoteAppTmpQ/. $RemoteRootQ/app/ && rm -rf $RemoteAppTmpQ"

Write-Host "Finalizing console service..."
Invoke-RemoteSudo "bash $RemoteRootQ/bootstrap.sh finalize $RemoteRootQ $ConsolePortQ $DomainQ"

Write-Host "Done."
Write-Host "Console root: $RemoteRoot"
if (-not $Domain) {
    Write-Host "Warning: console will be exposed over plain HTTP. Use only on a trusted network."
}
Write-Host ("Console URL: " + (ConsoleUrl))
Write-Host "Control command: sudo $RemoteRoot/consolectl status"
