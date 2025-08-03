# ubuntu_config_service.py
# This Flask application runs on your Ubuntu machine to receive configuration commands
# from the main Flask web app and execute system-level commands using subprocess.
# This version supports both real execution on a full Ubuntu OS (or privileged container)
# and mocking of system commands when in a Docker test environment.

import os
import subprocess
import json
import logging
from flask import Flask, request, jsonify
from datetime import datetime
import ipaddress # For CIDR conversion
import yaml # For YAML manipulation (install with pip install pyyaml)
import time # For sleep
from pathlib import Path

# --- Logging Configuration ---
LOG_FILE = '/var/log/ubuntu_config_service.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('UbuntuConfigService')

app = Flask(__name__)

# --- Docker Test Mode Flag ---
# This environment variable will be set in docker-compose.dev.yml for testing purposes.
# When True, timedatectl and netplan commands will be mocked.
IN_DOCKER_TEST_MODE = os.getenv("IN_DOCKER_TEST_MODE", "false").lower() == "true"
if IN_DOCKER_TEST_MODE:
    logger.warning("Running in Docker Test Mode: timedatectl and netplan commands will be mocked.")

# --- Constants ---
NETPLAN_CONFIG_DIR = '/etc/netplan/'
NETPLAN_CONFIG_FILE = os.path.join(NETPLAN_CONFIG_DIR, '01-vcns-network.yaml') # Dedicated config file
DEFAULT_NTP_SERVER = 'pool.ntp.org' # Default NTP server if none provided

# --- Helper Function to Run Shell Commands ---
def run_command(command_list, check_output=False):
    """
    Executes a shell command.
    Args:
        command_list (list): A list of strings representing the command and its arguments.
                             e.g., ['timedatectl', 'set-ntp', 'true']
        check_output (bool): If True, capture and return stdout/stderr.
                             If False, just check return code.
    Returns:
        tuple: (success_boolean, output_string_or_None)
    """
    try:
        logger.info(f"Executing command: {' '.join(command_list)}")

        # In Docker, we typically run as root, so 'sudo' is often not needed
        # and might not even be installed. We remove it from the command list.
        if command_list and command_list[0] == 'sudo':
            command_list = command_list[1:]
            logger.info(f"Removed 'sudo' from command. New command: {' '.join(command_list)}")

        # --- Mock system commands in Docker Test Mode ---
        if IN_DOCKER_TEST_MODE and command_list:
            command_name = command_list[0]
            if command_name in ['timedatectl', 'netplan']:
                mock_output = f"Mocked: {' '.join(command_list)} - This command would normally run on a full Ubuntu OS."
                logger.info(mock_output)
                return True, mock_output
        # --- End Mocking ---

        # Always capture output when using check=True, to prevent AttributeError
        # and to get detailed error messages.
        result = subprocess.run(command_list, capture_output=True, text=True, check=True)

        output = result.stdout.strip()
        if output:
            logger.info(f"Command output: {output}")
        return True, output
    except subprocess.CalledProcessError as e:
        error_output = (e.stderr or e.stdout or "").strip()
        logger.error(f"Command failed with exit code {e.returncode}: {error_output}")
        logger.error(f"Full command attempted: {' '.join(command_list)}")
        if "command not found" in error_output.lower() or "No such file or directory" in error_output:
            return False, f"Command '{command_list[0]}' not found. Ensure it is installed and in PATH."
        # Specific error message for timedatectl in non-systemd environments
        if "systemd as init system (PID 1)" in error_output or "Failed to connect to bus" in error_output:
            return False, f"Cannot execute '{command_list[0]}': This command requires systemd as init system (PID 1) and D-Bus, which are typically not available in a standard Docker container. This service is intended for a full Ubuntu OS."
        return False, f"Command execution failed: {error_output}"
    except FileNotFoundError:
        return False, f"Command '{command_list[0]}' not found. Is it installed and in PATH?"
    except Exception as e:
        logger.critical(f"An unexpected error occurred in run_command: {e}", exc_info=True)
        return False, f"An unexpected error occurred: {e}"


