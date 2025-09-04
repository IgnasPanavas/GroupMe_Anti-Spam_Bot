#!/bin/bash

# SpamShield Platform Management Script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/venv"
PLATFORM_DIR="$SCRIPT_DIR/spamshield_platform"
LOG_DIR="$PLATFORM_DIR/logs"
PID_FILE="$LOG_DIR/platform.pid"
LOG_FILE="$LOG_DIR/platform.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

start() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "SpamShield Platform is already running (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    echo "Starting SpamShield Platform..."
    cd "$SCRIPT_DIR"
    source "$VENV_PATH/bin/activate"
    
    nohup python "$PLATFORM_DIR/main.py" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    
    sleep 3
    if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "SpamShield Platform started successfully (PID: $(cat $PID_FILE))"
        return 0
    else
        echo "Failed to start SpamShield Platform"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "SpamShield Platform is not running"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    echo "Stopping SpamShield Platform (PID: $PID)..."
    
    if kill -0 "$PID" 2>/dev/null; then
        kill -TERM "$PID"
        sleep 5
        
        if kill -0 "$PID" 2>/dev/null; then
            echo "Graceful shutdown failed, forcing..."
            kill -KILL "$PID"
        fi
        
        rm -f "$PID_FILE"
        echo "SpamShield Platform stopped"
    else
        echo "Process not found, cleaning up PID file"
        rm -f "$PID_FILE"
    fi
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        PID=$(cat "$PID_FILE")
        echo "SpamShield Platform is running (PID: $PID)"
        
        # Test health endpoint
        if curl -s http://localhost:8000/health > /dev/null; then
            echo "Health check: ✅ PASSED"
        else
            echo "Health check: ❌ FAILED"
        fi
        return 0
    else
        echo "SpamShield Platform is not running"
        [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
        return 1
    fi
}

restart() {
    echo "Restarting SpamShield Platform..."
    stop
    sleep 2
    start
}

logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "Log file not found: $LOG_FILE"
        return 1
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the SpamShield Platform"
        echo "  stop    - Stop the SpamShield Platform"  
        echo "  restart - Restart the SpamShield Platform"
        echo "  status  - Check platform status and health"
        echo "  logs    - Follow platform logs"
        exit 1
        ;;
esac

exit $?
