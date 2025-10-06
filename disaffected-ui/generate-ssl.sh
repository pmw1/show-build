#!/bin/bash

# Create SSL directory if it doesn't exist
mkdir -p /app/ssl

# Generate SSL certificates if they don't exist
if [ ! -f "/app/ssl/key.pem" ] || [ ! -f "/app/ssl/cert.pem" ]; then
    echo "Generating SSL certificates for HTTPS development server..."
    openssl req -x509 -newkey rsa:2048 -keyout /app/ssl/key.pem -out /app/ssl/cert.pem -days 365 -nodes -subj "/C=US/ST=Dev/L=Local/O=ShowBuild/OU=Development/CN=localhost"
    echo "SSL certificates generated successfully!"
fi

# Start the Vue development server
exec npm run serve