#!/usr/bin/env python3
"""
WSGI entry point for SpamShield API
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app
from prediction_server import app

if __name__ == "__main__":
    app.run()
