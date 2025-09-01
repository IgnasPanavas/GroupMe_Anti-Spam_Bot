#!/usr/bin/env python3
"""
Simple Health Check Web Server
Runs on the EC2 instance to serve health status data
"""

from flask import Flask, jsonify
from flask_cors import CORS
import subprocess
import json
import os

app = Flask(__name__)
CORS(app)

@app.route('/health')
def health():
    """Return basic health status"""
    try:
        # Run the health check script
        result = subprocess.run(['python3', 'ec2-health-check.py'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            health_data = json.loads(result.stdout)
            return jsonify({
                'status': 'healthy',
                'data': health_data
            })
        else:
            return jsonify({
                'status': 'unhealthy',
                'error': result.stderr
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/bot-status')
def bot_status():
    """Return bot-specific status"""
    try:
        result = subprocess.run(['python3', 'ec2-health-check.py'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            health_data = json.loads(result.stdout)
            bot_status = health_data.get('bot_status', {})
            
            return jsonify({
                'active': bot_status.get('running', False),
                'processes': bot_status.get('processes', []),
                'count': bot_status.get('count', 0),
                'timestamp': health_data.get('timestamp'),
                'uptime': health_data.get('uptime')
            })
        else:
            return jsonify({
                'active': False,
                'error': result.stderr
            }), 500
            
    except Exception as e:
        return jsonify({
            'active': False,
            'error': str(e)
        }), 500

@app.route('/')
def root():
    """Root endpoint"""
    return jsonify({
        'service': 'EC2 Health Check Server',
        'endpoints': ['/health', '/bot-status'],
        'timestamp': '2025-09-01T19:30:00Z'
    })

if __name__ == '__main__':
    # Run on port 8080 (make sure security group allows this)
    app.run(host='0.0.0.0', port=8080, debug=False)
