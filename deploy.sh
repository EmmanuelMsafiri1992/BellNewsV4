#!/bin/bash
# deploy.sh - One command to do everything
# This combines the setup from start.sh with your preferred docker-compose command

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect host IP (copied from start.sh)
detect_host_ip() {
    local ip=""
    
    if command -v hostname >/dev/null 2>&1; then
        ip=$(hostname -I 2>/dev/null | awk '{print $1}')
        if [[ -n "$ip" && "$ip" != "127.0.0.1" ]]; then
            echo "$ip"
            return 0
        fi
    fi
    
    if command -v ip >/dev/null 2>&1; then
        ip=$(ip route get 8.8.8.8 2>/dev/null | grep -oP 'src \K\S+' | head -1)
        if [[ -n "$ip" && "$ip" != "127.0.0.1" ]]; then
            echo "$ip"
            return 0
        fi
    fi
    
    echo "127.0.0.1"
    return 1
}

# Prepare environment (copied from start.sh)
prepare_environment() {
    local host_ip
    host_ip=$(detect_host_ip)
    
    log_info "Detected host IP: $host_ip"
    
    export HOST_IP="$host_ip"
    export UBUNTU_CONFIG_SERVICE_URL="http://$host_ip:5002"
    
    cat > .env <<EOF
# Auto-generated environment file
HOST_IP=$host_ip
UBUNTU_CONFIG_SERVICE_URL=http://$host_ip:5002
CONFIG_SERVICE_PORT=5002
AUTO_DETECT_CONFIG_SERVICE=true
COMPOSE_PROJECT_NAME=fbellnews
EOF
    
    log_info "Environment prepared (.env file created)"
}

# Create directories (copied from start.sh)
create_directories() {
    log_info "Creating required directories..."
    
    directories=(
        "./bellapp/logs"
        "./config_service_logs"
        "./newsapp/storage/logs"
    )
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_info "Created directory: $dir"
        fi
    done
}

# Stop existing services
stop_services() {
    log_info "Stopping existing services..."
    docker-compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true
    docker container prune -f >/dev/null 2>&1 || true
}

# Main deployment function
main() {
    local mode="${1:-prod}"
    
    log_info "Starting deployment in $mode mode..."
    
    # Check if Docker is available
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    # Run setup tasks
    prepare_environment
    create_directories
    stop_services
    
    # Run your preferred docker-compose command
    log_info "Running: docker-compose -f docker-compose.prod.yml up --build -d"
    docker-compose -f docker-compose.prod.yml up --build -d
    
    if [[ $? -eq 0 ]]; then
        log_info "Services started successfully!"
        
        # Show service status
        echo ""
        log_info "Service Status:"
        docker-compose -f docker-compose.prod.yml ps
        
        # Show access URLs
        local host_ip
        host_ip=$(detect_host_ip)
        echo ""
        log_info "Access URLs:"
        echo "  bellapp:        http://$host_ip:5000"
        echo "  newsapp:        http://$host_ip:8000"
        echo "  config_service: http://$host_ip:5002"
        
    else
        log_error "Failed to start services"
        exit 1
    fi
}

# Handle different commands
case "${1:-deploy}" in
    "deploy"|"start"|"")
        main prod
        ;;
    "stop")
        log_info "Stopping services..."
        docker-compose -f docker-compose.prod.yml down
        ;;
    "status")
        docker-compose -f docker-compose.prod.yml ps
        ;;
    "logs")
        docker-compose -f docker-compose.prod.yml logs -f "${2:-}"
        ;;
    *)
        echo "Usage: $0 [deploy|stop|status|logs] [service_name]"
        echo ""
        echo "Examples:"
        echo "  $0                    # Deploy everything"
        echo "  $0 deploy             # Deploy everything"
        echo "  $0 stop               # Stop all services"
        echo "  $0 status             # Show service status"
        echo "  $0 logs               # Show all logs"
        echo "  $0 logs bellapp       # Show bellapp logs"
        exit 1
        ;;
esac