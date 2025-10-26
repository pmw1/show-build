@echo off
echo ========================================
echo Show-Build Windows Media Worker
echo ========================================
echo.

REM Change to app directory where modules are located
cd /d J:\show-build\app

REM Set Python path to include app directory
set PYTHONPATH=J:\show-build\app;%PYTHONPATH%

REM Force Python to use UTC timezone (prevents 4-hour drift with UTC workers)
set TZ=UTC

REM Set Redis URL for Celery (CRITICAL - must be .223 not .210!)
set REDIS_URL=redis://:showbuild2025@192.168.51.223:6379/0

REM Show configuration
echo Working Directory: %CD%
echo Python Path: %PYTHONPATH%
echo Redis URL: %REDIS_URL%
echo.
echo Starting Celery worker...
echo.

REM Start Celery worker
python -m celery -A celery_app worker --loglevel=info --pool=solo --concurrency=1 --queues=media --hostname=windows-worker@%%h

pause
