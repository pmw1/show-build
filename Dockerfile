FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11
WORKDIR /app

# Set timezone to America/New_York
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install wkhtmltopdf for PDF generation (download from releases since not in Trixie repos)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    fontconfig \
    libfreetype6 \
    libjpeg62-turbo \
    libpng16-16 \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libxrender1 \
    xfonts-75dpi \
    xfonts-base \
    && wget -q https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
    && apt-get install -y ./wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
    && rm wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# UNTOUCHABLE ZONE START - Existing requirements and setup
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install -r /app/requirements.txt
# UNTOUCHABLE ZONE END

# Add authentication and database dependencies
RUN pip install --no-cache-dir \
    "python-jose[cryptography]" \
    "passlib[bcrypt]" \
    "python-multipart" \
    "sqlalchemy>=2.0.0" \
    "alembic>=1.13.0" \
    "psycopg2-binary>=2.9.9" \
    "asyncpg>=0.29.0" \
    "celery>=5.3.0" \
    "redis>=5.0.0" \
    "websockets>=12.0" \
    "google-auth>=2.23.0" \
    "google-auth-oauthlib>=1.1.0" \
    "google-auth-httplib2>=0.1.1" \
    "google-api-python-client>=2.100.0" \
    "openai>=1.0.0"

# Copy application code
COPY ./app /app/

# Debug output
RUN echo "=== Directory Structure ===" && \
    ls -R /app && \
    echo "=== Python Path ===" && \
    PYTHONPATH=/app python3 -c "import sys; print('\n'.join(sys.path))"

# Set Python path environment variable
ENV PYTHONPATH=/app

# UNTOUCHABLE ZONE START - User setup and permissions
RUN groupadd -g 1001 disaffected || true && \
    useradd -m -u 1001 -g disaffected -G disaffected insider && \
    chown -R insider:disaffected /app && \
    chmod -R 755 /app/auth && \
    chmod -R 644 /app/auth/*.py && \
    chmod 755 /app/auth/__init__.py && \
    mkdir -p /app/storage && \
    chown -R insider:disaffected /app/storage && \
    chmod -R 755 /app/storage
USER insider
# UNTOUCHABLE ZONE END

# UNTOUCHABLE ZONE START - Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:80/health || exit 1
# UNTOUCHABLE ZONE END
