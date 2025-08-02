#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VCNS Timer Launcher Script
Launches vcns_timer_service.py and vcns_timer_web.py concurrently on Ubuntu-based systems,
WSL, or Docker.
Ensures system stability, proper permissions, and log directory creation.
This version removes the direct launch of ubuntu_config_service.py, as it's now managed by Docker Compose.
It also explicitly redirects subprocess output to log files within the container when running in Docker/WSL.
"""

import os
import sys
import time
import subprocess
import logging.handlers
from pathlib import Path
import shutil
import stat
import psutil
import platform

# Detect Docker environment
IN_DOCKER = os.getenv("IN_DOCKER", "0") == "1"

# Configure base directory
IS_WSL = "microsoft-standard" in platform.uname().release.lower()
BASE_DIR = Path("/bellapp") if IN_DOCKER else Path("/opt/vcns_timer") if not IS_WSL else Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "vcns_timer_launcher.log"

# Ensure log directory exists
try:
    os.makedirs(LOG_DIR, exist_ok=True)
    os.chmod(LOG_DIR, 0o775)
    # Only try to chown if not in Docker, as Docker handles user/group internally
    if not IN_DOCKER:
        shutil.chown(LOG_DIR, user=os.getuid(), group=os.getgid())
except Exception as e:
    print(f"Error creating log directory {LOG_DIR}: {e}", file=sys.stderr)
    sys.exit(1)

# Configure logging for the launcher itself
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=5*1024*1024, backupCount=5
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('VCNS-Timer-Launcher')

# Define paths to the service scripts
SERVICE_SCRIPT = BASE_DIR / "vcns_timer_service.py"
WEB_SCRIPT = BASE_DIR / "vcns_timer_web.py"

# Define service names for systemd (if not in Docker)
SERVICE_NAME = "vcns_timer_service"
WEB_NAME = "vcns_timer_web"

# Store PIDs of launched processes
service_pid = None
web_pid = None

def create_service_content(script_path, service_name):
    """Generates systemd service file content for a Python script."""
    return f"""[Unit]
Description={service_name}
After=network.target

[Service]
User={os.getlogin() if not IN_DOCKER else 'root'}
Group={os.getlogin() if not IN_DOCKER else 'root'}
WorkingDirectory={BASE_DIR}
ExecStart=/usr/bin/python3 {script_path}
Restart=always
StandardOutput=file:{LOG_DIR}/{service_name}.log
StandardError=file:{LOG_DIR}/{service_name}.err
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""

