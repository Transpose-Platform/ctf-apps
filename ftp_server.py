#!/usr/bin/env python3
"""
Permissive FTP Server for Chat Application
Runs in background with standard credentials
"""

import os
import sys
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import threading
import signal
import time

class PermissiveFTPHandler(FTPHandler):
    """Custom FTP handler with permissive settings"""
    
    def on_connect(self):
        print(f"FTP: Client connected from {self.remote_ip}:{self.remote_port}")
    
    def on_disconnect(self):
        print(f"FTP: Client disconnected from {self.remote_ip}:{self.remote_port}")
    
    def on_login(self, username):
        print(f"FTP: User '{username}' logged in from {self.remote_ip}")
    
    def on_logout(self, username):
        print(f"FTP: User '{username}' logged out")

def setup_ftp_server():
    """Setup and configure the FTP server"""
    
    # Create authorizer with maximum permissive settings
    authorizer = DummyAuthorizer()
    
    # Use filesystem root for maximum access
    ftp_root = "/"
    
    # Add admin user with full permissions to entire filesystem
    authorizer.add_user(
        "admin",           # username
        "admin",           # password
        ftp_root,          # home directory (filesystem root)
        perm="elradfmwMT"  # full permissions: read, write, execute, etc.
    )
    
    # Add anonymous user with read permissions to entire filesystem
    authorizer.add_anonymous(
        ftp_root,
        perm="elr"  # read and list permissions only
    )
    
    # Create handler with maximum permissive settings
    handler = PermissiveFTPHandler
    handler.authorizer = authorizer
    
    # Maximum permissive settings
    handler.banner = "Permissive FTP Server - Full System Access!"
    handler.max_cons = 256
    handler.max_cons_per_ip = 10
    handler.passive_ports = range(60000, 60100)
    handler.permit_foreign_addresses = True
    handler.permit_privileged_ports = True
    
    # Disable security restrictions
    handler.abstracted_fs = None  # Allow real filesystem access
    
    # Create and configure server
    server = FTPServer(("0.0.0.0", 2121), handler)
    server.max_cons = 256
    server.max_cons_per_ip = 10
    
    return server

def start_ftp_server():
    """Start the FTP server in a separate thread"""
    
    try:
        server = setup_ftp_server()
        
        print("="*50)
        print("PERMISSIVE FTP Server Starting...")
        print(f"Host: 0.0.0.0 (all interfaces)")
        print(f"Port: 2121")
        print(f"Root Directory: / (ENTIRE FILESYSTEM)")
        print("")
        print("⚠️  WARNING: FULL SYSTEM ACCESS ENABLED ⚠️")
        print("")
        print("Admin credentials:")
        print("  Username: admin")
        print("  Password: admin")
        print("  Permissions: Full read/write access to ENTIRE system")
        print("")
        print("Anonymous access:")
        print("  Username: anonymous")
        print("  Password: (any or none)")
        print("  Permissions: Read-only access to ENTIRE system")
        print("")
        print("Accessible paths include:")
        print("  /Users - All user directories")
        print("  /Applications - All applications")
        print("  /System - System files")
        print("  /tmp, /var, /etc - System directories")
        print("  / - Everything on the filesystem")
        print("="*50)
        
        # Start server
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\nFTP Server shutting down...")
    except Exception as e:
        print(f"FTP Server error: {e}")
    finally:
        if 'server' in locals():
            server.close_all()

def start_ftp_background():
    """Start FTP server in background thread"""
    
    ftp_thread = threading.Thread(target=start_ftp_server, daemon=True)
    ftp_thread.start()
    
    # Give server time to start
    time.sleep(2)
    
    return ftp_thread

if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--background":
        # Start in background mode
        ftp_thread = start_ftp_background()
        
        # Keep main thread alive
        try:
            while ftp_thread.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down FTP server...")
            sys.exit(0)
    else:
        # Start in foreground mode
        start_ftp_server()
