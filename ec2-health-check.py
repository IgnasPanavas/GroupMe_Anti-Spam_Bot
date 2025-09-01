#!/usr/bin/env python3
"""
EC2 Instance Health Check Script
This script runs on the EC2 instance and reports its health status
"""

import json
import subprocess
import psutil
import os
import time
from datetime import datetime

def check_bot_process():
    """Check if the GroupMe bot process is running"""
    try:
        # Look for Python processes that might be running the bot
        bot_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'python' or proc.info['name'] == 'python3':
                    cmdline = proc.info['cmdline']
                    if cmdline and any('bot' in arg.lower() or 'groupme' in arg.lower() for arg in cmdline):
                        bot_processes.append({
                            'pid': proc.info['pid'],
                            'cmdline': ' '.join(cmdline),
                            'cpu_percent': proc.cpu_percent(),
                            'memory_percent': proc.memory_percent()
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return {
            'running': len(bot_processes) > 0,
            'processes': bot_processes,
            'count': len(bot_processes)
        }
    except Exception as e:
        return {
            'running': False,
            'error': str(e)
        }

def check_system_health():
    """Check basic system health metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': round(memory.available / (1024**3), 2),
            'disk_percent': disk.percent,
            'disk_free_gb': round(disk.free / (1024**3), 2)
        }
    except Exception as e:
        return {
            'error': str(e)
        }

def check_network():
    """Check network connectivity"""
    try:
        # Check if we can reach external services
        import requests
        test_urls = [
            'https://httpbin.org/status/200',
            'https://api.groupme.com/v3/bots'
        ]
        
        network_status = {}
        for url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                network_status[url] = {
                    'reachable': True,
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds()
                }
            except Exception as e:
                network_status[url] = {
                    'reachable': False,
                    'error': str(e)
                }
        
        return network_status
    except Exception as e:
        return {
            'error': str(e)
        }

def main():
    """Main health check function"""
    health_data = {
        'timestamp': datetime.now().isoformat(),
        'instance_id': os.environ.get('INSTANCE_ID', 'unknown'),
        'hostname': os.uname().nodename,
        'uptime': time.time() - psutil.boot_time(),
        'bot_status': check_bot_process(),
        'system_health': check_system_health(),
        'network': check_network()
    }
    
    # Print as JSON for easy parsing
    print(json.dumps(health_data, indent=2))

if __name__ == '__main__':
    main()
