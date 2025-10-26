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

REM Show what we're using
echo Working Directory: %CD%
echo Python Path: %PYTHONPATH%
echo.

REM Start Celery worker
python -m celery -A celery_app worker --loglevel=info --pool=solo --concurrency=1 --queues=media --hostname=windows-worker@%%h

pause
