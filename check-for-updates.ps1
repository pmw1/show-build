# Check for Show-Build Worker Updates
# Run this periodically or before starting the worker to check if updates are available
#
# Usage: .\check-for-updates.ps1
#        .\check-for-updates.ps1 -AutoUpdate    # Automatically sync if updates found
#        .\check-for-updates.ps1 -Silent        # Exit code only (0=up-to-date, 1=needs update)

param(
    [string]$ServerUrl = "http://192.168.51.210:8888",
    [string]$LocalAppDir = "J:\show-build\app",
    [switch]$AutoUpdate,
    [switch]$Silent
)

# Calculate local file hashes
function Get-LocalFileHashes {
    param([string]$AppDir)

    $keyFiles = @{
        "services/ffmpeg_tasks.py" = "$AppDir\services\ffmpeg_tasks.py"
        "platform_utils.py" = "$AppDir\platform_utils.py"
        "celery_app.py" = "$AppDir\celery_app.py"
        "models_v2.py" = "$AppDir\models_v2.py"
    }

    $hashes = @{}
    foreach ($file in $keyFiles.GetEnumerator()) {
        $localPath = $file.Value
        if (Test-Path $localPath) {
            $hash = Get-FileHash -Path $localPath -Algorithm MD5
            $hashes[$file.Key] = $hash.Hash.Substring(0, 8).ToLower()
        } else {
            $hashes[$file.Key] = "missing"
        }
    }

    return $hashes
}

if (-not $Silent) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Show-Build Worker Update Check" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

# Get server version info
try {
    $response = Invoke-RestMethod -Uri "$ServerUrl/version" -Method Get -TimeoutSec 10
    $serverCommit = $response.git_commit
    $serverBranch = $response.git_branch
    $serverDate = $response.git_date
    $serverFiles = $response.key_files

    if (-not $Silent) {
        Write-Host "Server Version:" -ForegroundColor Green
        Write-Host "  Commit: $serverCommit" -ForegroundColor Gray
        Write-Host "  Branch: $serverBranch" -ForegroundColor Gray
        Write-Host "  Date: $serverDate" -ForegroundColor Gray
        Write-Host ""
    }
} catch {
    if (-not $Silent) {
        Write-Host "ERROR: Cannot connect to server at $ServerUrl" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    exit 2
}

# Get local hashes
$localHashes = Get-LocalFileHashes -AppDir $LocalAppDir

# Compare files
$needsUpdate = $false
$changedFiles = @()

if (-not $Silent) {
    Write-Host "File Comparison:" -ForegroundColor Yellow
}

foreach ($file in $serverFiles.PSObject.Properties) {
    $serverHash = $file.Value
    $localHash = $localHashes[$file.Name]

    if ($serverHash -ne $localHash) {
        $needsUpdate = $true
        $changedFiles += $file.Name
        if (-not $Silent) {
            Write-Host "  [UPDATE] $($file.Name)" -ForegroundColor Red
            Write-Host "           Server: $serverHash  Local: $localHash" -ForegroundColor Gray
        }
    } else {
        if (-not $Silent) {
            Write-Host "  [OK] $($file.Name)" -ForegroundColor Green
        }
    }
}

Write-Host ""

if ($needsUpdate) {
    if (-not $Silent) {
        Write-Host "========================================" -ForegroundColor Yellow
        Write-Host "UPDATE REQUIRED" -ForegroundColor Yellow
        Write-Host "========================================" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Changed files:" -ForegroundColor Yellow
        foreach ($file in $changedFiles) {
            Write-Host "  - $file" -ForegroundColor Yellow
        }
        Write-Host ""
    }

    if ($AutoUpdate) {
        if (-not $Silent) {
            Write-Host "Auto-updating..." -ForegroundColor Cyan
        }

        # Run sync script
        $syncScript = Join-Path (Split-Path $LocalAppDir) "sync-from-linux.ps1"
        if (Test-Path $syncScript) {
            & $syncScript
        } else {
            # Fallback to git pull
            Push-Location (Split-Path $LocalAppDir)
            git fetch origin
            git reset --hard origin/dev-fork
            Pop-Location
        }

        if (-not $Silent) {
            Write-Host ""
            Write-Host "Update complete! Please restart the worker." -ForegroundColor Green
        }
    } else {
        if (-not $Silent) {
            Write-Host "To update, run one of:" -ForegroundColor Cyan
            Write-Host "  .\check-for-updates.ps1 -AutoUpdate" -ForegroundColor Gray
            Write-Host "  .\sync-from-linux.ps1" -ForegroundColor Gray
            Write-Host "  git pull origin dev-fork" -ForegroundColor Gray
        }
    }

    exit 1
} else {
    if (-not $Silent) {
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "UP TO DATE" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Local worker code matches server." -ForegroundColor Green
    }
    exit 0
}
