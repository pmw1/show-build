FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11
WORKDIR /app

# UNTOUCHABLE ZONE START - Existing requirements and setup
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install -r /app/requirements.txt
# UNTOUCHABLE ZONE END

# Add authentication dependencies
RUN pip install --no-cache-dir \
    "python-jose[cryptography]" \
    "passlib[bcrypt]" \
    "python-multipart"

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
