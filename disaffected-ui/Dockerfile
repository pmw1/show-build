# Frontend Dockerfile for Vue.js application

# Development stage
FROM node:18-alpine as development

# Install OpenSSL for SSL certificate generation
RUN apk add --no-cache openssl

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy source code (excluding ssl directory to prevent permission issues)
COPY --chown=node:node . .
RUN mkdir -p /app/ssl && chown -R node:node /app/ssl

# Expose port 8080 for Vue dev server (HTTPS)
EXPOSE 8080

# Create SSL generation and startup script
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'mkdir -p /app/ssl' >> /start.sh && \
    echo 'if [ ! -f "/app/ssl/key.pem" ] || [ ! -f "/app/ssl/cert.pem" ]; then' >> /start.sh && \
    echo '  echo "Generating SSL certificates for HTTPS development server..."' >> /start.sh && \
    echo '  openssl req -x509 -newkey rsa:2048 -keyout /app/ssl/key.pem -out /app/ssl/cert.pem -days 365 -nodes -subj "/C=US/ST=Dev/L=Local/O=ShowBuild/OU=Development/CN=192.168.51.210" -addext "subjectAltName=DNS:localhost,DNS:192.168.51.210,IP:127.0.0.1,IP:192.168.51.210,IP:0.0.0.0"' >> /start.sh && \
    echo '  echo "SSL certificates generated successfully!"' >> /start.sh && \
    echo 'fi' >> /start.sh && \
    echo 'export HTTPS=true' >> /start.sh && \
    echo 'export SSL_CRT_FILE=/app/ssl/cert.pem' >> /start.sh && \
    echo 'export SSL_KEY_FILE=/app/ssl/key.pem' >> /start.sh && \
    echo 'exec npm run serve -- --host 0.0.0.0 --port 8080' >> /start.sh && \
    chmod +x /start.sh

# Use SSL generation script to start server
CMD ["/start.sh"]

# Build stage for production
FROM node:18-alpine as build-stage

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine as production-stage

# Copy built application from build stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]