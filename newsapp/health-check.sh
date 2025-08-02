#!/bin/bash
# health-check.sh - Verify that all services are running correctly

LOG_FILE="/var/log/laravel/health-check.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_laravel() {
    local current_ip="$1"
    local url="http://$current_ip:8000"

    log "Checking Laravel at $url"

    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|302"; then
        log "✓ Laravel is responding"
        return 0
    else
        log "✗ Laravel is not responding"
        return 1
    fi
}

check_vite() {
    local current_ip="$1"
    local url="http://$current_ip:5173"

    log "Checking Vite at $url"

    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|404"; then
        log "✓ Vite dev server is responding"
        return 0
    else
        log "✗ Vite dev server is not responding"
        return 1
    fi
}

check_processes() {
    log "Checking running processes..."

    # Check Laravel/Apache
    if pgrep -f "artisan serve" > /dev/null || pgrep apache2 > /dev/null; then
        log "✓ Laravel/Apache process is running"
    else
        log "✗ Laravel/Apache process is not running"
        return 1
    fi

    # Check Vite (only in development)
    if [ "$NODE_ENV" = "development" ] || [ "$APP_ENV" = "local" ]; then
        if pgrep -f "vite" > /dev/null; then
            log "✓ Vite process is running"
        else
            log "✗ Vite process is not running"
            return 1
        fi
    fi

    # Check IP monitor
    if [ "$ENABLE_IP_MONITORING" = "true" ]; then
        if [ -f "/var/run/ip-monitor.pid" ] && kill -0 "$(cat /var/run/ip-monitor.pid)" 2>/dev/null; then
            log "✓ IP monitoring service is running"
        else
            log "✗ IP monitoring service is not running"
            return 1
        fi
    fi

    return 0
}

check_files() {
    log "Checking required files..."

    local required_files=(
        "/var/www/html/.env"
        "/var/www/html/public/index.php"
        "/var/www/html/artisan"
    )

    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            log "✓ Found: $file"
        else
            log "✗ Missing: $file"
            return 1
        fi
    done

    return 0
}

get_current_ip() {
    local ip=""
    ip=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' | head -1)
    if [ -z "$ip" ]; then
        ip=$(hostname -I | awk '{print $1}')
    fi
    if [ -z "$ip" ]; then
        ip="localhost"
    fi
    echo "$ip"
}

main() {
    local mode="${1:-full}"

    log "=== Health Check Started ==="

    local current_ip=$(get_current_ip)
    log "Current IP: $current_ip"

    local failed=0

    case "$mode" in
        "full")
            check_files || ((failed++))
            check_processes || ((failed++))
            check_laravel "$current_ip" || ((failed++))
            if [ "$NODE_ENV" = "development" ] || [ "$APP_ENV" = "local" ]; then
                check_vite "$current_ip" || ((failed++))
            fi
            ;;
        "quick")
            check_laravel "$current_ip" || ((failed++))
            ;;
        "processes")
            check_processes || ((failed++))
            ;;
        *)
            echo "Usage: $0 {full|quick|processes}"
            exit 1
            ;;
    esac

    if [ $failed -eq 0 ]; then
        log "=== All checks passed ✓ ==="
        exit 0
    else
        log "=== $failed check(s) failed ✗ ==="
        exit 1
    fi
}

main "$@"
