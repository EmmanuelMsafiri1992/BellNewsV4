#!/bin/bash
# start-services.sh - Complete startup script for Laravel app with dynamic IP

set -e

APP_DIR="/var/www/html"
LOG_DIR="/var/log/laravel"
SCRIPTS_DIR="$APP_DIR/scripts"

# Create necessary directories
mkdir -p "$LOG_DIR"
mkdir -p "$SCRIPTS_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_DIR/startup.log"
}

# Function to detect HOST machine IP (not container IP)
detect_ip() {
    local ip=""

    # Method 1: Try host.docker.internal (Docker Desktop on Windows/Mac)
    ip=$(getent hosts host.docker.internal 2>/dev/null | awk '{print $1}')

    # Method 2: Check if DOCKER_HOST_IP environment variable is set
    if [ -z "$ip" ] && [ -n "$DOCKER_HOST_IP" ]; then
        ip="$DOCKER_HOST_IP"
    fi

    # Method 3: Try to find host IP through gateway
    if [ -z "$ip" ]; then
        local gateway=$(ip route | grep default | awk '{print $3}' | head -1)
        if [ -n "$gateway" ]; then
            # Use gateway IP as host IP (common in Docker bridge networks)
            local network=$(echo "$gateway" | cut -d'.' -f1-3)

            # Try to find a host in the same network
            ip=$(ip neigh | grep "$network" | grep -v "$gateway" | head -1 | awk '{print $1}')

            # If that fails, construct likely host IP
            if [ -z "$ip" ]; then
                # Common pattern: if gateway is x.x.x.1, host might be x.x.x.2 or check ARP
                local last_octet=$(echo "$gateway" | cut -d'.' -f4)
                if [ "$last_octet" = "1" ]; then
                    # Try common host IPs in the network
                    for i in 2 10 100 74; do
                        local test_ip="${network}.${i}"
                        if ping -c 1 -W 1 "$test_ip" >/dev/null 2>&1; then
                            ip="$test_ip"
                            break
                        fi
                    done
                fi
            fi
        fi
    fi

    # Method 4: Check Docker bridge gateway (usually host IP)
    if [ -z "$ip" ]; then
        local docker_gw=$(ip route | grep docker0 | awk '{print $9}' | head -1)
        if [ -n "$docker_gw" ]; then
            ip="$docker_gw"
        fi
    fi

    # Method 5: Use environment variable from docker-compose
    if [ -z "$ip" ] && [ -n "$HOST_MACHINE_IP" ]; then
        ip="$HOST_MACHINE_IP"
    fi

    # Method 6: Parse routing table for host routes
    if [ -z "$ip" ]; then
        # Look for routes that point to non-Docker networks
        ip=$(ip route | grep -E "192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\." | grep -v docker | awk '{print $9}' | head -1)
    fi

    # Fallback: Use the default gateway as the host IP
    if [ -z "$ip" ]; then
        ip=$(ip route | grep default | awk '{print $3}' | head -1)
    fi

    # Final fallback
    if [ -z "$ip" ]; then
        ip="localhost"
    fi

    echo "$ip"
}

# Function to update all configuration files
update_configurations() {
    local current_ip="$1"

    log "Updating configurations for IP: $current_ip"

    # Update .env file
    if [ -f "$APP_DIR/.env" ]; then
        # Create backup
        cp "$APP_DIR/.env" "$APP_DIR/.env.backup.$(date +%s)"

        # Update URLs
        sed -i "s|^APP_URL=.*|APP_URL=http://$current_ip:8000|g" "$APP_DIR/.env"
        sed -i "s|^VITE_API_BASE_URL=.*|VITE_API_BASE_URL=http://$current_ip:8000|g" "$APP_DIR/.env"

        # Add if missing
        if ! grep -q "^APP_URL=" "$APP_DIR/.env"; then
            echo "APP_URL=http://$current_ip:8000" >> "$APP_DIR/.env"
        fi
        if ! grep -q "^VITE_API_BASE_URL=" "$APP_DIR/.env"; then
            echo "VITE_API_BASE_URL=http://$current_ip:8000" >> "$APP_DIR/.env"
        fi
    fi

    # Update CORS configuration if it exists
    local cors_file="$APP_DIR/config/cors.php"
    if [ -f "$cors_file" ]; then
        # Add current IP to allowed origins
        if ! grep -q "$current_ip" "$cors_file"; then
            sed -i "/allowed_origins.*\[/a\\        'http://$current_ip:8000'," "$cors_file"
        fi
    fi
}

# Function to build frontend assets
build_frontend() {
    local current_ip="$1"

    log "Building frontend assets for IP: $current_ip"

    cd "$APP_DIR"

    # Set environment variables
    export HOST_IP="$current_ip"
    export NODE_ENV="${NODE_ENV:-development}"

    # Install dependencies if needed
    if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
        log "Installing npm dependencies..."
        npm ci --silent --prefer-offline
    fi

    # Build assets
    log "Building Vite assets..."
    if [ "$NODE_ENV" = "production" ]; then
        npm run build
    else
        # For development, build and start dev server
        npm run build

        # Start Vite dev server in background
        log "Starting Vite development server..."
        pkill -f "vite.*dev" || true
        sleep 2
        npm run dev -- --host 0.0.0.0 --port 5173 &
    fi

    log "Frontend build completed"
}

