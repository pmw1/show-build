# Sync Show-Build Code from Linux Server (Windows Worker)
# Run this from the Windows worker to pull latest code from Linux server
#
# Usage: .\sync-from-linux.ps1

param(
    [string]$LinuxHost = "192.168.51.210",
    [string]$LinuxUser = "kevin",
    [string]$LinuxPath = "/mnt/process/show-build/app",
    [string]$LocalPath = "J:\show-build\app",
    [switch]$Restart
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Show-Build Windows Worker Sync" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we have SSH/SCP access
$scp = Get-Command scp -ErrorAction SilentlyContinue
if (-not $scp) {
    Write-Host "ERROR: SCP not found. Install Git for Windows or OpenSSH." -ForegroundColor Red
    Write-Host ""
    Write-Host "Quick fix: Use Git to pull changes instead:" -ForegroundColor Yellow
    Write-Host "  cd J:\show-build" -ForegroundColor Yellow
    Write-Host "  git pull origin dev-fork" -ForegroundColor Yellow
    exit 1
}

Write-Host "Source: $LinuxUser@${LinuxHost}:$LinuxPath" -ForegroundColor Green
Write-Host "Destination: $LocalPath" -ForegroundColor Green
Write-Host ""

# Stop worker if running
if ($Restart) {
    Write-Host "Stopping Celery worker..." -ForegroundColor Yellow
    Stop-Process -Name "celery" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Sync files using SCP (recursive, excluding pycache)
Write-Host "Syncing files..." -ForegroundColor Yellow
$excludePatterns = @("__pycache__", "*.pyc", ".git")

try {
    # Use rsync if available (better than scp), otherwise fall back to scp
    $rsync = Get-Command rsync -ErrorAction SilentlyContinue
    if ($rsync) {
        $excludeArgs = $excludePatterns | ForEach-Object { "--exclude=$_" }
        & rsync -av --delete $excludeArgs "${LinuxUser}@${LinuxHost}:${LinuxPath}/" "${LocalPath}/"
    } else {
        # SCP fallback (no exclude support, will copy everything)
        & scp -r "${LinuxUser}@${LinuxHost}:${LinuxPath}/*" "$LocalPath\"
    }

    Write-Host ""
    Write-Host "Sync complete!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Sync failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Restart worker if requested
if ($Restart) {
    Write-Host ""
    Write-Host "Restarting worker..." -ForegroundColor Yellow
    Start-Sleep -Seconds 1
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c start_worker.bat" -WorkingDirectory "J:\show-build"
    Write-Host "Worker restarted!" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
if (-not $Restart) {
    Write-Host "1. Stop current worker (Ctrl+C)" -ForegroundColor Yellow
    Write-Host "2. Run: .\start_worker.bat" -ForegroundColor Yellow
}
Write-Host ""
