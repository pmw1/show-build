"""
WebSocket endpoints for real-time processing updates.
Server pushes job status and progress to connected clients.
"""
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import List, Dict
import json
import asyncio
import logging
from database import get_db
from models import ProcessingJob, ProcessingStatus
from auth.utils import get_current_user_or_key
import redis
import os

logger = logging.getLogger(__name__)

# Redis client for pubsub
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

class ConnectionManager:
    """Manage WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new WebSocket connection."""
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)
        logger.info(f"Client {client_id} connected via WebSocket")
        
    def disconnect(self, websocket: WebSocket, client_id: str):
        """Remove WebSocket connection."""
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
        logger.info(f"Client {client_id} disconnected from WebSocket")
        
    async def send_personal_message(self, message: str, client_id: str):
        """Send message to specific client."""
        if client_id in self.active_connections:
            for websocket in self.active_connections[client_id]:
                try:
                    await websocket.send_text(message)
                except:
                    # Remove broken connection
                    self.active_connections[client_id].remove(websocket)
                    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients."""
        for client_connections in self.active_connections.values():
            for websocket in client_connections:
                try:
                    await websocket.send_text(message)
                except:
                    # Connection broken, will be cleaned up later
                    pass

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time job updates."""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types from client
            if message.get("type") == "subscribe_job":
                job_id = message.get("job_id")
                await handle_job_subscription(websocket, client_id, job_id)
            elif message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(websocket, client_id)

async def handle_job_subscription(websocket: WebSocket, client_id: str, job_id: str):
    """Handle client subscription to specific job updates."""
    try:
        # Send initial job status
        await send_job_status_update(client_id, job_id)
        
        # Set up Redis pubsub for job updates
        pubsub = redis_client.pubsub()
        pubsub.subscribe(f"job_updates:{job_id}")
        
        # Listen for updates in background
        asyncio.create_task(listen_for_job_updates(pubsub, client_id, job_id))
        
    except Exception as e:
        logger.error(f"Error subscribing to job {job_id}: {e}")

async def listen_for_job_updates(pubsub, client_id: str, job_id: str):
    """Listen for Redis pubsub job updates and forward to WebSocket."""
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await manager.send_personal_message(
                    json.dumps({
                        "type": "job_update",
                        "job_id": job_id,
                        "data": data
                    }),
                    client_id
                )
    except Exception as e:
        logger.error(f"Error listening for job updates: {e}")
    finally:
        pubsub.close()

async def send_job_status_update(client_id: str, job_id: str):
    """Send current job status to client."""
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.job_id == job_id).first()
        if job:
            status_data = {
                "job_id": job_id,
                "status": job.status,
                "progress": job.progress,
                "job_type": job.job_type,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error_message": job.error_message,
                "result": job.result
            }
            
            await manager.send_personal_message(
                json.dumps({
                    "type": "job_status",
                    "job_id": job_id,
                    "data": status_data
                }),
                client_id
            )
    finally:
        db.close()

def publish_job_update(job_id: str, status: str, progress: int = 0, message: str = "", result: Dict = None):
    """Publish job update to Redis for WebSocket broadcasting."""
    update_data = {
        "status": status,
        "progress": progress,
        "message": message,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    if result:
        update_data["result"] = result
    
    try:
        redis_client.publish(f"job_updates:{job_id}", json.dumps(update_data))
    except Exception as e:
        logger.error(f"Failed to publish job update: {e}")

# Utility functions for Celery tasks to publish updates
def update_job_progress(job_id: str, progress: int, message: str = ""):
    """Update job progress and broadcast to WebSocket clients."""
    publish_job_update(job_id, "running", progress, message)

def complete_job(job_id: str, result: Dict):
    """Mark job as completed and broadcast result."""
    publish_job_update(job_id, "completed", 100, "Job completed successfully", result)

def fail_job(job_id: str, error_message: str):
    """Mark job as failed and broadcast error."""
    publish_job_update(job_id, "failed", 0, error_message)