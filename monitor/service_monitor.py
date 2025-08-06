#!/usr/bin/env python3
"""
Service Monitor - Continuous monitoring of IP addresses and ports
Pings services every second and logs results with persistence
"""

import json
import socket
import time
import os
import sys
from datetime import datetime
from typing import List, Dict, Tuple
import threading
import signal
import urllib.request
import urllib.error

class ServiceMonitor:
    def __init__(self, config_file="monitor_config.json", results_file="monitor_results.json"):
        self.config_file = config_file
        self.results_file = results_file
        self.services = []
        self.running = False
        self.success_counts = {}  # Store success counts per IP:port
        
        # Load configuration
        self.load_config()
        
        # Load previous results if they exist
        self.load_previous_state()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def load_config(self):
        """Load monitoring configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.services = config.get('services', [])
                    print(f"Loaded {len(self.services)} services from config")
            else:
                # Create default configuration
                self.create_default_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """Create default monitoring configuration"""
        default_services = [
            {"ip": "127.0.0.1", "port": 5000, "name": "Chat App"},
            {"ip": "127.0.0.1", "port": 2121, "name": "FTP Server"},
            {"ip": "127.0.0.1", "port": 11434, "name": "Ollama API"},
            {"ip": "127.0.0.1", "port": 5432, "name": "PostgreSQL"},
            {"ip": "8.8.8.8", "port": 53, "name": "Google DNS"},
            {"ip": "1.1.1.1", "port": 53, "name": "Cloudflare DNS"},
        ]
        
        config = {
            "services": default_services,
            "check_interval": 1,
            "timeout": 5
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.services = default_services
        print(f"Created default config with {len(default_services)} services")
    
    def load_previous_state(self):
        """Load previous success counts from results file"""
        if not os.path.exists(self.results_file):
            print("No previous results file found, starting fresh")
            self.success_counts = {}
            return
        
        try:
            with open(self.results_file, 'r') as f:
                data = json.load(f)
                self.success_counts = data.get('success_counts', {})
                
            total_successes = sum(self.success_counts.values())
            print(f"Loaded previous state: {len(self.success_counts)} services, {total_successes} total successful pings")
            
            # Display current counts
            for service_key, count in self.success_counts.items():
                print(f"  {service_key}: {count} successful pings")
                
        except Exception as e:
            print(f"Error loading previous state: {e}")
            self.success_counts = {}
    
    def check_http_service(self, ip: str, port: int, timeout: int = 5) -> Tuple[bool, float, str]:
        """Check if HTTP service is alive by requesting the page"""
        start_time = time.time()
        
        try:
            url = f"http://{ip}:{port}/"
            
            # Create request with timeout
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'ServiceMonitor/1.0')
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_time = (time.time() - start_time) * 1000
                status_code = response.getcode()
                
                if 200 <= status_code < 400:
                    return True, response_time, f"HTTP {status_code} - Page loaded successfully"
                else:
                    return False, response_time, f"HTTP {status_code} - Unexpected status code"
                    
        except urllib.error.HTTPError as e:
            response_time = (time.time() - start_time) * 1000
            return False, response_time, f"HTTP {e.code} - {e.reason}"
        except urllib.error.URLError as e:
            response_time = (time.time() - start_time) * 1000
            return False, response_time, f"URL Error: {e.reason}"
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return False, response_time, f"HTTP Error: {e}"
    
    def check_health_service(self, ip: str, port: int, timeout: int = 5) -> Tuple[bool, float, str]:
        """Check service health via health endpoint or socket connection"""
        start_time = time.time()
        
        # First try health endpoint
        try:
            health_url = f"http://{ip}:{port}/health"
            req = urllib.request.Request(health_url)
            req.add_header('User-Agent', 'ServiceMonitor/1.0')
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_time = (time.time() - start_time) * 1000
                status_code = response.getcode()
                
                if status_code == 200:
                    return True, response_time, "Health check passed"
                else:
                    return False, response_time, f"Health check failed - HTTP {status_code}"
                    
        except:
            # Fall back to socket connection check
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                
                result = sock.connect_ex((ip, port))
                sock.close()
                
                response_time = (time.time() - start_time) * 1000
                
                if result == 0:
                    return True, response_time, "Socket connection successful"
                else:
                    return False, response_time, f"Connection failed (error {result})"
                    
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                return False, response_time, f"Connection error: {e}"
    
    def check_service(self, service: Dict, timeout: int = 5) -> Tuple[bool, float, str]:
        """Check service based on port type"""
        ip = service['ip']
        port = service['port']
        
        if port == 5000:
            # HTTP page load check
            return self.check_http_service(ip, port, timeout)
        elif port == 5001:
            # Health check
            return self.check_health_service(ip, port, timeout)
        else:
            # Default socket connection check
            start_time = time.time()
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                
                result = sock.connect_ex((ip, port))
                sock.close()
                
                response_time = (time.time() - start_time) * 1000
                
                if result == 0:
                    return True, response_time, "Connected successfully"
                else:
                    return False, response_time, f"Connection failed (error {result})"
                    
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                return False, response_time, f"Connection error: {e}"
    
    def log_result(self, service: Dict, is_alive: bool, response_time: float, message: str):
        """Update success count and save to file"""
        timestamp = datetime.now().isoformat()
        service_key = f"{service['ip']}:{service['port']}"
        
        # Update success count only if service is alive
        if is_alive:
            if service_key not in self.success_counts:
                self.success_counts[service_key] = 0
            self.success_counts[service_key] += 1
        
        # Save updated counts to file
        self.save_results()
        
        # Print status with current success count
        status = "✓" if is_alive else "✗"
        current_count = self.success_counts.get(service_key, 0)
        print(f"{timestamp} {status} {service['name']} ({service_key}) - {response_time:.1f}ms - {message} [Total successful: {current_count}]")
    
    def monitor_cycle(self):
        """Perform one monitoring cycle for all services"""
        for service in self.services:
            is_alive, response_time, message = self.check_service(service)
            self.log_result(service, is_alive, response_time, message)
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        self.running = True
        
        print("="*60)
        print("SERVICE MONITOR STARTED")
        print("="*60)
        print(f"Monitoring {len(self.services)} services")
        print(f"Check interval: 1 second")
        print(f"Results file: {self.results_file}")
        print(f"Config file: {self.config_file}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("Status format: [timestamp] [status] [service] - [response_time] - [message]")
        print("="*60)
        
        try:
            while self.running:
                start_time = time.time()
                
                # Perform monitoring cycle
                self.monitor_cycle()
                
                # Calculate sleep time to maintain 1-second intervals
                elapsed = time.time() - start_time
                sleep_time = max(0, 1.0 - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print("\nShutdown requested...")
        finally:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop monitoring gracefully"""
        self.running = False
        print("\nMonitoring stopped")
        print(f"Results saved to: {self.results_file}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}, shutting down...")
        self.stop_monitoring()
        sys.exit(0)
    
    def save_results(self):
        """Save success counts to file"""
        try:
            # Create service mapping for display
            service_details = {}
            for service in self.services:
                key = f"{service['ip']}:{service['port']}"
                service_details[key] = {
                    "name": service['name'],
                    "ip": service['ip'],
                    "port": service['port'],
                    "successful_pings": self.success_counts.get(key, 0)
                }
            
            data = {
                "last_updated": datetime.now().isoformat(),
                "success_counts": self.success_counts,
                "service_details": service_details
            }
            
            with open(self.results_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving results: {e}")
    
    def show_stats(self):
        """Show monitoring statistics"""
        if not os.path.exists(self.results_file):
            print("No results file found")
            return
        
        try:
            with open(self.results_file, 'r') as f:
                data = json.load(f)
            
            success_counts = data.get('success_counts', {})
            service_details = data.get('service_details', {})
            last_updated = data.get('last_updated', 'Unknown')
            
            total_successes = sum(success_counts.values())
            
            print("="*60)
            print("MONITORING STATISTICS")
            print("="*60)
            print(f"Last updated: {last_updated}")
            print(f"Total successful pings: {total_successes}")
            print(f"Services monitored: {len(success_counts)}")
            print("\nSuccess counts per service:")
            
            for service_key, details in service_details.items():
                print(f"  {details['name']} ({service_key}):")
                print(f"    Successful pings: {details['successful_pings']}")
            
        except Exception as e:
            print(f"Error calculating stats: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "stats":
            monitor = ServiceMonitor()
            monitor.show_stats()
            return
        elif sys.argv[1] == "config":
            monitor = ServiceMonitor()
            print(f"Config file: {monitor.config_file}")
            print(f"Services: {len(monitor.services)}")
            for service in monitor.services:
                print(f"  - {service['name']}: {service['ip']}:{service['port']}")
            return
    
    # Start monitoring
    monitor = ServiceMonitor()
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
