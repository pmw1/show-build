"""
API Documentation Router - Interactive endpoint documentation
Provides a comprehensive view of all available endpoints with examples
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from typing import Dict, List

router = APIRouter(prefix="/docs", tags=["documentation"])


def get_endpoint_documentation() -> Dict[str, List[Dict]]:
    """
    Returns structured documentation for all endpoints.
    """
    return {
        "Core System": [
            {
                "method": "GET",
                "path": "/",
                "description": "Landing page with basic API info",
                "auth": False,
                "example": None
            },
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check endpoint",
                "auth": False,
                "example": {"response": {"status": "healthy"}}
            },
            {
                "method": "GET",
                "path": "/show-info",
                "description": "Get show metadata",
                "auth": False,
                "example": {
                    "response": {
                        "show_title": "Disaffected",
                        "show_description": "A show about current events and technology.",
                        "episodes_base_path": "/home/episodes"
                    }
                }
            }
        ],
        "Authentication": [
            {
                "method": "POST",
                "path": "/login",
                "description": "Login with username/password to get JWT token",
                "auth": False,
                "example": {
                    "request": {"username": "user@example.com", "password": "secret"},
                    "response": {"access_token": "eyJ...", "token_type": "bearer"}
                }
            },
            {
                "method": "POST",
                "path": "/users",
                "description": "Create new user account (admin only)",
                "auth": True,
                "example": {
                    "request": {"username": "newuser@example.com", "password": "password123"},
                    "response": {"username": "newuser@example.com", "id": 123}
                }
            },
            {
                "method": "GET",
                "path": "/users",
                "description": "List all users (admin only)",
                "auth": True,
                "example": None
            },
            {
                "method": "POST",
                "path": "/apikey",
                "description": "Generate API key for machine-to-machine auth",
                "auth": True,
                "example": {
                    "request": {"client_name": "automation-script"},
                    "response": {"api_key": "sk_live_...", "client_name": "automation-script"}
                }
            }
        ],
        "Episodes - File-Based (Legacy)": [
            {
                "method": "GET",
                "path": "/episodes",
                "description": "List all episodes from filesystem",
                "auth": False,
                "example": {
                    "response": {
                        "episodes": [
                            {"episode_number": "0237", "title": "Episode Title", "airdate": "2024-01-01"}
                        ]
                    }
                }
            },
            {
                "method": "GET",
                "path": "/episodes/{episode_number}/rundown",
                "description": "Get rundown items with YAML frontmatter",
                "auth": False,
                "example": None
            },
            {
                "method": "GET",
                "path": "/episodes/{episode_number}/info",
                "description": "Get episode info from info.md",
                "auth": True,
                "example": None
            },
            {
                "method": "PUT",
                "path": "/episodes/{episode_number}/info",
                "description": "Update episode info in info.md",
                "auth": True,
                "example": {
                    "request": {"title": "New Title", "airdate": "2024-01-01"}
                }
            }
        ],
        "Episodes - Database (Modern)": [
            {
                "method": "POST",
                "path": "/episodes/{episode_id}/compile-script",
                "description": "Start background script compilation with Celery",
                "auth": True,
                "example": {
                    "request": {"output_format": "html", "include_cues": True},
                    "response": {
                        "job_id": "abc123",
                        "status": "started",
                        "websocket_url": "/ws/{client_id}"
                    }
                }
            },
            {
                "method": "GET",
                "path": "/jobs/{job_id}/status",
                "description": "Check background job status",
                "auth": True,
                "example": {
                    "response": {
                        "job_id": "abc123",
                        "status": "completed",
                        "progress": 100,
                        "result": {}
                    }
                }
            }
        ],
        "Rundown Management": [
            {
                "method": "POST",
                "path": "/rundown/{episode_number}/reorder",
                "description": "Reorder rundown segments",
                "auth": False,
                "example": {
                    "request": {
                        "segments": [
                            {"filename": "10-opening.md", "order": 1}
                        ]
                    }
                }
            },
            {
                "method": "POST",
                "path": "/rundown/{episode_number}/item",
                "description": "Create new rundown item",
                "auth": False,
                "example": {
                    "request": {
                        "title": "New Segment",
                        "type": "segment",
                        "slug": "new-segment",
                        "duration": "00:05:00"
                    }
                }
            }
        ],
        "Media Processing": [
            {
                "method": "POST",
                "path": "/proc_vid",
                "description": "Upload video file for processing (max 50MB)",
                "auth": False,
                "example": {
                    "request": "multipart/form-data with file, type, id, episode, slug"
                }
            },
            {
                "method": "POST",
                "path": "/upload_image",
                "description": "Upload image file",
                "auth": False,
                "example": {
                    "request": "multipart/form-data with file, id, episode, slug"
                }
            },
            {
                "method": "POST",
                "path": "/next-id",
                "description": "Generate unique asset ID",
                "auth": False,
                "example": {
                    "request": {"slug": "test-asset", "type": "video"},
                    "response": {"id": "12345"}
                }
            }
        ],
        "Asset Management": [
            {
                "method": "GET",
                "path": "/api/assets",
                "description": "List assets in directory tree",
                "auth": True,
                "example": None
            },
            {
                "method": "POST",
                "path": "/api/assets/folder",
                "description": "Create new folder",
                "auth": True,
                "example": {
                    "request": {"path": "/videos/new-folder"}
                }
            },
            {
                "method": "POST",
                "path": "/api/assets/upload",
                "description": "Upload multiple files",
                "auth": True,
                "example": None
            },
            {
                "method": "DELETE",
                "path": "/api/assets",
                "description": "Delete asset",
                "auth": True,
                "example": {
                    "request": {"path": "/videos/old-file.mp4"}
                }
            }
        ],
        "MQTT Messaging": [
            {
                "method": "POST",
                "path": "/publish/",
                "description": "Publish message to MQTT broker",
                "auth": False,
                "example": {
                    "request": {"topic": "episode/update", "message": "Episode 237 updated"},
                    "response": {"status": "published"}
                }
            },
            {
                "method": "GET",
                "path": "/listen/",
                "description": "Subscribe to MQTT topic",
                "auth": False,
                "example": {
                    "request": {"topic": "episode/+/status"}
                }
            }
        ],
        "WebSocket": [
            {
                "method": "WebSocket",
                "path": "/ws/{client_id}",
                "description": "Real-time updates for job status and live production",
                "auth": False,
                "example": {
                    "connect": "ws://localhost:8888/ws/my-client-123",
                    "message": {"type": "job_update", "job_id": "abc123", "progress": 50}
                }
            }
        ],
        "API Configuration": [
            {
                "method": "GET",
                "path": "/api-configs",
                "description": "Get all API configurations",
                "auth": True,
                "example": None
            },
            {
                "method": "POST",
                "path": "/api-configs",
                "description": "Save API configurations",
                "auth": True,
                "example": {
                    "request": {"service": "youtube", "api_key": "..."}
                }
            },
            {
                "method": "POST",
                "path": "/test/{service}",
                "description": "Test external API connection",
                "auth": True,
                "example": {
                    "response": {"service": "youtube", "status": "connected"}
                }
            }
        ],
        "Templates": [
            {
                "method": "GET",
                "path": "/api/templates",
                "description": "List all templates",
                "auth": True,
                "example": None
            },
            {
                "method": "POST",
                "path": "/api/templates",
                "description": "Create new template",
                "auth": True,
                "example": {
                    "request": {"name": "Standard Episode", "content": "..."}
                }
            }
        ]
    }


@router.get("/api", response_class=HTMLResponse)
async def api_documentation():
    """
    Interactive API documentation with all endpoints and examples.
    """
    endpoints = get_endpoint_documentation()
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Show-Build API Documentation</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }
            
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-bottom: 30px;
            }
            
            h2 {
                color: #34495e;
                margin-top: 40px;
                border-bottom: 1px solid #ddd;
                padding-bottom: 5px;
            }
            
            .endpoint {
                background: white;
                margin: 15px 0;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border-left: 4px solid #3498db;
            }
            
            .method {
                display: inline-block;
                padding: 3px 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                margin-right: 10px;
            }
            
            .method.GET { background: #61affe; color: white; }
            .method.POST { background: #49cc90; color: white; }
            .method.PUT { background: #fca130; color: white; }
            .method.DELETE { background: #f93e3e; color: white; }
            .method.WebSocket { background: #9b59b6; color: white; }
            
            .path {
                font-family: 'Courier New', monospace;
                font-weight: bold;
                color: #2c3e50;
            }
            
            .description {
                color: #666;
                margin: 10px 0;
            }
            
            .auth-required {
                display: inline-block;
                background: #e74c3c;
                color: white;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 11px;
                margin-left: 10px;
            }
            
            .example {
                background: #2c3e50;
                color: #ecf0f1;
                padding: 10px;
                border-radius: 5px;
                margin-top: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                overflow-x: auto;
            }
            
            .example-label {
                color: #3498db;
                font-weight: bold;
                margin-top: 10px;
                font-size: 12px;
            }
            
            .info-box {
                background: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 5px;
                padding: 15px;
                margin: 20px 0;
                color: #155724;
            }
            
            .warning-box {
                background: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 5px;
                padding: 15px;
                margin: 20px 0;
                color: #856404;
            }
            
            pre {
                margin: 0;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            
            .nav {
                background: white;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 30px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .nav a {
                color: #3498db;
                text-decoration: none;
                margin-right: 20px;
            }
            
            .nav a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <h1>🎬 Show-Build API Documentation</h1>
        
        <div class="info-box">
            <strong>Server IP:</strong> 192.168.51.210<br>
            <strong>Frontend URL:</strong> http://192.168.51.210:8080<br>
            <strong>Backend API URL:</strong> http://192.168.51.210:8888<br>
            <strong>WebSocket URL:</strong> ws://192.168.51.210:8888/ws/{client_id}<br>
            <strong>MQTT Broker:</strong> 192.168.51.210:1883<br>
            <strong>Authentication:</strong> JWT Bearer token or API Key in headers
        </div>
        
        <div class="nav">
            <strong>Quick Navigation:</strong>
    """
    
    # Add navigation links
    for category in endpoints.keys():
        anchor = category.replace(" ", "-").replace("-", "_").lower()
        html_content += f'<a href="#{anchor}">{category}</a>'
    
    html_content += """
        </div>
        
        <div class="warning-box">
            <strong>⚠️ Dual Architecture:</strong> This system has both legacy file-based endpoints and modern database-driven endpoints. 
            The database endpoints offer background processing and real-time updates via WebSocket.
        </div>
    """
    
    # Generate endpoint documentation
    for category, endpoint_list in endpoints.items():
        anchor = category.replace(" ", "-").replace("-", "_").lower()
        html_content += f'<h2 id="{anchor}">{category}</h2>'
        
        for endpoint in endpoint_list:
            html_content += '<div class="endpoint">'
            html_content += f'<span class="method {endpoint["method"]}">{endpoint["method"]}</span>'
            html_content += f'<span class="path">{endpoint["path"]}</span>'
            
            if endpoint.get("auth"):
                html_content += '<span class="auth-required">🔒 AUTH REQUIRED</span>'
            
            html_content += f'<div class="description">{endpoint["description"]}</div>'
            
            if endpoint.get("example"):
                if isinstance(endpoint["example"], dict):
                    if "request" in endpoint["example"]:
                        html_content += '<div class="example-label">Request Example:</div>'
                        html_content += '<div class="example">'
                        if isinstance(endpoint["example"]["request"], str):
                            html_content += f'<pre>{endpoint["example"]["request"]}</pre>'
                        else:
                            import json
                            html_content += f'<pre>{json.dumps(endpoint["example"]["request"], indent=2)}</pre>'
                        html_content += '</div>'
                    
                    if "response" in endpoint["example"]:
                        html_content += '<div class="example-label">Response Example:</div>'
                        html_content += '<div class="example">'
                        import json
                        html_content += f'<pre>{json.dumps(endpoint["example"]["response"], indent=2)}</pre>'
                        html_content += '</div>'
                    
                    # Special cases
                    if "connect" in endpoint["example"]:
                        html_content += '<div class="example-label">Connection Example:</div>'
                        html_content += '<div class="example">'
                        html_content += f'<pre>{endpoint["example"]["connect"]}</pre>'
                        html_content += '</div>'
                    
                    if "message" in endpoint["example"]:
                        html_content += '<div class="example-label">Message Example:</div>'
                        html_content += '<div class="example">'
                        import json
                        html_content += f'<pre>{json.dumps(endpoint["example"]["message"], indent=2)}</pre>'
                        html_content += '</div>'
            
            html_content += '</div>'
    
    # Add authentication section
    html_content += """
        <h2>Authentication Guide</h2>
        
        <div class="info-box">
            <h3>JWT Token Authentication (Browser/Frontend)</h3>
            <ol>
                <li>POST to /login with username and password</li>
                <li>Receive JWT token in response</li>
                <li>Include token in Authorization header: <code>Bearer {token}</code></li>
                <li>Tokens expire after 48 hours (configurable)</li>
            </ol>
        </div>
        
        <div class="info-box">
            <h3>API Key Authentication (Machine-to-Machine)</h3>
            <ol>
                <li>POST to /apikey to generate a key (requires admin)</li>
                <li>Include key in X-API-Key header: <code>X-API-Key: {api_key}</code></li>
                <li>Keys don't expire unless manually revoked</li>
            </ol>
        </div>
        
        <h2>WebSocket Connection</h2>
        
        <div class="example">
// JavaScript WebSocket connection example
const ws = new WebSocket('ws://192.168.51.210:8888/ws/my-client-123');

ws.onopen = () => {
    console.log('Connected to WebSocket');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
    
    // Handle different message types
    switch(data.type) {
        case 'job_update':
            console.log(`Job ${data.job_id} progress: ${data.progress}%`);
            break;
        case 'compilation_complete':
            console.log('Script compilation finished!');
            break;
    }
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};
        </div>
        
        <h2>MQTT Integration</h2>
        
        <div class="info-box">
            <h3>MQTT Broker Configuration</h3>
            <ul>
                <li><strong>Host:</strong> 192.168.51.210 (or container name: mqtt-broker from within Docker)</li>
                <li><strong>Port:</strong> 1883</li>
                <li><strong>WebSocket Port:</strong> 9001</li>
                <li><strong>Topics:</strong> Use hierarchical topics like <code>episode/237/status</code></li>
            </ul>
        </div>
        
        <div class="example">
# Python MQTT client example
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect("192.168.51.210", 1883, 60)

# Publish a message
client.publish("episode/237/status", "processing")

# Subscribe to updates
def on_message(client, userdata, msg):
    print(f"{msg.topic}: {msg.payload.decode()}")

client.on_message = on_message
client.subscribe("episode/+/status")
client.loop_forever()
        </div>
        
        <footer style="margin-top: 60px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; text-align: center;">
            <p>Show-Build API v2.0 - Segment-Centric Architecture</p>
            <p>For more details, see <code>/docs/API_ENDPOINTS.md</code> and <code>/docs/PRODUCTION_HIERARCHY.md</code></p>
        </footer>
    </body>
    </html>
    """
    
    return html_content


