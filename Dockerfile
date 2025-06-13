FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install -r /app/requirements.txt
COPY ./app /app
RUN groupadd -g 1001 disaffected || true && \
    useradd -m -u 1001 -g disaffected -G disaffected insider
USER insider
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:80/health || exit 1
