#!/bin/bash
# start.sh - Smart deployment script with auto IP detection

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
PROD_COMPOSE_FILE="docker-compose.prod.yml"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

detect_host_ip() {
    local ip=""
    
    # Method 1: hostname -I (most reliable on Ubuntu)
    if command -v hostname >/dev/null 2>&1; then
        ip=$(hostname -I 2>/dev/null | awk '{print $1}')
        if [[ -n "$ip" && "$ip" != "127.0.0.1" ]]; then
            echo "$ip"
            return 0
        fi
    fi
    
    # Method 2: ip route
    if command -v ip >/dev/null 2>&1; then
        ip=$(ip route get 8.8.8.8 2>/dev/null | grep -oP 'src \K\S+' | head -1)
        if [[ -n "$ip" && "$ip" != "127.0.0.1" ]]; then
            echo "$ip"
            return 0
        fi
    fi
    
    # Method 3: ifconfig (fallback)
    if command -v ifconfig >/dev/null 2>&1; then
        ip=$(ifconfig 2>/dev/null | grep -E 'inet.*broadcast' | grep -v '127.0.0.1' | awk '{print $2}' | head -1)
        if [[ -n "$ip" ]]; then
            echo "$ip"
            return 0
        fi
    fi
    
    # Fallback
    echo "127.0.0.1"
    return 1
}

check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose >/dev/null 2>&1; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running"
        exit 1
    fi
}

prepare_environment() {
    local host_ip
    host_ip=$(detect_host_ip)
    
    log_info "Detected host IP: $host_ip"
    
    # Export environment variables
    export HOST_IP="$host_ip"
    export UBUNTU_CONFIG_SERVICE_URL="http://$host_ip:5002"
    
    # Create .env file for docker-compose
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

stop_services() {
    log_info "Stopping existing services..."
    
    if [[ -f "$PROD_COMPOSE_FILE" ]]; then
        docker-compose -f "$PROD_COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
    fi
    
    if [[ -f "$COMPOSE_FILE" ]]; then
        docker-compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
    fi
    
    # Clean up any remaining containers
    docker container prune -f >/dev/null 2>&1 || true
}

build_services() {
    local compose_file="$1"
    
    log_info "Building services using $compose_file..."
    docker-compose -f "$compose_file" build --no-cache
    
    if [[ $? -eq 0 ]]; then
        log_info "Build completed successfully"
    else
        log_error "Build failed"
        exit 1
    fi
}

start_services() {
    local compose_file="$1"
    
    log_info "Starting services using $compose_file..."
    docker-compose -f "$compose_file" up -d
    
    if [[ $? -eq 0 ]]; then
        log_info "Services started successfully"
    else
        log_error "Failed to start services"
        exit 1
    fi
}

check_service_health() {
    log_info "Checking service health..."
    
    local host_ip
    host_ip=$(detect_host_ip)
    
    # Wait a bit for services to start
    sleep 5
    
    # Check bellapp
    log_info "Checking bellapp (port 5000)..."
    if curl -f -s "http://$host_ip:5000" >/dev/null; then
        log_info "✓ bellapp is responding"
    else
        log_warn "✗ bellapp is not responding"
    fi
    
    # Check config_service
    log_info "Checking config_service (port 5002)..."
    if curl -f -s "http://$host_ip:5002" >/dev/null; then
        log_info "✓ config_service is responding"
    else
        log_warn "✗ config_service is not responding"
    fi
    
    # Check newsapp
    log_info "Checking newsapp (port 8000)..."
    if curl -f -s "http://$host_ip:8000" >/dev/null; then
        log_info "✓ newsapp is responding"
    else
        log_warn "✗ newsapp is not responding"
    fi
}

show_status() {
    log_info "Service Status:"
    docker-compose ps
    
    local host_ip
    host_ip=$(detect_host_ip)
    
    echo ""
    log_info "Access URLs:"
    echo "  bellapp:        http://$host_ip:5000"
    echo "  newsapp:        http://$host_ip:8000"
    echo "  config_service: http://$host_ip:5002"
}

# Main execution
main() {
    local mode="${1:-dev}"
    local action="${2:-start}"
    
    log_info "Starting deployment in $mode mode with action: $action"
    
    # Select compose file
    if [[ "$mode" == "prod" || "$mode" == "production" ]]; then
        if [[ ! -f "$PROD_COMPOSE_FILE" ]]; then
            log_error "Production compose file not found: $PROD_COMPOSE_FILE"
            exit 1
        fi
        COMPOSE_FILE="$PROD_COMPOSE_FILE"
        log_info "Using production configuration"
    else
        if [[ ! -f "$COMPOSE_FILE" ]]; then
            log_error "Development compose file not found: $COMPOSE_FILE"
            exit 1
        fi
        log_info "Using development configuration"
    fi
    
    case "$action" in
        "start")
            check_docker
            prepare_environment
            create_directories
            stop_services
            build_services "$COMPOSE_FILE"
            start_services "$COMPOSE_FILE"
            check_service_health
            show_status
            ;;
        "stop")
            stop_services
            log_info "Services stopped"
            ;;
        "restart")
            check_docker
            prepare_environment
            stop_services
            start_services "$COMPOSE_FILE"
            check_service_health
            show_status
            ;;
        "rebuild")
            check_docker
            prepare_environment
            create_directories
            stop_services
            build_services "$COMPOSE_FILE"
            start_services "$COMPOSE_FILE"
            check_service_health
            show_status
            ;;
        "status")
            show_status
            ;;
        "logs")
            local service="${3:-}"
            if [[ -n "$service" ]]; then
                docker-compose -f "$COMPOSE_FILE" logs -f "$service"
            else
                docker-compose -f "$COMPOSE_FILE" logs -f
            fi
            ;;
        *)
            echo "Usage: $0 [dev|prod] [start|stop|restart|rebuild|status|logs] [service_name]"
            echo ""
            echo "Examples:"
            echo "  $0 dev start          # Start in development mode"
            echo "  $0 prod start         # Start in production mode"
            echo "  $0 dev stop           # Stop all services"
            echo "  $0 dev logs bellapp   # Show logs for bellapp service"
            echo "  $0 dev status         # Show service status"
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"