@app.route('/apply_network_settings', methods=['POST'])
def apply_network_settings():
    """
    Receives network configuration from the main Flask app and applies it to the system
    using Netplan.
    """
    try:
        data = request.json
        if not data:
            logger.error("No JSON data received.")
            return jsonify({"status": "error", "message": "No JSON data received."}), 400

        logger.info(f"Received JSON data for network settings: {json.dumps(data)}")

        ip_type = data.get('ipType')
        if not ip_type:
            logger.error("Missing 'ipType' in request data.")
            return jsonify({"status": "error", "message": "Missing 'ipType' field."}), 400

        ip_address = data.get('ipAddress')
        subnet_mask = data.get('subnetMask')
        gateway = data.get('gateway')
        dns_server = data.get('dnsServer')

        netplan_config = {
            'network': {
                'version': 2,
                'renderer': 'networkd',
                'ethernets': {
                    'eth0': { # Assuming 'eth0' is the primary network interface
                        'dhcp4': True if ip_type == 'dynamic' else False
                    }
                }
            }
        }

        if ip_type == 'static':
            if not all([ip_address, subnet_mask, gateway, dns_server]):
                logger.error("Missing required fields for static IP configuration.")
                return jsonify({"status": "error", "message": "Missing required fields for static IP."}), 400

            # Convert subnet mask to CIDR prefix
            try:
                cidr_prefix = ipaddress.IPv4Network(f'0.0.0.0/{subnet_mask}').prefixlen
                address_cidr = f"{ip_address}/{cidr_prefix}"
            except (ipaddress.AddressValueError, ValueError) as e:
                logger.error(f"Invalid IP address or subnet mask: {e}")
                return jsonify({"status": "error", "message": "Invalid IP or subnet mask."}), 400

            netplan_config['network']['ethernets']['eth0']['dhcp4'] = False
            netplan_config['network']['ethernets']['eth0']['addresses'] = [address_cidr]
            netplan_config['network']['ethernets']['eth0']['routes'] = [{'to': 'default', 'via': gateway}]
            netplan_config['network']['ethernets']['eth0']['nameservers'] = {'addresses': [dns_server]}

        # Write the Netplan configuration to a dedicated file
        try:
            yaml_content = yaml.dump(netplan_config, default_flow_style=False)
            logger.info(f"Generated Netplan YAML content:\n{yaml_content}")

            # Use a temporary file for atomic write
            temp_file = Path(NETPLAN_CONFIG_FILE + '.tmp')
            temp_file.write_text(yaml_content)
            temp_file.rename(NETPLAN_CONFIG_FILE)

            logger.info(f"Successfully wrote Netplan configuration to {NETPLAN_CONFIG_FILE}")

        except Exception as e:
            logger.critical(f"Failed to write Netplan configuration file: {e}", exc_info=True)
            return jsonify({"status": "error", "message": f"Failed to write Netplan config file: {e}"}), 500

        # Wait for a moment to ensure the file system has updated.
        time.sleep(1)

        # Validate the Netplan configuration
        success_generate, error_generate = run_command(['netplan', 'generate'])
        if not success_generate:
            logger.error(f"Netplan generate failed: {error_generate}")
            return jsonify({"status": "error", "message": f"Netplan generate failed: {error_generate}"}), 500

        # Apply the new network configuration
        success_apply, error_apply = run_command(['netplan', 'apply'])

        if success_apply:
            logger.info("Network settings applied successfully.")
            return jsonify({"status": "success", "message": "Network settings applied successfully."}), 200
        else:
            logger.error(f"Netplan apply failed: {error_apply}")
            return jsonify({"status": "error", "message": f"Failed to apply network settings: {error_apply}"}), 500

    except Exception as e:
        logger.critical(f"Unexpected error in apply_network_settings: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {e}"}), 500


@app.route('/apply_time_settings', methods=['POST'])
def apply_time_settings():
    """
    Receives time configuration from the main Flask app and applies it to the system.
    """
    try:
        data = request.json
        if not data:
            logger.error("No JSON data received for time settings.")
            return jsonify({"status": "error", "message": "No JSON data received."}), 400

        time_type = data.get('timeType')
        timezone = data.get('timezone')
        manual_date = data.get('manualDate')
        manual_time = data.get('manualTime')
        ntp_server = data.get('ntpServer') or DEFAULT_NTP_SERVER

        # Always set timezone first
        if timezone:
            success_tz, error_tz = run_command(['timedatectl', 'set-timezone', timezone])
            if not success_tz:
                logger.error(f"Failed to set timezone: {error_tz}")
                # Don't fail the whole request, but warn.
                pass

        if time_type == 'ntp':
            # Enable NTP synchronization
            success_ntp_on, error_ntp_on = run_command(['timedatectl', 'set-ntp', 'true'])
            if success_ntp_on:
                logger.info("NTP synchronization enabled successfully.")
                # We can't set a specific NTP server with timedatectl, it uses system config.
                # The user's provided NTP server is just for documentation or a more advanced config.
                return jsonify({"status": "success", "message": "NTP synchronization enabled."}), 200
            else:
                logger.error(f"Failed to enable NTP: {error_ntp_on}")
                return jsonify({"status": "error", "message": f"Failed to enable NTP: {error_ntp_on}"}), 500
        elif time_type == 'manual':
            # Disable NTP synchronization
            success_ntp_off, error_ntp_off = run_command(['timedatectl', 'set-ntp', 'false'])
            if not success_ntp_off:
                 logger.error(f"Failed to disable NTP: {error_ntp_off}")
                 # Still proceed with setting manual time, but log the warning
                 pass

            # Set manual time
            if not manual_date or not manual_time:
                 logger.error("Manual date or time not provided.")
                 return jsonify({"status": "error", "message": "Manual date and time are required."}), 400

            set_time_command = ['timedatectl', 'set-time', f"{manual_date} {manual_time}:00"]
            success_set_time, error_set_time = run_command(set_time_command)

            if success_set_time:
                logger.info("Manual time set successfully.")
                return jsonify({"status": "success", "message": "Manual time set successfully."}), 200
            else:
                logger.error(f"Failed to set manual time: {error_set_time}")
                return jsonify({"status": "error", "message": f"Failed to set manual time: {error_set_time}"}), 500
        else:
            logger.warning(f"Invalid timeType received: {time_type}")
            return jsonify({"status": "error", "message": "Invalid timeType. Must be 'ntp' or 'manual'."}), 400
    except Exception as e:
        logger.critical(f"Unexpected error in apply_time_settings: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {e}"}), 500

# --- Main Execution ---
if __name__ == '__main__':
    logger.info("Starting Ubuntu Configuration Service...")
    # Ensure Netplan config directory exists on the host (via mount)
    # This mkdir is safe even if the directory already exists.
    # It's important for the case where the service runs natively or in a privileged container.
    os.makedirs(NETPLAN_CONFIG_DIR, exist_ok=True)
    app.run(
        host='0.0.0.0',
        port=5002,
        debug=False,
        threaded=True,
        use_reloader=False
    )
