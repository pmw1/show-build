# ============================================================================
# Show-Build Cross-Platform Celery Worker Setup Script
# For Windows Media Processing Workers
# ============================================================================
#
# This script sets up a Windows machine as a Celery media processing worker
# for the Show-Build production system.
#
# Prerequisites:
#   - Windows 10/11 or Windows Server
#   - Python 3.9+ installed
#   - FFmpeg installed (or will be installed by this script)
#   - Network access to Show-Build server (192.168.51.210)
#
# Usage:
#   .\setup_windows_worker.ps1
#
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Show-Build Windows Worker Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# ============================================================================
# STEP 1: Install Winget (if not already installed)
# ============================================================================
Write-Host "[1/8] Checking for Winget..." -ForegroundColor Green

try {
    $wingetVersion = winget --version
    Write-Host "  Winget found: $wingetVersion" -ForegroundColor Gray
} catch {
    Write-Host "  Winget not found. Installing..." -ForegroundColor Yellow
    # Install Winget (Windows Package Manager)
    Invoke-WebRequest -Uri "https://github.com/microsoft/winget-cli/releases/latest/download/Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle" -OutFile "$env:TEMP\winget.msixbundle"
    Add-AppxPackage -Path "$env:TEMP\winget.msixbundle"
    Write-Host "  Winget installed successfully" -ForegroundColor Green
}

# ============================================================================
# STEP 2: Install FFmpeg
# ============================================================================
Write-Host ""
Write-Host "[2/8] Checking for FFmpeg..." -ForegroundColor Green

try {
    $ffmpegVersion = & ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Host "  FFmpeg found: $ffmpegVersion" -ForegroundColor Gray
} catch {
    Write-Host "  FFmpeg not found. Installing via Winget..." -ForegroundColor Yellow
    winget install --id=Gyan.FFmpeg -e --silent --accept-package-agreements --accept-source-agreements

    # Add FFmpeg to PATH
    $ffmpegPath = "C:\Program Files\FFmpeg\bin"
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    if ($currentPath -notlike "*$ffmpegPath*") {
        [Environment]::SetEnvironmentVariable("Path", "$currentPath;$ffmpegPath", "Machine")
        $env:Path += ";$ffmpegPath"  # Add to current session
    }

    Write-Host "  FFmpeg installed successfully" -ForegroundColor Green
}

# ============================================================================
# STEP 3: Install Python Dependencies
# ============================================================================
Write-Host ""
Write-Host "[3/8] Checking Python..." -ForegroundColor Green

try {
    $pythonVersion = python --version
    Write-Host "  Python found: $pythonVersion" -ForegroundColor Gray
} catch {
    Write-Host "  ERROR: Python not found. Please install Python 3.9+ from python.org" -ForegroundColor Red
    exit 1
}

Write-Host "  Installing Python dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install celery redis sqlalchemy psycopg2-binary pywin32

Write-Host "  Python dependencies installed" -ForegroundColor Green

# ============================================================================
# STEP 4: Configure Network Share
# ============================================================================
Write-Host ""
Write-Host "[4/8] Configuring network share..." -ForegroundColor Green

$shareServer = "192.168.51.210"
$sharePath = "\\$shareServer\sync\disaffected"
$driveLetter = "Z:"

# Test network connectivity
Write-Host "  Testing connection to $shareServer..." -ForegroundColor Yellow
if (Test-Connection -ComputerName $shareServer -Count 2 -Quiet) {
    Write-Host "  Network connection OK" -ForegroundColor Gray
} else {
    Write-Host "  WARNING: Cannot reach $shareServer" -ForegroundColor Red
    Write-Host "  Please check network connectivity and firewall settings" -ForegroundColor Yellow
}

# Map network drive
Write-Host "  Mapping $driveLetter to $sharePath..." -ForegroundColor Yellow

# Remove existing mapping if present
if (Test-Path $driveLetter) {
    net use $driveLetter /delete /y 2>&1 | Out-Null
}

# Prompt for credentials
Write-Host "  Enter network share credentials:" -ForegroundColor Cyan
$username = Read-Host "  Username (e.g., kevin)"
$password = Read-Host "  Password" -AsSecureString
$credential = New-Object System.Management.Automation.PSCredential($username, $password)

# Map the drive
try {
    $password_plain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password))
    net use $driveLetter $sharePath /user:$username $password_plain /persistent:yes

    if (Test-Path $driveLetter) {
        Write-Host "  Network share mapped successfully" -ForegroundColor Green
    } else {
        throw "Drive mapping failed"
    }
} catch {
    Write-Host "  ERROR: Failed to map network share" -ForegroundColor Red
    Write-Host "  Please map manually: net use Z: $sharePath /user:USERNAME /persistent:yes" -ForegroundColor Yellow
    exit 1
}

# ============================================================================
# STEP 5: Create Show-Build Directory
# ============================================================================
Write-Host ""
Write-Host "[5/8] Setting up Show-Build directory..." -ForegroundColor Green

$showBuildDir = "C:\show-build"

if (-not (Test-Path $showBuildDir)) {
    New-Item -ItemType Directory -Path $showBuildDir | Out-Null
    Write-Host "  Created $showBuildDir" -ForegroundColor Gray
}

# Copy platform_utils.py and celery files
Write-Host "  Copying Show-Build worker files..." -ForegroundColor Yellow

