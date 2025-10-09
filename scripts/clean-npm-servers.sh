#!/bin/bash

# Clean NPM servers and caches for show-build
# This script performs a thorough cleanup of npm caches, node_modules, and restarts the dev server

set -e

echo "🧹 Starting thorough NPM cleanup for show-build..."

# Navigate to frontend directory
cd /mnt/process/show-build/disaffected-ui

# Stop any running dev servers
echo "🛑 Stopping running npm processes..."
pkill -f "vue-cli-service" || true
pkill -f "webpack-dev-server" || true

# Clear npm cache
echo "🗑️  Clearing npm cache..."
npm cache clean --force

# Remove node_modules
echo "📦 Removing node_modules..."
rm -rf node_modules

# Remove package-lock.json to force fresh resolution
echo "🔒 Removing package-lock.json..."
rm -f package-lock.json

# Clear Vue CLI cache
echo "🎨 Clearing Vue CLI cache..."
rm -rf node_modules/.cache

# Reinstall dependencies
echo "📥 Reinstalling npm packages..."
npm install

echo "✅ NPM cleanup complete!"
echo ""
echo "To restart the dev server, run:"
echo "  cd /mnt/process/show-build/disaffected-ui && npm run serve"
