#!/usr/bin/env python3
"""
Generate a dynamic systemd service file for VCNS Timer
"""

import os
import getpass
import subprocess
import platform  # Added missing import
from pathlib import Path
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def create_service_file():
    if "microsoft-standard" in platform.uname().release.lower():
        logger.warning("Systemd setup skipped in WSL")
        return False
    # Get current user
    user = getpass.getuser()
    logger.info(f"Detected user: {user}")

    # Get script directory (parent of this script)
    script_dir = Path(__file__).resolve().parent
    logger.info(f"Detected script directory: {script_dir}")

    # Path to the main timer script
    timer_script = script_dir / "nano_web_timer.py"
    if not timer_script.exists():
        logger.error(f"Timer script not found at: {timer_script}")
        return False

    # Path to Python 3
    try:
        python_path = subprocess.check_output(["which", "python3"], text=True).strip()
    except subprocess.CalledProcessError:
        logger.error("Python 3 not found in PATH")
        return False
    logger.info(f"Detected Python 3 path: {python_path}")

    # Service file content
    service_content = f"""[Unit]
Description=VCNS Timer Service
After=network-online.target
Wants=network-online.target

[Service]
User={user}
WorkingDirectory={script_dir}
ExecStart={python_path} {timer_script}
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""

    # Write service file
    service_file = Path("/etc/systemd/system/vcns-timer.service")
    try:
        with service_file.open("w") as f:
            f.write(service_content)
        logger.info(f"Created service file at: {service_file}")

        # Set permissions
        service_file.chmod(0o644)
        logger.info(f"Set permissions for {service_file}")

        # Reload systemd daemon
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        logger.info("Reloaded systemd daemon")

        # Enable service
        subprocess.run(["systemctl", "enable", "vcns-timer.service"], check=True)
        logger.info("Enabled VCNS Timer service")

        # Start service
        subprocess.run(["systemctl", "start", "vcns-timer.service"], check=True)
        logger.info("Started VCNS Timer service")

        # Check status
        subprocess.run(["systemctl", "status", "vcns-timer.service"], check=False)
        return True
    except PermissionError:
        logger.error(f"Permission denied: Run this script with sudo (e.g., 'sudo python3 {__file__}')")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Systemd command failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Generating VCNS Timer systemd service file...")
    if create_service_file():
        sys.exit(0)
    else:
        sys.exit(1)