def create_web_content():
    """Generates systemd service file content for the Flask web application."""
    return f"""[Unit]
Description=VCNS Timer Web App
After=network.target {SERVICE_NAME}.service

[Service]
User={os.getlogin() if not IN_DOCKER else 'root'}
Group={os.getlogin() if not IN_DOCKER else 'root'}
WorkingDirectory={BASE_DIR}
ExecStart=/usr/bin/python3 {WEB_SCRIPT}
Restart=always
StandardOutput=file:{LOG_DIR}/{WEB_NAME}.log
StandardError=file:{LOG_DIR}/{WEB_NAME}.err
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""

def install_systemd_service(service_name, service_content):
    """Installs and enables a systemd service."""
    if platform.system() != "Linux" or IN_DOCKER or IS_WSL:
        logger.info(f"Skipping systemd installation for {service_name}: Not a native Linux system or running in Docker/WSL.")
        return True

    service_file = f"/etc/systemd/system/{service_name}.service"
    try:
        with open(service_file, "w") as f:
            f.write(service_content)
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
        subprocess.run(["sudo", "systemctl", "enable", service_name], check=True)
        logger.info(f"Systemd service {service_name} installed and enabled.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install systemd service {service_name}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error writing service file {service_file}: {e}")
        return False

def start_service(script_path, service_name, service_content=None):
    """
    Starts a Python script as a subprocess or systemd service.
    Returns the PID if started as subprocess, otherwise None.
    """
    global service_pid, web_pid

    if IN_DOCKER or IS_WSL:
        logger.info(f"Starting {service_name} as subprocess in Docker/WSL with log redirection...")
        log_file_path = LOG_DIR / f"{service_name}.log"
        err_file_path = LOG_DIR / f"{service_name}.err" # For standard error

        try:
            # Open log files for writing (append mode)
            # Using 'w' mode to overwrite for fresh logs on each start
            # For persistent logs across restarts, 'a' (append) might be desired,
            # but 'w' is better for debugging fresh starts.
            stdout_file = open(log_file_path, 'w')
            stderr_file = open(err_file_path, 'w')

            # Use sys.executable to ensure the correct Python interpreter is used
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=BASE_DIR,
                stdout=stdout_file, # Redirect stdout to the log file
                stderr=stderr_file, # Redirect stderr to the error file
                text=True, # Handle stdout/stderr as text
                bufsize=1 # Line-buffered output
            )

            # Store file handles to keep them open as long as process runs
            if service_name == SERVICE_NAME:
                service_pid = process.pid
                process.stdout_file = stdout_file
                process.stderr_file = stderr_file
            elif service_name == WEB_NAME:
                web_pid = process.pid
                process.stdout_file = stdout_file
                process.stderr_file = stderr_file

            logger.info(f"{service_name} started with PID: {process.pid}. Logs redirected to {log_file_path}")
            return process.pid
        except Exception as e:
            logger.critical(f"Failed to start {service_name} as subprocess: {e}")
            sys.exit(1)
    else:
        logger.info(f"Attempting to start {service_name} using systemd...")
        if install_systemd_service(service_name, service_content):
            try:
                subprocess.run(["sudo", "systemctl", "start", service_name], check=True)
                logger.info(f"Systemd service {service_name} started.")
                return None # Systemd manages PID
            except subprocess.CalledProcessError as e:
                logger.critical(f"Failed to start systemd service {service_name}: {e}")
                sys.exit(1)
        else:
            logger.critical(f"Systemd service {service_name} could not be installed/started.")
            sys.exit(1)

def monitor_services():
    """Monitors the launched services and exits if any critical service stops."""
    global service_pid, web_pid

    if IN_DOCKER or IS_WSL:
        logger.info("Monitoring subprocesses...")
        try:
            while True:
                time.sleep(5) # Check every 5 seconds
                # Check if critical processes are still running
                critical_pids = []
                if service_pid is not None:
                    critical_pids.append(service_pid)
                if web_pid is not None:
                    critical_pids.append(web_pid)

                for pid in critical_pids:
                    if not psutil.pid_exists(pid):
                        logger.critical(f"Process with PID {pid} stopped, exiting launcher.")
                        sys.exit(1)
        except KeyboardInterrupt:
            logger.info("Shutting down launcher")
            # Terminate all launched processes and close file handles
            for pid in [service_pid, web_pid]:
                if pid and psutil.pid_exists(pid):
                    try:
                        process = psutil.Process(pid)
                        # Attempt to close stdout/stderr file handles if they were stored
                        if hasattr(process, 'stdout_file') and process.stdout_file:
                            process.stdout_file.close()
                        if hasattr(process, 'stderr_file') and process.stderr_file:
                            process.stderr_file.close()
                        process.terminate()
                        logger.info(f"Terminated PID {pid} and closed log files.")
                    except psutil.NoSuchProcess:
                        logger.warning(f"Process PID {pid} already gone.")
                    except Exception as e:
                        logger.error(f"Error terminating process {pid} or closing files: {e}")
            sys.exit(0)
    else:
        logger.info("Monitoring systemd services (via systemctl status)...")
        # For systemd, we rely on systemd's own monitoring and restart capabilities
        # This launcher will simply stay alive. If systemd services fail,
        # systemd will handle restarts or notifications.
        try:
            while True:
                time.sleep(60) # Sleep for a minute, systemd is doing the heavy lifting
                # Optional: Add checks for systemd service status if more active monitoring is needed
                # For example: subprocess.run(["systemctl", "is-active", SERVICE_NAME], check=True)
        except KeyboardInterrupt:
            logger.info("Launcher received KeyboardInterrupt. Exiting.")
            sys.exit(0)


def main():
    logger.info("Starting VCNS Timer Launcher")

    if IN_DOCKER:
        logger.info("Running inside Docker container.")
        # When in Docker, Docker Compose manages the config_service.
        # This launcher only needs to start the bellapp services.
        start_service(SERVICE_SCRIPT, SERVICE_NAME)
        time.sleep(5)  # Give service a moment to initialize
        start_service(WEB_SCRIPT, WEB_NAME)
    else:
        logger.info("Running outside Docker container (native/WSL).")
        # On native/WSL, we still manage all services via this launcher
        # or systemd.
        # Removed: start_service(UBUNTU_CONFIG_SCRIPT, UBUNTU_CONFIG_SERVICE_NAME, create_service_content(UBUNTU_CONFIG_SCRIPT, UBUNTU_CONFIG_SERVICE_NAME))
        # time.sleep(3) # Give it a moment to initialize
        start_service(SERVICE_SCRIPT, SERVICE_NAME, create_service_content(SERVICE_SCRIPT, SERVICE_NAME))
        time.sleep(5)  # Ensure backend is up before starting web
        start_service(WEB_SCRIPT, WEB_NAME, create_web_content())

    # Monitor services
    logger.info("Monitoring services")
    monitor_services()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Unhandled exception in launcher: {e}", exc_info=True)
        sys.exit(1)

