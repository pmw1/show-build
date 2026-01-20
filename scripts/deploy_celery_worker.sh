#!/bin/bash
#
# deploy_celery_worker.sh
#
# Automated Celery worker deployment script for Show-Build
# Deploys a fully functional FFmpeg worker to a remote Linux server
#
# Usage:
#   ./deploy_celery_worker.sh <hostname> <worker_name> <queue_name> [concurrency]
#
# Example:
#   ./deploy_celery_worker.sh proxima media_worker media 4
#   ./deploy_celery_worker.sh kairo media_worker media 4
#
# Prerequisites:
#   - SSH key-based authentication configured
#   - Remote server has Docker and Docker Compose installed
#   - Remote server has mounted /mnt/sync/disaffected/episodes and /mnt/sync/shared_media
#

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REDIS_HOST="${REDIS_HOST:-192.168.51.223}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-showbuild2025}"
LLM_STATE_API_KEY="${LLM_STATE_API_KEY:-}"  # Optional: for SOT processing notifications
WORKER_DIR="show-build-worker"

# Function to print colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check command existence
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed"
        exit 1
    fi
}

# Validate arguments
if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <hostname> <worker_name> <queue_name> [concurrency]"
    echo ""
    echo "Arguments:"
    echo "  hostname     - Remote server hostname/IP (e.g., kairo, 192.168.51.197)"
    echo "  worker_name  - Unique worker name (e.g., media_worker)"
    echo "  queue_name   - Celery queue to consume (e.g., media, compilation)"
    echo "  concurrency  - Number of worker processes (default: 4)"
    echo ""
    echo "Examples:"
    echo "  $0 kairo media_worker media 4"
    echo "  $0 proxima compilation_worker compilation 2"
    echo "  $0 192.168.51.197 quotes_worker quotes 4"
    exit 1
fi

HOSTNAME="$1"
WORKER_NAME="$2"
QUEUE_NAME="$3"
CONCURRENCY="${4:-4}"

log_info "Starting deployment of Celery worker to $HOSTNAME"
log_info "Worker: ${WORKER_NAME}@${HOSTNAME}"
log_info "Queue: $QUEUE_NAME"
log_info "Concurrency: $CONCURRENCY"

# Check prerequisites
check_command ssh
check_command scp

# Test SSH connectivity
log_info "Testing SSH connectivity to $HOSTNAME..."
if ! ssh -o ConnectTimeout=5 "$HOSTNAME" "echo 'SSH connection successful'" &> /dev/null; then
    log_error "Cannot connect to $HOSTNAME via SSH"
    log_error "Please ensure SSH key authentication is configured"
    exit 1
fi
log_success "SSH connection verified"

# Check if Docker is installed on remote server
log_info "Checking Docker installation on $HOSTNAME..."
if ! ssh "$HOSTNAME" "command -v docker &> /dev/null"; then
    log_error "Docker is not installed on $HOSTNAME"
    log_error "Please install Docker before deploying worker"
    exit 1
fi
log_success "Docker found on remote server"

# Check if Docker Compose is available
log_info "Checking Docker Compose on $HOSTNAME..."
if ! ssh "$HOSTNAME" "docker compose version &> /dev/null"; then
    log_error "Docker Compose is not available on $HOSTNAME"
    log_error "Please install Docker Compose v2 (docker compose, not docker-compose)"
    exit 1
fi
log_success "Docker Compose found on remote server"

# Create deployment directory on remote server
log_info "Creating deployment directory on $HOSTNAME..."
ssh "$HOSTNAME" "mkdir -p ~/${WORKER_DIR}"
log_success "Deployment directory created: ~/${WORKER_DIR}"

# Generate Dockerfile
log_info "Generating Dockerfile..."
cat > /tmp/worker_dockerfile << 'EOF'
FROM python:3.11-slim

# Install ffmpeg and fonts for FSQ rendering
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app /app

# Copy tools directory (for FSQ renderer)
COPY tools /tools

# Add tools to Python path
ENV PYTHONPATH="/app:/tools:${PYTHONPATH}"

# Run Celery worker
CMD ["celery", "-A", "celery_app.celery_app", "worker", "--loglevel=info"]
EOF

# Generate requirements.txt
log_info "Generating requirements.txt..."
cat > /tmp/worker_requirements.txt << 'EOF'
# Celery and Redis
celery[redis]>=5.3.0
redis>=5.0.0

