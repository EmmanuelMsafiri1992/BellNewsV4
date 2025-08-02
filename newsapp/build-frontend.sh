#!/bin/bash
# build-frontend.sh - Dynamic frontend build script

set -e

# Function to get the current IP address
get_host_ip() {
    # Try multiple methods to get the host IP
    local ip=""

    # Method 1: Check default route (most reliable in containers)
    ip=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' | head -1)

    # Method 2: Check network interfaces if first method fails
    if [ -z "$ip" ]; then
        ip=$(hostname -I | awk '{print $1}')
    fi

    # Method 3: Fallback to environment variable if available
    if [ -z "$ip" ] && [ -n "$HOST_IP" ]; then
        ip="$HOST_IP"
    fi

    # Method 4: Final fallback
    if [ -z "$ip" ]; then
        ip="localhost"
    fi

    echo "$ip"
}

# Function to update environment files with current IP
update_env_files() {
    local current_ip="$1"
    local env_file=".env"
    local backup_file=".env.backup"

    echo "Updating environment configuration with IP: $current_ip"

    # Create backup
    if [ -f "$env_file" ]; then
        cp "$env_file" "$backup_file"
    fi

    # Update .env file
    if [ -f "$env_file" ]; then
        # Update APP_URL
        sed -i "s|^APP_URL=.*|APP_URL=http://$current_ip:8000|g" "$env_file"
        # Update VITE_API_BASE_URL
        sed -i "s|^VITE_API_BASE_URL=.*|VITE_API_BASE_URL=http://$current_ip:8000|g" "$env_file"
    else
        echo "Warning: .env file not found, creating minimal configuration"
        cat > "$env_file" << EOF
APP_URL=http://$current_ip:8000
VITE_API_BASE_URL=http://$current_ip:8000
EOF
    fi

    echo "Environment updated successfully"
}

# Function to build the frontend
build_frontend() {
    echo "Building frontend assets..."

    # Clear cache and reinstall if needed
    if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
        echo "Installing npm dependencies..."
        npm ci --silent
    fi

    # Build the assets
    echo "Building Vite assets..."
    npm run build

    echo "Frontend build completed successfully"
}

# Function to start Vite dev server
start_vite_dev() {
    local current_ip="$1"
    echo "Starting Vite development server on $current_ip:5173"

    # Kill any existing Vite processes
    pkill -f "vite" || true

    # Start Vite dev server in background
    npm run dev -- --host 0.0.0.0 --port 5173 &

    echo "Vite dev server started"
}

# Main execution
main() {
    echo "=== Dynamic Frontend Build Script ==="

    # Get current IP
    current_ip=$(get_host_ip)
    echo "Detected IP address: $current_ip"

    # Update environment configuration
    update_env_files "$current_ip"

    # Check if we're in development or production mode
    if [ "$APP_ENV" = "local" ] || [ "$NODE_ENV" = "development" ]; then
        echo "Running in development mode"
        build_frontend
        start_vite_dev "$current_ip"
    else
        echo "Running in production mode"
        build_frontend
    fi

    echo "=== Frontend setup completed ==="
}

# Run main function
main "$@"
