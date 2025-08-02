#!/bin/bash
# host-ip-detector.sh - Reliable host IP detection for Docker containers

# Function to detect the actual HOST machine IP (Windows/Linux/NanoPi)
get_real_host_ip() {
    local ip=""
    local debug="${DEBUG_IP_DETECTION:-false}"

    [ "$debug" = "true" ] && echo "DEBUG: Starting host IP detection..." >&2

    # Method 1: host.docker.internal (Docker Desktop - Windows/Mac)
    if command -v getent >/dev/null 2>&1; then
        ip=$(getent hosts host.docker.internal 2>/dev/null | awk '{print $1}')
        [ "$debug" = "true" ] && echo "DEBUG: host.docker.internal -> $ip" >&2
        if [ -n "$ip" ] && [[ "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "$ip"
            return 0
        fi
    fi

    # Method 2: Check Docker gateway and find host in same network
    local gateway=$(ip route | grep default | awk '{print $3}' | head -1)
    [ "$debug" = "true" ] && echo "DEBUG: Docker gateway -> $gateway" >&2

    if [ -n "$gateway" ]; then
        local network=$(echo "$gateway" | cut -d'.' -f1-3)
        [ "$debug" = "true" ] && echo "DEBUG: Network -> $network" >&2

        # Try to ping common host IPs in the network
        for suffix in 1 2 10 74 100 254; do
            local test_ip="${network}.${suffix}"
            [ "$debug" = "true" ] && echo "DEBUG: Testing $test_ip..." >&2

            # Skip if it's the gateway itself
            [ "$test_ip" = "$gateway" ] && continue

            # Quick ping test (1 second timeout)
            if timeout 1 ping -c 1 -W 1 "$test_ip" >/dev/null 2>&1; then
                [ "$debug" = "true" ] && echo "DEBUG: Found responsive host -> $test_ip" >&2
                ip="$test_ip"
                break
            fi
        done
    fi

    # Method 3: Try to read from Docker's /proc/net/route
    if [ -z "$ip" ] && [ -f "/proc/net/route" ]; then
        # Find non-Docker routes
        while read -r line; do
            local iface=$(echo "$line" | awk '{print $1}')
            local dest=$(echo "$line" | awk '{print $2}')
            local gateway_hex=$(echo "$line" | awk '{print $3}')

            # Skip Docker interfaces
            [[ "$iface" == docker* ]] && continue
            [[ "$iface" == br-* ]] && continue

            # Convert hex gateway to IP
            if [ "$dest" = "00000000" ] && [ -n "$gateway_hex" ] && [ "$gateway_hex" != "00000000" ]; then
                ip=$(printf "%d.%d.%d.%d" $((0x${gateway_hex:6:2})) $((0x${gateway_hex:4:2})) $((0x${gateway_hex:2:2})) $((0x${gateway_hex:0:2})))
                [ "$debug" = "true" ] && echo "DEBUG: Route table gateway -> $ip" >&2
                break
            fi
        done < /proc/net/route
    fi

    # Method 4: Try to connect to a known external service and see our source IP
    if [ -z "$ip" ]; then
        # This shows what IP we use to reach the internet
        local external_ip=$(ip route get 8.8.8.8 2>/dev/null | grep -oP 'src \K\S+' | head -1)
        [ "$debug" = "true" ] && echo "DEBUG: External route IP -> $external_ip" >&2

        # Only use if it's not a Docker internal IP
        if [ -n "$external_ip" ] && [[ "$external_ip" != 172.1[7-9].* ]] && [[ "$external_ip" != 172.2[0-9].* ]]; then
            ip="$external_ip"
        fi
    fi

    # Method 5: Check for mounted host info (if available)
    if [ -z "$ip" ] && [ -f "/host/proc/net/route" ]; then
        # If host's /proc is mounted, read the real host routing table
        while read -r line; do
            local dest=$(echo "$line" | awk '{print $2}')
            local gateway_hex=$(echo "$line" | awk '{print $3}')
            local iface=$(echo "$line" | awk '{print $1}')

            if [ "$dest" = "00000000" ] && [ -n "$gateway_hex" ] && [ "$gateway_hex" != "00000000" ]; then
                local gw_ip=$(printf "%d.%d.%d.%d" $((0x${gateway_hex:6:2})) $((0x${gateway_hex:4:2})) $((0x${gateway_hex:2:2})) $((0x${gateway_hex:0:2})))

                # Find host IP in same network as gateway
                local host_network=$(echo "$gw_ip" | cut -d'.' -f1-3)
                for host_suffix in 2 10 74 100; do
                    local potential_host="${host_network}.${host_suffix}"
                    if [ "$potential_host" != "$gw_ip" ]; then
                        ip="$potential_host"
                        break
                    fi
                done
                break
            fi
        done < /host/proc/net/route
        [ "$debug" = "true" ] && echo "DEBUG: Host route table -> $ip" >&2
    fi

    # Method 6: Environment variable override
    if [ -z "$ip" ] && [ -n "$HOST_IP_OVERRIDE" ]; then
        ip="$HOST_IP_OVERRIDE"
        [ "$debug" = "true" ] && echo "DEBUG: Environment override -> $ip" >&2
    fi

    # Validation: Make sure we have a valid IP
    if [ -n "$ip" ] && [[ "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        [ "$debug" = "true" ] && echo "DEBUG: Final IP -> $ip" >&2
        echo "$ip"
        return 0
    fi

    # Ultimate fallback
    [ "$debug" = "true" ] && echo "DEBUG: Using localhost fallback" >&2
    echo "localhost"
    return 1
}

# Test function to validate the detected IP
test_detected_ip() {
    local ip="$1"
    local port="${2:-8000}"

    # Skip test for localhost
    [ "$ip" = "localhost" ] && return 0

    # Try to connect to the IP (with timeout)
    if timeout 3 bash -c "</dev/tcp/$ip/$port" 2>/dev/null; then
        return 0
    fi

    return 1
}

# Main function
main() {
    local debug_mode="${1:-false}"

    if [ "$debug_mode" = "debug" ] || [ "$debug_mode" = "-d" ]; then
        export DEBUG_IP_DETECTION=true
    fi

    local detected_ip=$(get_real_host_ip)

    echo "$detected_ip"

    # If debug mode, show additional info
    if [ "$DEBUG_IP_DETECTION" = "true" ]; then
        echo "=== IP Detection Debug Info ===" >&2
        echo "Container IP: $(hostname -I | awk '{print $1}')" >&2
        echo "Default Gateway: $(ip route | grep default | awk '{print $3}')" >&2
        echo "Docker Gateway: $(ip route | grep docker0 2>/dev/null | awk '{print $9}')" >&2
        echo "host.docker.internal: $(getent hosts host.docker.internal 2>/dev/null | awk '{print $1}')" >&2
        echo "Detected Host IP: $detected_ip" >&2
        echo "=================================" >&2
    fi
}

# Allow script to be sourced or executed
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