# Database (needed for tasks that access DB)
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.9

# HTTP requests (for notifications)
requests>=2.31.0

# Media processing
ffmpeg-python>=0.2.0

# Image processing (for FSQ quote generation)
pillow>=10.0.0

# Content processing
python-frontmatter>=1.0.0
markdown>=3.4.3
pydantic>=2.0.3
pydantic-settings>=2.0.3

# AI/Transcription (for Whisper API)
httpx>=0.25.0
openai>=1.0.0
EOF

# Generate docker-compose.yml
# For asset queues, include all priority levels
log_info "Generating docker-compose.yml..."

# Determine queue list based on queue name
if [ "$QUEUE_NAME" = "assets" ]; then
    FULL_QUEUE_LIST="assets_high,assets,assets_low"
    log_info "Asset queue selected - will consume: assets_high, assets, assets_low"
else
    FULL_QUEUE_LIST="$QUEUE_NAME"
fi

# Determine volume mount path based on hostname
# Kairo has NFS at /mnt/whisperbox/sync instead of /mnt/sync
if [ "$HOSTNAME" = "kairo" ]; then
    VOLUME_PATH="/mnt/whisperbox/sync:/mnt/sync"
    log_info "Kairo detected - using NFS mount at /mnt/whisperbox/sync"
else
    VOLUME_PATH="/mnt/sync:/mnt/sync"
fi

# Kairo needs to connect to kairo_kairo-network for Whisper access
if [ "$HOSTNAME" = "kairo" ]; then
    log_info "Kairo detected - will connect to kairo_kairo-network for Whisper"
    cat > /tmp/worker_compose.yml << EOF
services:
  celery-worker:
    build: .
    container_name: ${HOSTNAME}-${WORKER_NAME}
    user: "1000:1001"
    command: celery -A celery_app worker -Q ${FULL_QUEUE_LIST} --hostname=${WORKER_NAME}@${HOSTNAME} --concurrency=${CONCURRENCY}
    volumes:
      - ${VOLUME_PATH}
    environment:
      - REDIS_URL=redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/0
      - MEDIA_ROOT=/mnt/sync/disaffected
      - DATABASE_URL=postgresql://showbuild:showbuild@192.168.51.210:5433/showbuild
      - PYTHONPATH=/app:/tools
      - LLM_STATE_API_KEY=${LLM_STATE_API_KEY:-}
    networks:
      - default
      - kairo_kairo-network
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  kairo_kairo-network:
    external: true
EOF
else
    cat > /tmp/worker_compose.yml << EOF
services:
  celery-worker:
    build: .
    container_name: ${HOSTNAME}-${WORKER_NAME}
    user: "1000:1001"
    command: celery -A celery_app worker -Q ${FULL_QUEUE_LIST} --hostname=${WORKER_NAME}@${HOSTNAME} --concurrency=${CONCURRENCY}
    volumes:
      - ${VOLUME_PATH}
    environment:
      - REDIS_URL=redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/0
      - MEDIA_ROOT=/mnt/sync/disaffected
      - DATABASE_URL=postgresql://showbuild:showbuild@192.168.51.210:5433/showbuild
      - PYTHONPATH=/app:/tools
      - LLM_STATE_API_KEY=${LLM_STATE_API_KEY:-}
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
EOF
fi

# Upload configuration files
log_info "Uploading configuration files to $HOSTNAME..."
scp /tmp/worker_dockerfile "$HOSTNAME:~/${WORKER_DIR}/Dockerfile"
scp /tmp/worker_requirements.txt "$HOSTNAME:~/${WORKER_DIR}/requirements.txt"
scp /tmp/worker_compose.yml "$HOSTNAME:~/${WORKER_DIR}/docker-compose.yml"
log_success "Configuration files uploaded"

# Clean up temp files
rm -f /tmp/worker_dockerfile /tmp/worker_requirements.txt /tmp/worker_compose.yml

# Copy application code
log_info "Copying application code to $HOSTNAME..."
PROJECT_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
APP_DIR="${PROJECT_DIR}/app"
TOOLS_DIR="${PROJECT_DIR}/tools"

if [ ! -d "$APP_DIR" ]; then
    log_error "Cannot find app directory at $APP_DIR"
    exit 1
fi

