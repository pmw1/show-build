# Worker flavor: MEDIA-CPU — software ffmpeg (libx264), no GPU.
# For: media/SOT/fsq workers on CPU-only hosts.
# Same app code as base + media-gpu; the GPU-first ffmpeg helper degrades to CPU
# automatically here (nvenc never available), so behavior is identical, just CPU.
#   docker build -f deploy/workers/worker.media-cpu.Dockerfile -t <registry>/worker-media-cpu:<tag> .
FROM python:3.11-slim

ENV TZ=America/New_York \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/tools
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# ffmpeg (software) + fonts for FSQ render.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        ffmpeg \
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
COPY ./tools /tools

RUN groupadd -g 1001 disaffected || true && \
    useradd -m -u 1001 -g disaffected insider || true && \
    chown -R insider:disaffected /app
USER insider

CMD ["celery", "-A", "celery_app", "worker", "-Q", "media,assets_low", "--loglevel=info"]
