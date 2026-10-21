# WorkBOXig PowerShell Automation and Updater Script
param(
    [Parameter(Position=0)]
    [string]$CommitMessage,
    [switch]$Push,
    [switch]$Pull,
    [switch]$Build,
    [switch]$Test
)

$ErrorActionPreference = "Stop"

function Show-Header {
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "       WorkBOXig - PowerShell Automation and Updater      " -ForegroundColor Yellow
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Run-Tests {
    Write-Host "Running test suite..." -ForegroundColor Yellow
    python -m unittest tests/test_app.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "All tests passed cleanly!" -ForegroundColor Green
        return $true
    } else {
        Write-Host "Tests failed! Aborting." -ForegroundColor Red
        return $false
    }
}

function Do-Push {
    param([string]$Msg)
    if (-not $Msg) {
        $Msg = Read-Host "Enter commit message"
    }
    if (-not $Msg) {
        $Msg = "chore: update WorkBOXig codebase"
    }

    if (-not (Run-Tests)) {
        return
    }

    Write-Host "`nStaging changes (git add .)..." -ForegroundColor Yellow
    git add .

    Write-Host "Committing: '$Msg'..." -ForegroundColor Yellow
    git commit -m "$Msg"

    Write-Host "Pushing to GitHub (origin main)..." -ForegroundColor Yellow
    git push

    Write-Host "`nSuccessfully pushed to GitHub!" -ForegroundColor Green
}

function Do-Pull {
    Write-Host "Pulling latest changes from GitHub..." -ForegroundColor Yellow
    git pull
    Write-Host "Updating dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    Write-Host "`nProject updated to latest GitHub version!" -ForegroundColor Green
}

function Do-Build {
    if (-not (Run-Tests)) {
        return
    }

    Write-Host "`nBuilding WorkBOXig.exe..." -ForegroundColor Yellow
    python -m PyInstaller WorkBOXig.spec --noconfirm

    Write-Host "`nBuilding WorkBOXig_Setup.exe..." -ForegroundColor Yellow
    python -m PyInstaller installer.spec --noconfirm

    Write-Host "`nBuild complete! Executables ready in dist/:" -ForegroundColor Green
    Get-ChildItem dist | Select-Object Name, Length, LastWriteTime
}

# Entry point
Show-Header

if ($CommitMessage -and -not $Pull -and -not $Build -and -not $Test) {
    Do-Push -Msg $CommitMessage
    exit
}

if ($Push) {
    Do-Push -Msg $CommitMessage
    exit
}

if ($Pull) {
    Do-Pull
    exit
}

if ($Build) {
    Do-Build
    exit
}

if ($Test) {
    Run-Tests
    exit
}

Write-Host "Select action:" -ForegroundColor White
Write-Host " [1] Push changes to GitHub" -ForegroundColor Green
Write-Host " [2] Pull latest changes from GitHub" -ForegroundColor Cyan
Write-Host " [3] Build .exe and Setup installer" -ForegroundColor Magenta
Write-Host " [4] Run automated tests" -ForegroundColor Yellow
Write-Host " [0] Exit" -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "Your choice (1-4)"

switch ($choice) {
    "1" { Do-Push }
    "2" { Do-Pull }
    "3" { Do-Build }
    "4" { Run-Tests }
    default { Write-Host "Exit." -ForegroundColor Gray }
}