scp -r "$APP_DIR" "$HOSTNAME:~/${WORKER_DIR}/"
log_success "Application code copied"

# Copy tools directory (needed for FSQ renderer)
if [ -d "$TOOLS_DIR" ]; then
    log_info "Copying tools directory to $HOSTNAME..."
    scp -r "$TOOLS_DIR" "$HOSTNAME:~/${WORKER_DIR}/"
    log_success "Tools directory copied"
else
    log_warning "Tools directory not found at $TOOLS_DIR"
fi

# Check if volumes exist on remote server
log_info "Checking required volumes on $HOSTNAME..."
MISSING_VOLUMES=0
if ! ssh "$HOSTNAME" "[ -d /mnt/sync/disaffected/episodes ]"; then
    log_warning "Volume /mnt/sync/disaffected/episodes does not exist on $HOSTNAME"
    MISSING_VOLUMES=1
fi
if ! ssh "$HOSTNAME" "[ -d /mnt/sync/shared_media ]"; then
    log_warning "Volume /mnt/sync/shared_media does not exist on $HOSTNAME"
    MISSING_VOLUMES=1
fi

if [ $MISSING_VOLUMES -eq 1 ]; then
    log_warning "Some mounted volumes are missing. Worker may fail to access files."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_error "Deployment cancelled by user"
        exit 1
    fi
fi

# Build and start worker
log_info "Building and starting worker on $HOSTNAME..."
ssh "$HOSTNAME" "cd ~/${WORKER_DIR} && docker compose up -d --build"

# Wait for worker to start
log_info "Waiting for worker to start (10 seconds)..."
sleep 10

# Check if container is running
log_info "Checking container status..."
CONTAINER_STATUS=$(ssh "$HOSTNAME" "docker compose -f ~/${WORKER_DIR}/docker-compose.yml ps --format json" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list) and len(data) > 0:
        print(data[0].get('State', 'unknown'))
    else:
        print(data.get('State', 'unknown'))
except:
    print('unknown')
" 2>/dev/null || echo "unknown")

if [ "$CONTAINER_STATUS" = "running" ]; then
    log_success "Worker container is running"
else
    log_error "Worker container is not running (status: $CONTAINER_STATUS)"
    log_info "Showing container logs:"
    ssh "$HOSTNAME" "docker logs ${HOSTNAME}-${WORKER_NAME} --tail 50"
    exit 1
fi

# Show worker logs
log_info "Worker logs (last 30 lines):"
ssh "$HOSTNAME" "docker logs ${HOSTNAME}-${WORKER_NAME} --tail 30"

# Final verification
echo ""
log_success "═══════════════════════════════════════════════════════════"
log_success "Worker deployment completed successfully!"
log_success "═══════════════════════════════════════════════════════════"
echo ""
log_info "Deployment Details:"
echo "  Hostname:     $HOSTNAME"
echo "  Worker Name:  ${WORKER_NAME}@${HOSTNAME}"
echo "  Queue:        $QUEUE_NAME"
echo "  Concurrency:  $CONCURRENCY"
echo "  Container:    ${HOSTNAME}-${WORKER_NAME}"
echo "  Directory:    ~/${WORKER_DIR}"
echo ""
log_info "Useful Commands:"
echo "  View logs:        ssh $HOSTNAME 'docker logs ${HOSTNAME}-${WORKER_NAME} -f'"
echo "  Restart worker:   ssh $HOSTNAME 'cd ~/${WORKER_DIR} && docker compose restart'"
echo "  Stop worker:      ssh $HOSTNAME 'cd ~/${WORKER_DIR} && docker compose down'"
echo "  Update code:      scp -r $APP_DIR $HOSTNAME:~/${WORKER_DIR}/ && ssh $HOSTNAME 'cd ~/${WORKER_DIR} && docker compose restart'"
echo ""
log_info "Next Steps:"
echo "  1. Verify worker registration from Show-Build server:"
echo "     docker exec show-build-server python -c \"from celery_app import celery_app; print(list(celery_app.control.inspect().stats().keys()))\""
echo ""
echo "  2. Test task submission:"
echo "     docker exec show-build-server python -c \"from services.ffmpeg_tasks import process_sot_video; result = process_sot_video.delay('/path/to/video.mp4', '9999', 'test'); print('Task ID:', result.id)\""
echo ""

exit 0
