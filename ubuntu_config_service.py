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
        logger.error(f"An unexpected error occurred while executing command: {e}", exc_info=True)
        return False, f"An unexpected error occurred: {e}"

# --- Helper for CIDR conversion ---
def subnet_mask_to_cidr(subnet_mask):
    """Converts a subnet mask (e.g., '255.255.255.0') to CIDR notation (e.g., 24)."""
    try:
        network = ipaddress.IPv4Network(f'0.0.0.0/{subnet_mask}', strict=False)
        return network.prefixlen
    except ipaddress.AddressValueError:
        logger.error(f"Invalid subnet mask format: {subnet_mask}")
        return None
    except Exception as e:
        logger.error(f"Error converting subnet mask to CIDR: {e}")
        return None

# --- Netplan Configuration Functions ---
def _get_network_interface_name():
    """
    Attempts to find a common network interface name (e.g., eth0, enp0sX).
    This is a heuristic and might need to be made configurable for robust deployments.
    """
    try:
        # List common interface types
        interfaces = [f.name for f in os.scandir('/sys/class/net') if f.is_dir()]
        
        # Prioritize wired interfaces
        for iface in interfaces:
            if iface.startswith('eth') or iface.startswith('enp'):
                logger.info(f"Detected primary network interface: {iface}")
                return iface
        
        # Fallback to any detected interface if no common wired one is found
        if interfaces:
            logger.warning(f"No common wired interface found. Using first detected interface: {interfaces[0]}")
            return interfaces[0]

    except Exception as e:
        logger.error(f"Error detecting network interface: {e}")
    
    logger.error("Could not detect any network interface. Please specify manually.")
    return None # Indicate failure to detect

def _generate_netplan_yaml(ip_type, ip_address, subnet_mask, gateway, dns_server, interface_name):
    """
    Generates the Netplan YAML configuration based on the provided settings.
    """
    if not interface_name:
        raise ValueError("Network interface name is required to generate Netplan configuration.")

    netplan_config = {
        'network': {
            'version': 2,
            'renderer': 'networkd', # Or 'NetworkManager' if that's preferred
            'ethernets': {
                interface_name: {}
            }
        }
    }
    
    if ip_type == 'dynamic':
        netplan_config['network']['ethernets'][interface_name]['dhcp4'] = True
        logger.info(f"Generated Netplan YAML for dynamic IP on {interface_name}.")
    elif ip_type == 'static':
        if not all([ip_address, subnet_mask, gateway]):
            raise ValueError("For static IP, ipAddress, subnetMask, and gateway are required.")
        
        cidr = subnet_mask_to_cidr(subnet_mask)
        if cidr is None:
            raise ValueError("Invalid subnet mask provided for CIDR conversion.")

        netplan_config['network']['ethernets'][interface_name]['dhcp4'] = False
        netplan_config['network']['ethernets'][interface_name]['addresses'] = [f"{ip_address}/{cidr}"]
        netplan_config['network']['ethernets'][interface_name]['routes'] = [
            {'to': 'default', 'via': gateway}
        ]
        if dns_server:
            netplan_config['network']['ethernets'][interface_name]['nameservers'] = {
                'addresses': [dns_server]
            }
        logger.info(f"Generated Netplan YAML for static IP {ip_address}/{cidr} on {interface_name}.")
    else:
        raise ValueError(f"Invalid ipType: {ip_type}. Must be 'dynamic' or 'static'.")
    
    return netplan_config

