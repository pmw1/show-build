FROM python:3.11-slim
WORKDIR /app

ENV TZ=America/New_York \
    PYTHONUNBUFFERED=1 \
    ROUTER_CONFIG=/config/router.yaml

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app/

EXPOSE 11500
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "11500"]
