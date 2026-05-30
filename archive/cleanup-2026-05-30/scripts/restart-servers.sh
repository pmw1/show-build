#!/bin/bash

# Restart Show-Build servers
echo "🔄 Restarting Show-Build servers..."

# Stop backend services
echo "⏹️  Stopping Docker services..."
docker compose down 2>/dev/null

# Start backend services
echo "▶️  Starting backend services..."
docker compose up -d

# Wait for backend to be healthy
echo "⏳ Waiting for backend..."
for i in {1..10}; do
    if curl -s http://192.168.51.210:8888/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy"
        break
    fi
    sleep 1
done

# Start frontend dev server in background
echo "▶️  Starting frontend server..."
cd disaffected-ui
npm run serve > /dev/null 2>&1 &
FRONTEND_PID=$!

# Wait for frontend
echo "⏳ Waiting for frontend..."
for i in {1..15}; do
    if curl -s http://192.168.51.210:8080 > /dev/null 2>&1; then
        echo "✅ Frontend is running"
        break
    fi
    sleep 1
done

echo ""
echo "🚀 Servers restarted successfully!"
echo "   Backend:  http://192.168.51.210:8888"
echo "   Frontend: http://192.168.51.210:8080"
echo "   API Docs: http://192.168.51.210:8888/docs/api"
echo ""
echo "Frontend PID: $FRONTEND_PID (running in background)"