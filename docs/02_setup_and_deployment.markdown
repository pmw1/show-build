# Setup and Deployment

## Overview
This document outlines the setup and deployment process for the Disaffected Production Suite, including launch commands, dependency management, Docker configuration, and verification tests.

## Prerequisites
- **Node.js**: v16+ for frontend
- **Python**: 3.11 for backend
- **Docker**: For containerized deployment
- **Docker Compose**: V2 for multi-container orchestration
- **NPM**: For frontend package management

## Setup Instructions
1. **Clone Repository**:
   ```bash
   git clone /path/to/repository
   cd /mnt/process/show-build
   ```

2. **Install Frontend Dependencies**:
   ```bash
   cd disaffected-ui
   npm install --legacy-peer-deps
   ```

3. **Verify Docker Installation**:
   ```bash
   docker --version
   docker-compose --version
   ```

## Docker Configuration
- **Containers**:
  - `show-build-server`: FastAPI backend, runs on `http://192.168.51.210:8888/`
  - `mosquitto`: MQTT broker for real-time communication
  - Additional services: Whisper API, Node-RED
- **Volume Mounts**:
  - Host path `/mnt/sync/disaffected/episodes/` maps to `/home/episodes` in the `show-build-server` container for episode data.
  - Host path `/mnt/process/show-build/app/storage/` maps to `/app/storage/` for JSON storage (users, API keys).
- **Networking**:
  - Docker network: `video-post`
  - MQTT broker configured with `mosquitto.conf`:
    ```conf
    listener 1883 0.0.0.0
    allow_anonymous true
    ```
  - Backend accessible at `http://192.168.51.210:8888/` (host) or `http://show-build-server:8888/` (container).
- **Docker Compose Example**:
  ```yaml
  version: '3.8'
  services:
    show-build-server:
      image: show-build-fastapi
      volumes:
        - /mnt/sync/disaffected/episodes/:/home/episodes
        - /mnt/process/show-build/app/storage/:/app/storage
      ports:
        - "8888:8888"
      networks:
        - video-post
    mosquitto:
      image: eclipse-mosquitto
      volumes:
        - /mnt/process/show-build/tools/mosquitto.conf:/mosquitto/config/mosquitto.conf
      ports:
        - "1883:1883"
      networks:
        - video-post
  networks:
    video-post:
      driver: bridge
  ```

## Launch Commands
1. **Backend (FastAPI)**:
   ```bash
   cd /mnt/process/show-build
   docker compose up -d show-build-server
   ```
   - Runs at `http://192.168.51.210:8888/`
   - Health check: `curl http://192.168.51.210:8888/health`

2. **Frontend (Vue.js)**:
   ```bash
   cd /mnt/process/show-build/disaffected-ui
   npm run serve
   ```
   - Runs at `http://192.168.51.210:8080/`

## Configuration
- **vue.config.js**:
  ```javascript
  module.exports = {
    transpileDependencies: true,
    devServer: {
      host: '0.0.0.0',
      port: 8080,
      allowedHosts: 'all',
      proxy: {
        '/api': {
          target: 'http://192.168.51.210:8888',
          changeOrigin: true,
          secure: false,
          pathRewrite: { '^/api': '' }
        }
      }
    }
  }
  ```
- **Docker Compose**: Ensure `mosquitto.conf` is mounted and configured for remote access.

## Verification Tests
- **Frontend Access**:
  ```bash
  curl http://192.168.51.210:8080/
  ```
- **Backend Health**:
  ```bash
  curl http://192.168.51.210:8888/health
  ```
- **API Proxy**:
  ```bash
  curl http://192.168.51.210:8080/api/health
  ```

## Dependencies
- **Frontend**: Vue 3.2.13, Vuetify 3.8.8, Vue Router 4.5.1, Axios 1.9.0
- **Backend**: FastAPI, Python 3.11 (see `/app/requirements.txt`)
- **Infrastructure**: Docker, Eclipse Mosquitto MQTT

*Last Updated: July 8, 2025*