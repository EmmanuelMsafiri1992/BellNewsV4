#!/bin/bash
# ip-monitor.sh - Continuous IP monitoring and auto-rebuild service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/ip-monitor.log"
PID_FILE="/var/run/ip-monitor.pid"
CHECK_INTERVAL="${IP_CHECK_INTERVAL:-30}"  # Check every 30 seconds by default

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to get current IP
get_current_ip() {
    local ip=""

    # Try multiple methods
    ip=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' | head -1)

    if [ -z "$ip" ]; then
        ip=$(hostname -I | awk '{print $1}')
    fi

    if [ -z "$ip" ]; then
        ip="localhost"
    fi

    echo "$ip"
}

# Function to rebuild frontend
rebuild_frontend() {
    local new_ip="$1"

    log "Rebuilding frontend for IP: $new_ip"

    # Export IP for build scripts
    export HOST_IP="$new_ip"

    # Update environment
    if [ -f "/usr/local/bin/build-frontend.sh" ]; then
        /usr/local/bin/build-frontend.sh
    elif [ -f "$SCRIPT_DIR/build-frontend.sh" ]; then
        "$SCRIPT_DIR/build-frontend.sh"
    else
        log "ERROR: Frontend build script not found"
        return 1
    fi

    log "Frontend rebuild completed for IP: $new_ip"
}

# Function to check if frontend needs rebuilding
needs_rebuild() {
    local current_ip="$1"
    local last_ip_file="/tmp/last_known_ip"

    if [ ! -f "$last_ip_file" ]; then
        echo "$current_ip" > "$last_ip_file"
        return 0  # First run, build needed
    fi

    local last_ip=$(cat "$last_ip_file")

    if [ "$current_ip" != "$last_ip" ]; then
        echo "$current_ip" > "$last_ip_file"
        return 0  # IP changed, build needed
    fi

    return 1  # No change, no build needed
}

# Main monitoring loop
monitor_ip() {
    log "Starting IP monitoring service (checking every ${CHECK_INTERVAL}s)"

    # Store PID
    echo $$ > "$PID_FILE"

    while true; do
        current_ip=$(get_current_ip)

        if needs_rebuild "$current_ip"; then
            log "IP change detected or initial setup needed: $current_ip"

            if rebuild_frontend "$current_ip"; then
                log "Successfully rebuilt frontend for IP: $current_ip"

                # Restart Vite dev server if in development mode
                if [ "$NODE_ENV" = "development" ] || [ "$APP_ENV" = "local" ]; then
                    log "Restarting Vite dev server..."
                    pkill -f "vite.*dev" || true
                    sleep 2
                    (cd /var/www/html && npm run dev-auto) &
                fi
            else
                log "ERROR: Failed to rebuild frontend"
            fi
        fi

        sleep "$CHECK_INTERVAL"
    done
}

# Signal handlers
cleanup() {
    log "IP monitoring service stopping..."
    rm -f "$PID_FILE"
    exit 0
}

# Handle termination signals
trap cleanup SIGTERM SIGINT SIGQUIT

# Check if already running
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    log "IP monitor is already running with PID: $(cat "$PID_FILE")"
    exit 1
fi

# Start monitoring
case "${1:-start}" in
    start)
        monitor_ip
        ;;
    stop)
        if [ -f "$PID_FILE" ]; then
            kill "$(cat "$PID_FILE")" && log "IP monitor stopped"
            rm -f "$PID_FILE"
        else
            log "IP monitor is not running"
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            log "IP monitor is running with PID: $(cat "$PID_FILE")"
        else
            log "IP monitor is not running"
        fi
        ;;
    *)
        echo "Usage
