FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl docker.io \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
COPY sot_trace ./sot_trace
RUN pip install --no-cache-dir -e .

RUN mkdir -p /var/log/sot-trace/reports
ENV PYTHONUNBUFFERED=1 \
    SOT_TRACE_DATA_DIR=/var/log/sot-trace

CMD ["sot-trace", "daemon"]