@router.get("/", response_class=HTMLResponse)
async def documentation_index():
    """
    Documentation index page with links to all documentation resources.
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Show-Build Documentation</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 40px 20px;
                background: #f5f5f5;
            }
            
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }
            
            .doc-card {
                background: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-decoration: none;
                color: inherit;
                display: block;
                transition: transform 0.2s;
            }
            
            .doc-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }
            
            .doc-card h2 {
                color: #3498db;
                margin-top: 0;
            }
            
            .doc-card p {
                color: #666;
                margin-bottom: 0;
            }
            
            .badge {
                display: inline-block;
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                margin-left: 10px;
            }
            
            .badge.new { background: #27ae60; color: white; }
            .badge.updated { background: #f39c12; color: white; }
            .badge.interactive { background: #9b59b6; color: white; }
        </style>
    </head>
    <body>
        <h1>📚 Show-Build Documentation Hub</h1>
        
        <a href="/docs/api" class="doc-card">
            <h2>API Documentation <span class="badge interactive">INTERACTIVE</span></h2>
            <p>Complete API reference with all endpoints, authentication methods, and live examples. 
            Includes WebSocket and MQTT integration guides.</p>
        </a>
        
        <div class="doc-card">
            <h2>Production Hierarchy <span class="badge new">NEW</span></h2>
            <p>Understand the segment-centric architecture: Organization → Show → Season → Episode → Block → Segment. 
            Located at <code>/docs/PRODUCTION_HIERARCHY.md</code></p>
        </div>
        
        <div class="doc-card">
            <h2>API Endpoints Reference</h2>
            <p>Detailed endpoint documentation with request/response examples and architectural insights. 
            Located at <code>/docs/API_ENDPOINTS.md</code></p>
        </div>
        
        <div class="doc-card">
            <h2>Development TODO</h2>
            <p>Current development tasks, open architectural questions, and future features. 
            Located at <code>/TODO.md</code></p>
        </div>
        
        <div class="doc-card">
            <h2>Database Schema <span class="badge updated">V2</span></h2>
            <p>New segment-centric database models with AssetID system. 
            See <code>/app/models_v2.py</code> and <code>/app/models_assetid.py</code></p>
        </div>
        
        <div class="doc-card">
            <h2>AssetID Service</h2>
            <p>Central ID generation and tracking system with full history and relationships. 
            Located at <code>/app/services/asset_id.py</code></p>
        </div>
        
        <div class="doc-card" style="background: #e8f5e9;">
            <h2>Quick Links</h2>
            <p>
                <strong>FastAPI Swagger:</strong> <a href="/docs">Auto-generated OpenAPI docs</a><br>
                <strong>ReDoc:</strong> <a href="/redoc">Alternative API documentation</a><br>
                <strong>Health Check:</strong> <a href="/health">System health status</a>
            </p>
        </div>
        
        <footer style="margin-top: 60px; text-align: center; color: #666;">
            <p>Show-Build v2.0 - Development Fork (Branch: dev-fork)</p>
        </footer>
    </body>
    </html>
    """