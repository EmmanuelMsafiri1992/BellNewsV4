#!/bin/bash

# docker-entrypoint.sh for Laravel NewsApp
# This script dynamically updates environment variables and builds
# the frontend assets before the application starts.

# --------------------------------------------------------
# Step 1: Check for Host IP Address
# --------------------------------------------------------
if [ -z "${HOST_IP}" ]; then
  echo "HOST_IP environment variable is not set. Please provide it in the docker-compose file."
  echo "Example for Linux: HOST_IP=\$(ip route get 1 | awk '{print \$7; exit}')"
  echo "Example for Docker Desktop (macOS/Windows): HOST_IP=host.docker.internal"
  exit 1
fi

echo "--------------------------------------------------------"
echo "DEBUGGING: Starting docker-entrypoint.sh"
echo "Detected HOST_IP: ${HOST_IP}"
echo "--------------------------------------------------------"

# --------------------------------------------------------
# Step 2: Update Laravel's .env file
# --------------------------------------------------------
echo "Updating APP_URL in .env to http://${HOST_IP}:8000"
sed -i'' "s|^APP_URL=.*|APP_URL=http://${HOST_IP}:8000|" .env

# --------------------------------------------------------
# Step 3: Install npm dependencies and build frontend assets
# --------------------------------------------------------
echo "Running npm install..."
npm install

# Run the frontend build command using Vite.
# We pass the VITE_API_BASE_URL directly to the command to ensure
# it overrides any cached or hardcoded values.
echo "Running npm run build with VITE_API_BASE_URL=http://${HOST_IP}:8000..."
VITE_API_BASE_URL=http://${HOST_IP}:8000 npm run build

echo "Frontend assets built successfully."

# --------------------------------------------------------
# Step 4: Verify the build output for hardcoded IPs
# --------------------------------------------------------
echo "Verifying build output for hardcoded IP addresses..."
if grep -r "192.168.33.3" ./public/build; then
  echo "------------------------------------------------------------------------"
  echo "WARNING: The hardcoded IP '192.168.33.3' was found in the built assets."
  echo "This means the Vite build did not correctly override the value."
  echo "Please check your Vue.js source files (e.g., resources/js/) for any"
  echo "direct references to this IP address and use 'import.meta.env.VITE_API_BASE_URL' instead."
  echo "------------------------------------------------------------------------"
fi

# --------------------------------------------------------
# Step 5: Start the Laravel server
# --------------------------------------------------------
# The 'exec "$@"' command replaces the current process with the CMD instruction
# from the Dockerfile, which in this case is "php artisan serve...".
exec "$@"
