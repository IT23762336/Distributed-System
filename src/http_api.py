"""
Simple HTTP API server to query cluster status and messages
Runs alongside the main socket server on port +100 (e.g., 5100, 5101, 5102)
"""
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

logger = logging.getLogger("HTTPQueryAPI")


class QueryHandler(BaseHTTPRequestHandler):
    """Handle HTTP requests for status and messages"""
    
    def log_message(self, format, *args):
        """Suppress default HTTP logging"""
        pass
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            if self.path == "/messages":
                self.handle_messages()
            elif self.path == "/status":
                self.handle_status()
            else:
                self.send_error(404, "Endpoint not found")
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            self.send_error(500, str(e))
    
    def handle_messages(self):
        """Return all messages"""
        try:
            # Get message storage from server
            storage = self.server.cluster_server.message_storage
            
            # Get all messages synchronously
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            messages_data = loop.run_until_complete(storage.get_all_messages())
            loop.close()
            
            # Parse messages
            messages = []
            for msg_id, msg_json in messages_data:
                try:
                    msg = json.loads(msg_json)
                    messages.append({
                        "message_id": msg_id,
                        "content": msg.get("content", ""),
                        "sender": msg.get("sender", ""),
                        "timestamp": msg.get("timestamp", 0)
                    })
                except:
                    pass
            
            # Sort by timestamp
            messages.sort(key=lambda x: x["timestamp"])
            
            response = {
                "count": len(messages),
                "messages": messages
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            self.send_error(500, str(e))
    
    def handle_status(self):
        """Return cluster status"""
        try:
            server = self.server.cluster_server
            consensus = server.consensus
            failover = server.failover
            
            response = {
                "node_id": server.node_addr,
                "state": consensus.state.name if hasattr(consensus, 'state') else "UNKNOWN",
                "term": consensus.current_term if hasattr(consensus, 'current_term') else 0,
                "leader": consensus.leader_id if hasattr(consensus, 'leader_id') else None,
                "healthy_nodes": list(failover.healthy_nodes) if hasattr(failover, 'healthy_nodes') else []
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            self.send_error(500, str(e))


def start_http_api(cluster_server, http_port):
    """Start HTTP API server in background thread"""
    try:
        httpd = HTTPServer(('127.0.0.1', http_port), QueryHandler)
        httpd.cluster_server = cluster_server
        
        def run_server():
            logger.info(f"HTTP Query API started on port {http_port}")
            httpd.serve_forever()
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        
        return httpd
    except Exception as e:
        logger.error(f"Failed to start HTTP API: {e}")
        return None