def _write_and_apply_netplan(netplan_data):
    """
    Writes the Netplan configuration to a YAML file and applies it.
    """
    try:
        # Ensure the directory exists (it should be mounted from host)
        os.makedirs(NETPLAN_CONFIG_DIR, exist_ok=True)
        
        # Write the YAML content to the dedicated Netplan file
        with open(NETPLAN_CONFIG_FILE, 'w') as f:
            yaml.dump(netplan_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Netplan configuration written to {NETPLAN_CONFIG_FILE}")

        # Apply the Netplan configuration
        success, output = run_command(['netplan', 'apply'])
        if not success:
            raise Exception(f"Failed to apply Netplan configuration: {output}")
        
        logger.info("Netplan configuration applied successfully.")
        return True, "Netplan configuration applied successfully."
    except Exception as e:
        logger.error(f"Error writing or applying Netplan configuration: {e}")
        return False, f"Error applying network settings: {e}"

# --- Flask Routes ---
@app.route('/apply_network_settings', methods=['POST'])
def apply_network_settings():
    """
    Receives network configuration (dynamic/static IP) and applies them via Netplan.
    """
    data = request.get_json()
    if not data:
        logger.warning("No JSON data received for network settings.")
        return jsonify({"status": "error", "message": "No JSON data provided."}), 400

    ip_type = data.get('ipType')
    ip_address = data.get('ipAddress')
    subnet_mask = data.get('subnetMask')
    gateway = data.get('gateway')
    dns_server = data.get('dnsServer')

    logger.info(f"Received network configuration request: {data}")

    try:
        interface_name = _get_network_interface_name()
        if not interface_name:
            return jsonify({"status": "error", "message": "Could not detect network interface. Please configure manually."}), 500

        netplan_config = _generate_netplan_yaml(ip_type, ip_address, subnet_mask, gateway, dns_server, interface_name)
        success, message = _write_and_apply_netplan(netplan_config)

        if success:
            logger.info(f"Network settings applied: {message}")
            return jsonify({"status": "success", "message": message}), 200
        else:
            logger.error(f"Failed to apply network settings: {message}")
            return jsonify({"status": "error", "message": message}), 500
    except ValueError as ve:
        logger.warning(f"Invalid input for network settings: {ve}")
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        logger.critical(f"Unexpected error in apply_network_settings: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {e}"}), 500

@app.route('/apply_time_settings', methods=['POST'])
def apply_time_settings():
    """
    Receives time synchronization settings (NTP or manual) and attempts to apply them.
    Uses 'timedatectl' for NTP settings and 'date' command for manual time.
    """
    data = request.get_json()
    if not data:
        logger.warning("No JSON data received for time settings.")
        return jsonify({"status": "error", "message": "No JSON data provided."}), 400

    time_type = data.get('timeType')
    ntp_server = data.get('ntpServer')
    manual_date = data.get('manualDate')
    manual_time = data.get('manualTime')

    logger.info(f"Received time configuration request: {data}")

    try:
        if time_type == 'ntp':
            logger.info(f"Setting time synchronization to NTP with server: {ntp_server if ntp_server else DEFAULT_NTP_SERVER}")
            
            # Disable manual NTP first
            success_disable, error_disable = run_command(['timedatectl', 'set-ntp', 'false'])
            if not success_disable:
                logger.error(f"Failed to disable NTP: {error_disable}")
                return jsonify({"status": "error", "message": f"Failed to disable NTP: {error_disable}"}), 500

            # Enable NTP
            success_enable, error_enable = run_command(['timedatectl', 'set-ntp', 'true'])
            if not success_enable:
                logger.error(f"Failed to enable NTP: {error_enable}")
                return jsonify({"status": "error", "message": f"Failed to enable NTP: {error_enable}"}), 500
            
            logger.info("NTP synchronization enabled.")
            return jsonify({"status": "success", "message": "NTP synchronization enabled successfully."}), 200
        elif time_type == 'manual':
            if not all([manual_date, manual_time]):
                logger.warning("Missing manual time details.")
                return jsonify({"status": "error", "message": "For manual time, manualDate and manualTime are required."}), 400

            try:
                datetime.strptime(f"{manual_date} {manual_time}", "%Y-%m-%d %H:%M")
            except ValueError:
                logger.warning("Invalid manual date or time format.")
                return jsonify({"status": "error", "message": "Invalid date or time format. Use YYYY-MM-DD and HH:MM."}), 400

            logger.info(f"Setting manual time to: {manual_date} {manual_time}")
            # Disable NTP first
            success_disable, error_disable = run_command(['timedatectl', 'set-ntp', 'false'])
            if not success_disable:
                logger.error(f"Failed to disable NTP before setting manual time: {error_disable}")
                return jsonify({"status": "error", "message": f"Failed to disable NTP: {error_disable}"}), 500

            # Set the date and time
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
        use_reloader=False,
        use_debugger=False
    )
