@echo off
echo ========================================
echo Show-Build Windows Media Worker
echo ========================================
echo.

cd /d J:\show-build\app

REM Set Python path to include app directory
set PYTHONPATH=J:\show-build\app;%PYTHONPATH%

REM Force Python to use UTC timezone (prevents 4-hour drift with UTC workers)
set TZ=UTC

python -m celery -A celery_app worker --loglevel=info --pool=solo --concurrency=1 --queues=media --hostname=windows-worker@%%h

pause