# Check if Z: drive has the files
if (Test-Path "Z:\") {
    # TODO: User should copy these files from the Linux server
    Write-Host "  Please copy these files from the Show-Build server:" -ForegroundColor Cyan
    Write-Host "    - app/platform_utils.py -> $showBuildDir\platform_utils.py" -ForegroundColor Gray
    Write-Host "    - app/services/ffmpeg_tasks.py -> $showBuildDir\ffmpeg_tasks.py" -ForegroundColor Gray
    Write-Host "    - app/celery_app.py -> $showBuildDir\celery_app.py" -ForegroundColor Gray
    Write-Host "    - app/database.py -> $showBuildDir\database.py" -ForegroundColor Gray
    Write-Host "    - app/models_v2.py -> $showBuildDir\models_v2.py" -ForegroundColor Gray
    Write-Host ""
    Read-Host "  Press Enter when files are copied..."
}

# ============================================================================
# STEP 6: Create Celery Configuration
# ============================================================================
Write-Host ""
Write-Host "[6/8] Creating Celery configuration..." -ForegroundColor Green

$celeryConfig = @"
# Celery Configuration for Windows Worker
# Generated by setup_windows_worker.ps1

broker_url = 'redis://192.168.51.210:6379/0'
result_backend = 'redis://192.168.51.210:6379/0'

# Task routing - join the 'media' queue
task_routes = {
    'services.ffmpeg_tasks.*': {'queue': 'media'}
}

# Worker settings
worker_prefetch_multiplier = 1  # Process one task at a time (large video files)
task_acks_late = True  # Don't lose tasks if worker crashes
task_reject_on_worker_lost = True
worker_max_tasks_per_child = 10  # Restart worker after 10 tasks (memory management)

# Timeouts
task_soft_time_limit = 3600  # 1 hour soft limit
task_time_limit = 3900  # 1 hour 5 minutes hard limit

# Result settings
result_expires = 3600  # Results expire after 1 hour

# Serialization
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# Windows-specific settings
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(task_name)s] %(message)s'
"@

$celeryConfig | Out-File -FilePath "$showBuildDir\celeryconfig.py" -Encoding UTF8
Write-Host "  Celery configuration created" -ForegroundColor Green

# ============================================================================
# STEP 7: Create Worker Startup Script
# ============================================================================
Write-Host ""
Write-Host "[7/8] Creating worker startup script..." -ForegroundColor Green

$startWorkerScript = @"
@echo off
REM Show-Build Windows Celery Worker Startup Script
REM Auto-generated by setup_windows_worker.ps1

echo ========================================
echo Show-Build Windows Media Worker
echo ========================================
echo.

echo Starting Celery worker...
echo Worker will process tasks from 'media' queue
echo Platform: Windows
echo Hostname: %COMPUTERNAME%
echo.

cd /d C:\show-build

python -m celery -A celery_app worker ^
    --loglevel=info ^
    --pool=solo ^
    --concurrency=1 ^
    --queues=media ^
    --hostname=windows-%COMPUTERNAME%@%%h

pause
"@

$startWorkerScript | Out-File -FilePath "$showBuildDir\start_worker.bat" -Encoding ASCII
Write-Host "  Worker startup script created: $showBuildDir\start_worker.bat" -ForegroundColor Green

# ============================================================================
# STEP 8: Test Configuration
# ============================================================================
Write-Host ""
Write-Host "[8/8] Testing configuration..." -ForegroundColor Green

# Test FFmpeg
Write-Host "  Testing FFmpeg..." -ForegroundColor Yellow
try {
    & ffmpeg -version | Out-Null
    Write-Host "    FFmpeg: OK" -ForegroundColor Green
} catch {
    Write-Host "    FFmpeg: FAILED" -ForegroundColor Red
}

# Test network share
Write-Host "  Testing network share..." -ForegroundColor Yellow
if (Test-Path "Z:\episodes") {
    Write-Host "    Network share: OK" -ForegroundColor Green
} else {
    Write-Host "    Network share: Cannot access Z:\episodes" -ForegroundColor Red
}

# Test Redis connection
Write-Host "  Testing Redis connection..." -ForegroundColor Yellow
try {
    $pythonTest = @"
import redis
r = redis.Redis(host='192.168.51.210', port=6379, db=0)
r.ping()
print('OK')
"@
    $result = python -c $pythonTest 2>&1
    if ($result -match "OK") {
        Write-Host "    Redis connection: OK" -ForegroundColor Green
    } else {
        Write-Host "    Redis connection: FAILED - $result" -ForegroundColor Red
    }
} catch {
    Write-Host "    Redis connection: FAILED" -ForegroundColor Red
}

# ============================================================================
# Setup Complete
# ============================================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Ensure Show-Build Python files are in C:\show-build\" -ForegroundColor Gray
Write-Host "  2. Run: C:\show-build\start_worker.bat" -ForegroundColor Gray
Write-Host "  3. Worker will join the 'media' queue automatically" -ForegroundColor Gray
Write-Host "  4. Tasks will be distributed across Windows and Linux workers" -ForegroundColor Gray
Write-Host ""
Write-Host "To run worker as a Windows service:" -ForegroundColor Yellow
Write-Host "  1. Install NSSM: winget install NSSM.NSSM" -ForegroundColor Gray
Write-Host "  2. Run: nssm install ShowBuildWorker C:\show-build\start_worker.bat" -ForegroundColor Gray
Write-Host ""
Write-Host "Worker will automatically use:" -ForegroundColor Cyan
Write-Host "  - NVENC GPU encoding (if NVIDIA GPU detected)" -ForegroundColor Gray
Write-Host "  - Cross-platform path handling" -ForegroundColor Gray
Write-Host "  - Same task queue as Linux workers" -ForegroundColor Gray
Write-Host ""
