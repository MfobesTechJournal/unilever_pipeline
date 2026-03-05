#!/usr/bin/env python3
"""
Simple TCP Bridge for PostgreSQL
Forwards connections from cloud Grafana through a local proxy
"""

import socket
import threading
import selectors
import sys
from collections import defaultdict

class TCPBridge:
    def __init__(self, listen_host='0.0.0.0', listen_port=5555, target_host='localhost', target_port=5433):
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.target_host = target_host
        self.target_port = target_port
        self.selector = selectors.DefaultSelector()
        self.clients = defaultdict(dict)
        
    def accept_connection(self, sock):
        """Accept new client connection"""
        try:
            client_sock, client_addr = sock.accept()
            print(f"✓ New connection from {client_addr[0]}:{client_addr[1]}")
            
            # Connect to target
            target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_sock.setblocking(False)
            
            try:
                target_sock.connect_ex((self.target_host, self.target_port))
            except BlockingIOError:
                pass  # Expected for non-blocking
            
            # Register sockets
            self.selector.register(client_sock, selectors.EVENT_READ, data={'peer': target_sock, 'name': 'client'})
            self.selector.register(target_sock, selectors.EVENT_READ, data={'peer': client_sock, 'name': 'target'})
            
            self.clients[id(client_sock)] = {
                'client': client_sock,
                'target': target_sock,
                'addr': client_addr
            }
            
        except Exception as e:
            print(f"✗ Connection error: {e}")
    
    def forward_data(self, sock, peer_sock):
        """Forward data between sockets"""
        try:
            data = sock.recv(4096)
            if data:
                peer_sock.sendall(data)
                return True
            return False
        except Exception as e:
            print(f"✗ Forward error: {e}")
            return False
    
    def close_connection(self, sock):
        """Close a connection pair"""
        try:
            self.selector.unregister(sock)
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass
    
    def start(self):
        """Start the bridge server"""
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((self.listen_host, self.listen_port))
        server_sock.listen(5)
        server_sock.setblocking(False)
        
        self.selector.register(server_sock, selectors.EVENT_READ, data=None)
        
        print(f"\n{'='*80}")
        print("TCP BRIDGE STARTED")
        print(f"{'='*80}")
        print(f"Listening on: {self.listen_host}:{self.listen_port}")
        print(f"Forwarding to: {self.target_host}:{self.target_port}")
        print(f"{'='*80}\n")
        
        try:
            while True:
                events = self.selector.select(timeout=1)
                
                for key, mask in events:
                    if key.data is None:
                        # Server socket
                        self.accept_connection(key.fileobj)
                    else:
                        # Client or target socket
                        sock = key.fileobj
                        data = key.data
                        peer_sock = data['peer']
                        
                        if mask & selectors.EVENT_READ:
                            if not self.forward_data(sock, peer_sock):
                                # Connection closed
                                self.close_connection(sock)
                                if peer_sock in [self.selector.get_key(k).fileobj for k in self.selector.get_map()]:
                                    self.close_connection(peer_sock)
                
        except KeyboardInterrupt:
            print("\n\nShutting down bridge...")
        finally:
            self.selector.close()
            server_sock.close()

def check_postgresql():
    """Verify PostgreSQL is accessible"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='127.0.0.1',
            port=5433,
            user='postgres',
            password='123456',
            database='unilever_warehouse',
            timeout=5
        )
        conn.close()
        print("✓ PostgreSQL is accessible at localhost:5433")
        return True
    except ImportError:
        print("⚠ psycopg2 not available, skipping PostgreSQL check")
        return True
    except Exception as e:
        print(f"✗ PostgreSQL check failed: {e}")
        return False

def main():
    print("\n" + "="*80)
    print("LOCAL TCP BRIDGE FOR GRAFANA CLOUD")
    print("="*80 + "\n")
    
    # Check PostgreSQL
    if not check_postgresql():
        print("\nCannot proceed without accessible PostgreSQL")
        print("Ensure Docker containers are running: cd 11-infrastructure/network ; docker-compose up -d")
        return False
    
    # Create and start bridge
    bridge = TCPBridge(
        listen_host='0.0.0.0',
        listen_port=5555,
        target_host='127.0.0.1',
        target_port=5433
    )
    
    print("""
USAGE:
1. Make sure you can access this machine from Grafana Cloud (firewall/network)
   - If behind NAT, configure port forwarding: 5555 -> this machine
   
2. For Grafana Cloud datasource:
   - Update the datasource URL to: <your-public-ip>:5555
   - Rest of config remains the same (user: postgres, db: unilever_warehouse)
   
3. This terminal MUST stay open to maintain the bridge

For development (local testing):
   - Use localhost:5555 from local Grafana
   
For cloud access (requires port forwarding):
   - Obtain your public IP: curl ifconfig.co
   - Open port 5555 on your firewall/router
   - Use <public-ip>:5555 in Grafana Cloud datasource URL

Press Ctrl+C to stop the bridge
""")
    
    bridge.start()
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
