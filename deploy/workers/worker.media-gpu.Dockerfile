# Worker flavor: MEDIA-GPU — CUDA + nvenc-capable ffmpeg. GPU-first, CPU failover.
# For: media/SOT/fsq workers on GPU hosts (kairo, prefect, proxima-if-carded).
# Driver is injected at RUNTIME by the NVIDIA Container Toolkit (install once per
# host) + `--gpus all`; this image carries CUDA userspace + ffmpeg.
#   docker build -f deploy/workers/worker.media-gpu.Dockerfile -t <registry>/worker-media-gpu:<tag> .
#
# VALIDATION REQUIRED (can't be done from the showtime session — needs a GPU host):
#   docker run --rm --gpus all <image> ffmpeg -hide_banner -encoders | grep nvenc
#   -> must list h264_nvenc / hevc_nvenc. If the apt ffmpeg lacks nvenc, switch to
#      a known nvenc build (e.g. jrottenberg/ffmpeg:*-nvidia as a COPY --from stage,
#      or build ffmpeg --enable-nvenc). See NOTE below.
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV TZ=America/New_York \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/tools \
    DEBIAN_FRONTEND=noninteractive \
    NVIDIA_DRIVER_CAPABILITIES=compute,video,utility \
    NVIDIA_VISIBLE_DEVICES=all
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Python (not in the cuda base) + ffmpeg + fonts.
# NOTE: Ubuntu 22.04's ffmpeg is built with --enable-nvenc; nvenc works when the
# NVIDIA driver libs are present at runtime (toolkit injects them). If a given host's
# ffmpeg build lacks nvenc, swap this for a multi-stage COPY from a known nvenc image.
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 python3-pip \
        curl ca-certificates \
        ffmpeg \
        fonts-liberation fonts-dejavu-core \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
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

# Heavy encode queues; concurrency tuned per host (card nvenc session ceiling) in workers.yml.
CMD ["celery", "-A", "celery_app", "worker", "-Q", "media,fsq,assets_low", "--loglevel=info"]
