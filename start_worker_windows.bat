@echo off
echo ========================================
echo Show-Build Windows Media Worker
echo ========================================
echo.

cd /d J:\show-build

python -m celery -A celery_app worker --loglevel=info --pool=solo --concurrency=1 --queues=media --hostname=windows-%COMPUTERNAME%@%%h

pause
