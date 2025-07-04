#!/usr/bin/env python3
import http.server
import socketserver
import urllib.request
import urllib.parse
from urllib.error import URLError
import json
import sys

class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/'):
            self.proxy_request('GET')
        else:
            # Serve static files
            super().do_GET()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.proxy_request('POST')
        else:
            self.send_error(404, "Not Found")
    
    def proxy_request(self, method):
        # Remove /api prefix and forward to backend
        backend_path = self.path[4:]  # Remove '/api'
        backend_url = f'http://192.168.51.210:8888{backend_path}'
        
        try:
            # Forward request headers
            headers = {}
            for header, value in self.headers.items():
                if header.lower() not in ['host', 'connection']:
                    headers[header] = value
            
            # Read request body for POST requests
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Create request
            req = urllib.request.Request(backend_url, data=body, headers=headers, method=method)
            
            # Forward request
            with urllib.request.urlopen(req) as response:
                # Send response status
                self.send_response(response.getcode())
                
                # Forward response headers
                for header, value in response.headers.items():
                    if header.lower() not in ['connection', 'transfer-encoding']:
                        self.send_header(header, value)
                self.end_headers()
                
                # Forward response body
                self.wfile.write(response.read())
                
        except URLError as e:
            self.send_error(502, f"Bad Gateway: {e}")
        except Exception as e:
            self.send_error(500, f"Internal Server Error: {e}")

if __name__ == "__main__":
    PORT = 8080
    
    # Change to the public directory to serve static files
    import os
    os.chdir('/mnt/process/show-build/disaffected-ui/public')
    
    with socketserver.TCPServer(("0.0.0.0", PORT), ProxyHTTPRequestHandler) as httpd:
        print(f"Server running at http://0.0.0.0:{PORT}/")
        print(f"Network access: http://192.168.51.210:{PORT}/")
        print("API requests will be proxied to http://192.168.51.210:8888")
        httpd.serve_forever()