# Function to setup Laravel
setup_laravel() {
    log "Setting up Laravel application..."

    cd "$APP_DIR"

    # Generate app key if needed
    if ! grep -q "APP_KEY=base64:" .env 2>/dev/null; then
        php artisan key:generate --no-interaction
    fi

    # Database operations
    if [ "$DB_CONNECTION" = "sqlite" ]; then
        # Ensure SQLite database exists
        touch database/database.sqlite
        chmod 664 database/database.sqlite
    fi

    # Run migrations
    php artisan migrate --force --no-interaction || log "Migration failed, continuing..."

    # Storage link
    php artisan storage:link --no-interaction || log "Storage link already exists"

    # Clear and cache
    php artisan config:clear
    php artisan config:cache
    php artisan route:clear
    php artisan route:cache
    php artisan view:clear
    php artisan view:cache

    log "Laravel setup completed"
}

# Function to start background IP monitoring
start_ip_monitoring() {
    local current_ip="$1"

    if [ "$ENABLE_IP_MONITORING" = "true" ]; then
        log "Starting IP monitoring service..."

        # Create monitoring script
        cat > "$SCRIPTS_DIR/monitor-ip.sh" << 'EOF'
#!/bin/bash
last_ip=""
while true; do
    current_ip=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' | head -1)
    if [ -z "$current_ip" ]; then
        current_ip=$(hostname -I | awk '{print $1}')
    fi

    if [ "$current_ip" != "$last_ip" ] && [ -n "$last_ip" ]; then
        echo "[$(date)] IP changed from $last_ip to $current_ip" >> /var/log/laravel/ip-changes.log

        # Trigger rebuild
        export HOST_IP="$current_ip"
        cd /var/www/html
        /usr/local/bin/start-services.sh rebuild-only "$current_ip"
    fi

    last_ip="$current_ip"
    sleep 30
done
EOF
        chmod +x "$SCRIPTS_DIR/monitor-ip.sh"

        # Start monitoring in background
        nohup "$SCRIPTS_DIR/monitor-ip.sh" > "$LOG_DIR/ip-monitor.log" 2>&1 &
        echo $! > "/var/run/ip-monitor.pid"

        log "IP monitoring started with PID: $(cat /var/run/ip-monitor.pid)"
    fi
}

# Function to start main services
start_services() {
    log "Starting main services..."

    cd "$APP_DIR"

    if [ "$APP_ENV" = "local" ] || [ "$NODE_ENV" = "development" ]; then
        log "Starting Laravel development server..."
        php artisan serve --host=0.0.0.0 --port=8000 &
        echo $! > "/var/run/laravel.pid"
    else
        log "Starting Apache server..."
        apache2-foreground &
        echo $! > "/var/run/apache.pid"
    fi

    log "Services started successfully"
}

# Function for rebuild-only mode
rebuild_only() {
    local new_ip="$1"
    log "Rebuild-only mode: updating for IP $new_ip"

    update_configurations "$new_ip"
    build_frontend "$new_ip"

    # Restart services if needed
    if [ -f "/var/run/laravel.pid" ]; then
        local pid=$(cat "/var/run/laravel.pid")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            sleep 2
            cd "$APP_DIR"
            php artisan serve --host=0.0.0.0 --port=8000 &
            echo $! > "/var/run/laravel.pid"
        fi
    fi

    log "Rebuild completed"
}

# Main function
main() {
    local mode="${1:-start}"
    local ip_override="$2"

    log "=== Laravel Dynamic Startup Script ==="
    log "Mode: $mode"

    # Detect current IP
    local current_ip="${ip_override:-$(detect_ip)}"
    log "Current IP address: $current_ip"

    case "$mode" in
        "start")
            # Full startup sequence
            update_configurations "$current_ip"
            setup_laravel
            build_frontend "$current_ip"
            start_ip_monitoring "$current_ip"
            start_services

            # Keep script running
            log "Startup completed. Services are running."
            wait
            ;;
        "rebuild-only")
            rebuild_only "$current_ip"
            ;;
        "stop")
            log "Stopping services..."

            # Stop IP monitoring
            if [ -f "/var/run/ip-monitor.pid" ]; then
                kill "$(cat /var/run/ip-monitor.pid)" 2>/dev/null || true
                rm -f "/var/run/ip-monitor.pid"
            fi

            # Stop Laravel/Apache
            if [ -f "/var/run/laravel.pid" ]; then
                kill "$(cat /var/run/laravel.pid)" 2>/dev/null || true
                rm -f "/var/run/laravel.pid"
            fi
            if [ -f "/var/run/apache.pid" ]; then
                kill "$(cat /var/run/apache.pid)" 2>/dev/null || true
                rm -f "/var/run/apache.pid"
            fi

            # Stop Vite
            pkill -f "vite" || true

            log "Services stopped"
            ;;
        *)
            echo "Usage: $0 {start|rebuild-only|stop} [ip_address]"
            exit 1
            ;;
    esac
}

# Handle signals
trap 'log "Received termination signal"; main stop; exit 0' SIGTERM SIGINT

# Run main function
main "$@"
