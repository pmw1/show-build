# Worker flavor: BASE — light tasks, no media/ffmpeg.
# For: llm-content worker, celery-beat, future light workers.
# Build context = repo root (so ./app and ./requirements.txt resolve).
#   docker build -f deploy/workers/worker.base.Dockerfile -t <registry>/worker-base:<tag> .
FROM python:3.11-slim

ENV TZ=America/New_York \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/tools
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Minimal system deps (no ffmpeg). curl for healthchecks; fonts for any Pillow text.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        fonts-liberation \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ./app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt && \
    pip install --no-cache-dir \
        "celery>=5.3.0" "redis>=5.0.0" \
        "sqlalchemy>=2.0.0" "alembic>=1.13.0" \
        "psycopg2-binary>=2.9.9"

COPY ./app /app
# tools/ is optional (FSQ renderer etc.); copy if present in context.
COPY ./tools /tools

# Non-root to match the app image convention (uid 1001 / group disaffected).
RUN groupadd -g 1001 disaffected || true && \
    useradd -m -u 1001 -g disaffected insider || true && \
    chown -R insider:disaffected /app
USER insider

# Default command is overridden by compose (-Q <queues> etc.).
CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info"]
