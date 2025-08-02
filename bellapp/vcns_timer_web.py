import os
import sys
import time
import signal
import logging
import threading
import traceback
import requests # Import requests for making HTTP calls to external services
import subprocess
import re    
import socket
from pathlib import Path
from functools import wraps
from contextlib import contextmanager
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import bcrypt
import json
from datetime import datetime, timedelta
import pytz
import psutil
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from logging.handlers import RotatingFileHandler
import uuid # For generating license keys and alarm IDs

# Configure logging with rotation for robust application monitoring
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "vcns_timer_web.log"
USERS_FILE = BASE_DIR / "users.json"
CONFIG_FILE = BASE_DIR / "config.json"  # New config file for persistent application settings
ALARMS_FILE = BASE_DIR / "alarms.json" # New file for storing alarm data
os.makedirs(LOG_DIR, exist_ok=True) # Ensure the logs directory exists

def setup_logging():
    """
    Setup comprehensive logging with rotation and error handling.
    Logs are written to a file and also output to the console.
    This helps in debugging and monitoring the application's health.
    """
    try:
        log_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        )

        # File handler with rotation: logs will rotate after 10MB, keeping 5 backup files.
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(logging.INFO) # Set file logging level to INFO

        # Console handler: outputs logs to standard output for immediate visibility.
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_formatter)
        console_handler.setLevel(logging.INFO) # Set console logging level to INFO

        # Root logger configuration: ensures all logs from this application go through these handlers.
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO) # Global logging level
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        # Suppress excessive third-party logs to keep our logs clean and focused on application events.
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)

        return logging.getLogger("VCNS-Timer-Web") # Return a named logger for application-specific logging
    except Exception as e:
        # Fallback logging if setting up file logging fails (e.g., permission issues).
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        logger = logging.getLogger("VCNS-Timer-Web")
        logger.error(f"Failed to setup file logging: {e}")
        return logger

logger = setup_logging() # Initialize the application logger

# Application state management class for monitoring health and errors.
class AppState:
    def __init__(self):
        self.shutdown_requested = False # Flag to signal graceful shutdown
        self.last_heartbeat = time.time() # Timestamp of the last successful operation
        self.error_count = 0 # Counter for transient errors
        self.max_errors = 50 # Threshold for entering recovery mode
        self.recovery_mode = False # Flag indicating if the application is in recovery mode
        self.lock = threading.Lock() # Lock for thread-safe updates to state variables

    def increment_error(self):
        """Increments the error count and transitions to recovery mode if threshold is met."""
        with self.lock:
            self.error_count += 1
            if self.error_count >= self.max_errors:
                self.recovery_mode = True
                logger.warning(f"Entering recovery mode after {self.error_count} errors")

    def reset_errors(self):
        """Resets the error count and exits recovery mode."""
        with self.lock:
            self.error_count = 0
            self.recovery_mode = False

    def heartbeat(self):
        """Updates the last heartbeat timestamp, indicating the application is active."""
        with self.lock:
            self.last_heartbeat = time.time()

app_state = AppState() # Instantiate the application state manager

# Initialize Flask application
app = Flask(__name__)

def get_or_create_secret_key():
    """
    Retrieves the Flask secret key from a file, or generates a new one if it doesn't exist
    or is invalid. This ensures session persistence and security.
    """
    secret_file = BASE_DIR / "secret.key"

    # Attempt to read existing key
    if secret_file.exists():
        try:
            with open(secret_file, 'rb') as f:
                key = f.read()
            # Ensure key is at least 32 bytes for sufficient entropy
            if len(key) >= 32:
                logger.info(f"Loaded existing secret key from {secret_file}.")
                return key
            else:
                logger.warning(f"Existing secret key in {secret_file} is too short ({len(key)} bytes). Generating new one.")
        except Exception as e:
            logger.warning(f"Could not read existing secret key file {secret_file}: {e}. Generating new one.")
    
    # Generate new secret key if no valid existing key was found or if there was an error reading
    secret_key = os.urandom(32) # Generate a strong random key
    try:
        with open(secret_file, 'wb') as f:
            f.write(secret_key)
        # Set restrictive permissions (read/write for owner only) on the secret key file for security
        os.chmod(secret_file, 0o600)
        logger.info(f"Generated and saved new secret key to {secret_file}.")
    except Exception as e:
        logger.critical(f"FATAL: Could not save new secret key to {secret_file}: {e}. "
                        "This will lead to session management issues and potential application failure.")
        # If the secret key cannot be saved, the application is in a critical state and should not proceed.
        raise

    return secret_key # Always return a generated key if no valid existing one was found


# Updated Flask app configuration with better session handling and security.
app.config.update(
    SECRET_KEY=get_or_create_secret_key(),  # Persistent secret key for session security
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,  # 2MB maximum file size for uploads
    SEND_FILE_MAX_AGE_DEFAULT=300,  # 5 minutes cache control for static files
    PROPAGATE_EXCEPTIONS=True, # Allows exceptions to propagate for better debugging in development

    # Session configuration for persistent login and security
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24), # Sessions expire after 24 hours of inactivity
    SESSION_COOKIE_SECURE=False,  # Set to True if using HTTPS in production for secure cookies
    SESSION_COOKIE_HTTPONLY=True, # Prevents client-side JavaScript access to session cookie
    SESSION_COOKIE_SAMESITE='Lax', # Protects against CSRF attacks in modern browsers
    SESSION_COOKIE_NAME='vcns_session', # Custom name for the session cookie
    SESSION_REFRESH_EACH_REQUEST=True, # Renews the session ID on each request for security
    USE_SESSION_FOR_NEXT=True, # Stores the next URL in the session for redirect after login
)

# Initialize Flask-Login for user session management
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login" # The view name for the login page
login_manager.login_message = "Please log in to access this page." # Message shown for required login
login_manager.login_message_category = "info" # Category for flash message styling
login_manager.session_protection = "strong" # Provides strong session protection against session fixation
login_manager.refresh_view = "login" # View to redirect to when session needs to be refreshed

# User class for Flask-Login, extended to include user roles and individual user settings.
class User(UserMixin):
    def __init__(self, id, role="admin", user_settings=None):
        self.id = id # Unique identifier for the user (e.g., "admin", "superuser")
        self.role = role # User's role: "admin" or "superuser"
        # user_settings holds individual user preferences, including feature activation status
        self.user_settings = user_settings if user_settings is not None else {}

    def get_id(self):
        """Returns the user's unique ID as a string, required by Flask-Login."""
        return str(self.id)

    @property
    def is_superuser(self):
        """Convenience property to check if the user has superuser role."""
        return self.role == "superuser"

@login_manager.user_loader
def load_user(user_id):
    """
    Callback function to load a user from the user ID. Required by Flask-Login.
    This function retrieves user data, including role and settings, from the users.json file.
    """
    try:
        users_data = load_users_data() # Load all users data from the file
        user_info = users_data.get(user_id) # Get specific user's information
        if user_info:
            # Create and return a User object with role and user_settings
            return User(user_id, user_info.get('role', 'admin'), user_info.get('user_settings', {}))
        return None # Return None if user not found
    except Exception as e:
        logger.error(f"Error loading user {user_id}: {e}")
        return None

# Functions to load and save user data from/to a JSON file.
def load_users_data():
    """
    Loads all user data from the JSON file. If the file doesn't exist, it initializes
    default 'admin' and 'superuser' accounts with hashed passwords and their respective roles
    and initial feature activation statuses.
    """
    try:
        if USERS_FILE.exists():
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        else: 
            # Initialize default users if file doesn't exist
            default_admin_password = "adminpassword".encode('utf-8') 
            default_superuser_password = "superpassword".encode('utf-8')
            
            # Hash passwords using bcrypt for security
            hashed_admin = bcrypt.hashpw(default_admin_password, bcrypt.gensalt()).decode('utf-8')
            hashed_superuser = bcrypt.hashpw(default_superuser_password, bcrypt.gensalt()).decode('utf-8')

            # Define default user data, including roles and initial user settings.
            # Superuser has features_activated by default. Admin needs to activate.
            users_data = {
                'admin': {'password_hash': hashed_admin, 'role': 'admin', 'user_settings': {'features_activated': False}},
                'superuser': {'password_hash': hashed_superuser, 'role': 'superuser', 'user_settings': {'features_activated': True}}
            }
            with open(USERS_FILE, 'w') as f:
                json.dump(users_data, f, indent=2) # Save the initial user data to file
            logger.info("Initialized default 'admin' and 'superuser' users.")
            return users_data
    except Exception as e:
        logger.critical(f"FATAL: Failed to load or initialize users data from {USERS_FILE}: {e}. Application cannot proceed.")
        raise # Re-raise to prevent the app from starting if user data is critical

def save_users_data(users_data):
    """Saves all user data to the JSON file, ensuring data persistence."""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users_data, f, indent=2)
        logger.info("Users data updated.")
    except Exception as e:
        logger.error(f"Failed to save users data to {USERS_FILE}: {e}")

# --- Centralized Application Configuration Management ---
# This dictionary will hold all application settings (API URL, Network, Time, System-Wide License)
app_settings = {}

def get_default_settings():
    """
    Returns a dictionary of default initial settings for the application.
    This includes network, time, and a placeholder for the system-wide license,
    and a log for individually activated users.
    """
    return {
        'API_SERVICE_URL': os.environ.get("API_SERVICE_URL", "http://localhost:5001"), # Default API URL for timer service
        'networkSettings': {
            'ipType': 'dynamic', # Default IP configuration
            'ipAddress': '',
            'subnetMask': '',
            'gateway': '',
            'dnsServer': ''
        },
        'timeSettings': {
            'timeType': 'ntp', # Default time synchronization method
            'ntpServer': 'pool.ntp.org', # Default NTP server
            'manualDate': '', # For manual time setting (YYYY-MM-DD)
            'manualTime': ''  # For manual time setting (HH:MM)
        },
        'license': {
            'key': None, # System-wide license key
            'expiry': None, # System-wide license expiry date (ISO format datetime string)
            'status': 'unlicensed' # Current status of the system-wide license
        },
        'activated_user_log': [], # Log of users who have individually activated features
        'ubuntuDeviceIpAddress': '' # NEW: IP address of the Ubuntu device running the config service
    }

def load_config():
    """
    Loads application settings from the JSON configuration file.
    It performs a deep merge with default settings to ensure all configuration keys are present,
    even if new ones are added in later versions. It also checks the system-wide license status on load.
    """
    global app_settings # Declare intent to modify the global variable
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            try:
                loaded_settings = json.load(f)
                default_settings = get_default_settings()
                
                # Helper for deep merging dictionaries, ensuring nested structures are handled correctly.
                def deep_merge(dict1, dict2):
                    for k, v in dict2.items():
                        if k in dict1 and isinstance(dict1[k], dict) and isinstance(v, dict):
                            dict1[k] = deep_merge(dict1[k], v)
                        else:
                            dict1[k] = v
                    return dict1

                app_settings = deep_merge(default_settings, loaded_settings)

                # Ensure activated_user_log is always a list, even if corrupted in file.
                if not isinstance(app_settings.get('activated_user_log'), list):
                    app_settings['activated_user_log'] = []

                logger.info(f"Configuration loaded from {CONFIG_FILE}")
            except json.JSONDecodeError:
                logger.error(f"Error decoding JSON from {CONFIG_FILE}. Reverting to default settings.")
                app_settings = get_default_settings()
            except Exception as e:
                logger.error(f"Error loading config.json: {e}. Reverting to default settings.")
                app_settings = get_default_settings()
    else:
        app_settings = get_default_settings()
        logger.info(f"No config.json found. Initializing with default settings.")
    
    # Always check the system-wide license status immediately after loading configuration.
    check_license_status()

def save_config(settings_data):
    """Saves the current application settings to the JSON configuration file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(settings_data, f, indent=4) # Use indent for readable JSON
        logger.info("Configuration saved successfully.")
    except IOError as e:
        logger.error(f"Failed to save settings to {CONFIG_FILE}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while saving configuration: {e}")

def get_current_dynamic_ip(interface='eth0'):
    """
    Gets the current dynamic IP address of a specified network interface by
    parsing the output of the 'ip addr show' command.
    """
    try:
        result = subprocess.run(
            ['ip', 'addr', 'show', interface],
            check=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        output = result.stdout
        # Regular expression to find a dynamic IP address
        match = re.search(r'inet (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}).*?scope global dynamic', output)
        if match:
            return match.group(1) # e.g., "192.168.1.5/24"
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.error(f"Failed to get current dynamic IP for {interface}: {e}")
    return None

def execute_privileged_command(command):
    """
    Executes a command with sudo, providing logging and error handling.
    """
    try:
        logger.info(f"Executing privileged command: {' '.join(command)}")
        result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=10)
        logger.info(f"Command successful: {result.stdout}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with error: {e.stderr}")
        return False, e.stderr
    except FileNotFoundError:
        logger.error(f"Command not found: {command[0]}")
        return False, f"Command not found: {command[0]}"
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after 10 seconds: {' '.join(command)}")
        return False, f"Command timed out: {' '.join(command)}"


@app.route("/api/configure_dynamic_ip", methods=["POST"])
@login_required
def configure_dynamic_ip():
    """
    Handles the request to configure a dynamic IP address.
    Requires superuser role to execute privileged commands.
    """
    if not current_user.is_superuser:
        logger.warning(f"Unauthorized attempt by user '{current_user.id}' to configure dynamic IP.")
        return jsonify({"status": "error", "message": "Unauthorized: Only superusers can change network settings."}), 403

    try:
        interface = 'eth0'

        # Step 1: Generate and write the new network configuration for DHCP to /etc/network/interfaces
        logger.info(f"Writing new dynamic IP configuration for {interface}...")
        interfaces_content = f"""
auto lo
iface lo inet loopback

auto {interface}
iface {interface} inet dhcp
"""
        command_write_file = [
            'sudo', 'bash', '-c',
            f'echo -e "{interfaces_content}" > /etc/network/interfaces'
        ]
        success, error_output = execute_privileged_command(command_write_file)
        if not success:
            return jsonify({"status": "error", "message": f"Failed to write network configuration: {error_output}"}), 500

        # Step 2: Restart the network interface to apply changes
        logger.info(f"Restarting network interface {interface}...")
        command_restart_interface = ['sudo', 'ifdown', interface, '&&', 'sudo', 'ifup', interface]
        success, error_output = execute_privileged_command(command_restart_interface)
        if not success:
            logger.error(f"Restarting interface failed. This may require a reboot. Error: {error_output}")
            return jsonify({
                "status": "warning",
                "message": "Failed to restart network interface. A reboot may be required.",
                "reboot_required": True
            }), 500

        # Step 3: Save the new configuration to the app's config file
        app_settings['networkSettings']['ipType'] = 'dynamic'
        # Clear old static IP details
        app_settings['networkSettings']['ipAddress'] = ''
        app_settings['networkSettings']['subnetMask'] = ''
        app_settings['networkSettings']['gateway'] = ''
        app_settings['networkSettings']['dnsServer'] = ''
        save_config(app_settings)
        
        return jsonify({"status": "success", "message": "Dynamic IP configured successfully. No reboot required.", "reboot_required": False}), 200

    except Exception as e:
        logger.error(f"An error occurred during dynamic IP configuration: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": "An internal server error occurred."}), 500

    
@app.route("/api/configure_static_ip", methods=["POST"])
@login_required
def configure_static_ip():
    """
    Handles the request to configure a static IP address.
    Requires superuser role to execute privileged commands.
    """
    if not current_user.is_superuser:
        logger.warning(f"Unauthorized attempt by user '{current_user.id}' to configure static IP.")
        return jsonify({"status": "error", "message": "Unauthorized: Only superusers can change network settings."}), 403

    try:
        data = request.json
        ip_address = data.get('ipAddress')
        subnet_mask = data.get('subnetMask')
        gateway = data.get('gateway')
        dns_servers = data.get('dnsServer')
        interface = 'eth0'

        if not all([ip_address, subnet_mask, gateway]):
            return jsonify({"status": "error", "message": "Missing required network parameters."}), 400

        # Step 1: Generate and write the new network configuration to /etc/network/interfaces
        logger.info(f"Writing new static IP configuration for {interface}...")
        interfaces_content = f"""
auto lo
iface lo inet loopback

auto {interface}
iface {interface} inet static
    address {ip_address}
    netmask {subnet_mask}
    gateway {gateway}
    dns-nameservers {dns_servers}
"""
        # Writing to file requires sudo, so we'll use a subprocess call for this
        command_write_file = [
            'sudo', 'bash', '-c',
            f'echo -e "{interfaces_content}" > /etc/network/interfaces'
        ]
        success, error_output = execute_privileged_command(command_write_file)
        if not success:
            return jsonify({"status": "error", "message": f"Failed to write network configuration: {error_output}"}), 500

        # Step 2: Stop any DHCP client and remove the old dynamic IP
        logger.info("Stopping DHCP client and removing old dynamic IP...")
        current_dynamic_ip_with_prefix = get_current_dynamic_ip(interface)
        if current_dynamic_ip_with_prefix:
            command_dhclient_stop = ['sudo', 'dhclient', '-r', interface]
            execute_privileged_command(command_dhclient_stop)

            command_del_ip = ['sudo', 'ip', 'addr', 'del', current_dynamic_ip_with_prefix, 'dev', interface]
            execute_privileged_command(command_del_ip)

        # Step 3: Restart the network interface to apply changes
        logger.info(f"Restarting network interface {interface}...")
        command_restart_interface = ['sudo', 'ifdown', interface, '&&', 'sudo', 'ifup', interface]
        success, error_output = execute_privileged_command(command_restart_interface)
        if not success:
            logger.error(f"Restarting interface failed. This may require a reboot. Error: {error_output}")
            return jsonify({
                "status": "warning",
                "message": "Failed to restart network interface. A reboot may be required.",
                "reboot_required": True
            }), 500

        # Step 4: Save the new configuration to the app's config file
        app_settings['networkSettings']['ipType'] = 'static'
        app_settings['networkSettings']['ipAddress'] = ip_address
        app_settings['networkSettings']['subnetMask'] = subnet_mask
        app_settings['networkSettings']['gateway'] = gateway
        app_settings['networkSettings']['dnsServer'] = dns_servers
        save_config(app_settings)

        return jsonify({"status": "success", "message": "Static IP configured successfully. No reboot required.", "reboot_required": False}), 200

    except Exception as e:
        logger.error(f"An error occurred during static IP configuration: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": "An internal server error occurred."}), 500


# NEW ROUTE: Superadmin password reset functionality
@app.route("/admin/reset_password", methods=["POST"])
@login_required
def admin_reset_password():
    """
    Allows a superuser to reset another user's password.
    Requires superuser role.
    """
    if not current_user.is_superuser:
        flash("Unauthorized: Only superusers can reset passwords.", "error")
        logger.warning(f"Unauthorized attempt by user '{current_user.id}' to access admin password reset.")
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    target_username = request.form.get("username")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if not all([target_username, new_password, confirm_password]):
        flash("All fields (username, new password, confirm password) are required.", "error")
        return jsonify({"status": "error", "message": "All fields are required"}), 400

    if new_password != confirm_password:
        flash("New password and confirm password do not match.", "error")
        return jsonify({"status": "error", "message": "New passwords do not match"}), 400

    if len(new_password) < 8:
        flash("New password must be at least 8 characters long.", "error")
        return jsonify({"status": "error", "message": "New password must be at least 8 characters long"}), 400

    users_data = load_users_data()

    if target_username not in users_data:
        flash(f"User '{target_username}' not found.", "error")
        return jsonify({"status": "error", "message": f"User '{target_username}' not found"}), 404

    # Prevent superuser from resetting another superuser's password if desired, or allow if necessary.
    # For now, allow superuser to reset any user's password including other superusers.

    try:
        hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        users_data[target_username]['password_hash'] = hashed_new_password
        save_users_data(users_data)
        flash(f"Password for user '{target_username}' has been successfully reset.", "success")
        logger.info(f"Superuser '{current_user.id}' reset password for user '{target_username}'.")
        return jsonify({"status": "success", "message": f"Password for '{target_username}' reset successfully"}), 200
    except Exception as e:
        flash(f"Failed to reset password for '{target_username}': {e}", "error")
        logger.error(f"Error resetting password for '{target_username}' by superuser '{current_user.id}': {e}")
        return jsonify({"status": "error", "message": "Internal server error during password reset"}), 500
# --- Alarm Storage and Management Functions (Directly in Flask) ---
def load_alarms_data():
    """
    Loads alarm data from the alarms.json file.
    Includes safeguards to ensure alarm IDs are strings and handles JSON decoding errors.
    """
    if not ALARMS_FILE.exists():
        logger.info(f"Alarms file not found at {ALARMS_FILE}. Returning empty list.")
        return []
    try:
        with open(ALARMS_FILE, 'r') as f:
            alarms = json.load(f)
        
        # Safeguard: Ensure alarms is a list, and all 'id' fields are strings upon loading.
        # This prevents 'TypeError: Object of type UUID is not JSON serializable'.
        # Also ensures correct types for other fields.
        if not isinstance(alarms, list):
            logger.warning(f"Alarms data from {ALARMS_FILE} is not a list. Initializing with empty list.")
            return []

        cleaned_alarms = []
        for alarm in alarms:
            # Ensure alarm is a dictionary and has an 'id'
            if not isinstance(alarm, dict) or 'id' not in alarm:
                logger.warning(f"Skipping malformed alarm entry: {alarm}")
                continue

            if not isinstance(alarm['id'], str):
                try:
                    alarm['id'] = str(alarm['id'])
                except Exception as e:
                    logger.warning(f"Could not convert alarm ID '{alarm.get('id')}' to string during load. Skipping alarm. Error: {e}")
                    continue # Skip this alarm if its ID is problematic
            
            # Ensure volume and duration are integers
            if 'volume' in alarm and not isinstance(alarm['volume'], int):
                try: 
                    alarm['volume'] = int(alarm['volume'])
                except (ValueError, TypeError): 
                    logger.warning(f"Invalid 'volume' for alarm ID {alarm.get('id')}. Setting to 0. Value: {alarm['volume']}")
                    alarm['volume'] = 0 
            if 'duration' in alarm and not isinstance(alarm['duration'], int):
                try: 
                    alarm['duration'] = int(alarm['duration'])
                except (ValueError, TypeError): 
                    logger.warning(f"Invalid 'duration' for alarm ID {alarm.get('id')}. Setting to 0. Value: {alarm['duration']}")
                    alarm['duration'] = 0 
            
            # Ensure enabled is a boolean
            if 'enabled' in alarm and not isinstance(alarm['enabled'], bool):
                alarm['enabled'] = bool(alarm['enabled'])
            
            # Ensure days is a list
            if 'days' in alarm and not isinstance(alarm['days'], list):
                logger.warning(f"Invalid 'days' format for alarm ID {alarm.get('id')}. Expected list. Value: {alarm['days']}")
                alarm['days'] = [] # Default to empty list if format is incorrect
            
            cleaned_alarms.append(alarm)

        return cleaned_alarms
    except json.JSONDecodeError as e:
        logger.critical(f"FATAL ERROR: Could not decode alarms.json due to malformed JSON: {e}. "
                        "This file might be corrupted. Attempting to back up and start fresh.", exc_info=True)
        # Attempt to back up the corrupted file before returning an empty list
        if ALARMS_FILE.exists():
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            backup_path = ALARMS_FILE.with_suffix(f".json.bak.{timestamp}")
            try:
                os.rename(ALARMS_FILE, backup_path)
                logger.info(f"Corrupted alarms.json backed up to {backup_path}")
            except OSError as io_error:
                logger.error(f"Failed to backup corrupted alarms.json: {io_error}", exc_info=True)
        return [] # Return empty list to prevent further crashes from corrupted data
    except Exception as e:
        logger.critical(f"FATAL ERROR: Unexpected error loading alarms data: {e}", exc_info=True)
        return []

def save_alarms_data(alarms_list):
    """
    Saves alarm data to the alarms.json file.
    Ensures alarm IDs are strings before saving to prevent serialization errors.
    """
    try:
        # Safeguard: Ensure all 'id' fields are strings before saving.
        # This explicitly converts any UUID objects to strings if they somehow
        # ended up in the 'alarms' list.
        serializable_alarms = []
        for alarm in alarms_list:
            if not isinstance(alarm, dict): # Skip non-dict entries
                logger.warning(f"Skipping non-dictionary alarm entry during save: {alarm}")
                continue

            temp_alarm = alarm.copy() # Work on a copy to avoid modifying original list during iteration
            if 'id' in temp_alarm and not isinstance(temp_alarm['id'], str):
                try:
                    temp_alarm['id'] = str(temp_alarm['id'])
                except Exception as e:
                    logger.error(f"Could not convert alarm ID '{temp_alarm.get('id')}' to string for saving. Error: {e}. Skipping this alarm.")
                    continue
            serializable_alarms.append(temp_alarm)
        
        with open(ALARMS_FILE, 'w') as f:
            json.dump(serializable_alarms, f, indent=4) # Use indent for pretty-printing JSON
        logger.debug("Alarms saved to file")
    except Exception as e:
        logger.critical(f"FATAL ERROR: Failed to save alarms data to {ALARMS_FILE}: {e}", exc_info=True)
        # In a production environment, you might want to alert administrators
        # or implement a retry mechanism here.

# Retry strategy for robust API calls, allowing for transient network issues.
RETRY_STRATEGY = Retry(
    total=3, # Total number of retries
    backoff_factor=0.5, # Factor by which retry delay increases
    status_forcelist=[429, 500, 502, 503, 504], # HTTP status codes to retry on
    allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"] # HTTP methods to retry
)

def create_session():
    """Creates a requests session configured with the retry strategy."""
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=RETRY_STRATEGY)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def safe_api_call(method, endpoint, **kwargs):
    """
    Makes a safe API call to the external timer service.
    Handles network errors, HTTP errors, and JSON parsing.
    Uses the API_SERVICE_URL configured in `app_settings`.
    """
    session_requests = create_session()
    api_url_base = app_settings.get('API_SERVICE_URL')
    if not api_url_base:
        raise Exception("API Service URL is not configured in system settings.")

    url = f"{api_url_base}{endpoint}"

    try:
        with safe_operation(f"API {method.upper()} {endpoint}"):
            kwargs.setdefault('timeout', 10) # Set a default timeout for API requests
            response = session_requests.request(method, url, **kwargs)
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

            try:
                # Attempt to parse JSON response. Some successful API calls might return empty responses.
                if response.text:
                    return response.json()
                else:
                    return {"message": "Operation successful, no content.", "status": "success"}
            except ValueError:
                # If response is not JSON or empty, return it as a success message (e.g., for empty 200 OK)
                return {"message": response.text, "status": "success"}

    except requests.exceptions.Timeout:
        logger.error(f"API timeout for {method} {endpoint}")
        raise Exception("Service timeout - please ensure the timer service is running and accessible.")
    except requests.exceptions.ConnectionError:
        logger.error(f"API connection error for {method} {endpoint}")
        raise Exception("Service unavailable - check if the timer service is running and configured correctly.")
    except requests.exceptions.HTTPError as e:
        logger.error(f"API HTTP error for {method} {endpoint}: {e}")
        status_code = e.response.status_code
        try:
            error_details = e.response.json()
            error_message = error_details.get("message", f"Service error: {status_code}")
        except json.JSONDecodeError:
            error_message = f"Service error: {status_code} - {e.response.text.strip()}"
        raise Exception(error_message)
    except Exception as e:
        logger.error(f"Unexpected API error for {method} {endpoint}: {e}")
        raise Exception("An unexpected internal service error occurred.")

# Constants for file handling and alarm days
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".ogg"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB maximum file size for audio uploads

# Decorators for resilience and error handling across Flask routes.
def handle_exceptions(fallback_return=None):
    """
    Decorator to wrap Flask route functions, providing centralized exception handling,
    heartbeat updates, and error count management. It returns JSON for API errors
    and redirects with flashed messages for UI routes.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                app_state.heartbeat() # Update heartbeat on successful operation
                result = func(*args, **kwargs)
                app_state.reset_errors() # Reset errors if operation was successful
                return result
            except Exception as e:
                logger.error(f"Exception in {func.__name__}: {str(e)}")
                logger.debug(f"Traceback: {traceback.format_exc()}") # Log full traceback for debugging
                app_state.increment_error() # Increment error count

                # Differentiate response based on request path (API vs. HTML route)
                if request.path.startswith('/api/'):
                    return jsonify({"status": "error", "message": str(e)}), 500
                else: # For regular HTML routes (UI interactions)
                    flash(f"An error occurred: {str(e)}", "error")
                    # Redirect based on function name for appropriate user experience
                    if func.__name__ in ['login', 'logout']:
                        return redirect(url_for("login"))
                    # For most other actions, redirect to index to show flash message
                    return redirect(url_for("index"))
        return wrapper
    return decorator

@contextmanager
def safe_operation(operation_name):
    """
    Context manager for wrapping potentially risky operations with logging and error tracking.
    Ensures consistent logging of operation start, completion, and any exceptions.
    """
    logger.debug(f"Starting operation: {operation_name}")
    try:
        yield # Execute the code within the 'with' block
    except Exception as e:
        logger.error(f"Failed operation {operation_name}: {str(e)}")
        app_state.increment_error() # Increment error count on failure
        raise # Re-raise the exception after logging for proper handling up the stack
    finally:
        logger.debug(f"Completed operation: {operation_name}")

def validate_input(data, required_fields):
    """
    Helper function to validate incoming request data.
    Checks if data is a dictionary and if all required fields are present.
    """
    # For form data, request.form is a CombinedMultiDict, not a dict.
    # We should directly check keys in request.form instead of converting to dict for validation.
    if not hasattr(data, 'get'): # Check if it behaves like a dict-like object
        raise ValueError("Invalid input data format. Expected form data or JSON dictionary.")

    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    return True # Return True if validation passes

def allowed_file(filename):
    """Checks if a file's extension is among the allowed audio types."""
    if not filename:
        return False
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

def get_sounds_internal():
    """
    Retrieves a list of available sound files from the static audio directory.
    Includes error handling for file system operations.
    """
    audio_dir = BASE_DIR / "static" / "audio"
    os.makedirs(audio_dir, exist_ok=True) # Ensure the audio directory exists
    sounds = []
    try:
        for f in audio_dir.iterdir():
            if f.is_file() and allowed_file(f.name):
                if os.access(f, os.R_OK): # Check if the file is readable
                    sounds.append(f.name)
                else:
                    logger.warning(f"Sound file not readable and skipped: {f.name}")
    except Exception as e:
        logger.error(f"Error reading sounds directory: {e}")
    return {"sounds": sorted(sounds)} # Return as a dictionary for consistent API-like response

def get_metrics_internal():
    """
    Gathers local system and process metrics (CPU, memory, uptime).
    Uses `psutil` for robust system information retrieval.
    """
    try:
        process = psutil.Process() # Get current process information
        cpu_percent = process.cpu_percent(interval=0.1) # CPU usage percentage
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024) # Resident Set Size in MB
        create_time = process.create_time() # Process creation time
        uptime = datetime.now() - datetime.fromtimestamp(create_time) # Calculate uptime
        uptime_formatted = str(uptime).split(".")[0] # Format uptime for display
        system_memory = psutil.virtual_memory() # System-wide memory usage

        return {
            "process": {
                "cpu_percent": round(cpu_percent, 1),
                "memory_mb": round(memory_mb, 1),
                "uptime": uptime_formatted,
                "threads": process.num_threads()
            },
            "system": {
                "memory_percent": round(system_memory.percent, 1),
                "cpu_count": psutil.cpu_count()
            },
            "app_state": {
                "error_count": app_state.error_count,
                "recovery_mode": app_state.recovery_mode,
                "last_heartbeat": datetime.fromtimestamp(app_state.last_heartbeat).strftime("%H:%M:%S")
            }
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return {"error": "Metrics unavailable. An error occurred while fetching system performance data."}

# --- License Validation and Generation Functions (System-Wide) ---
def generate_license_key():
    """Generates a simple, unique UUID-based license key."""
    return str(uuid.uuid4())

def validate_license(license_key, expiry_date_str):
    """
    Validates a system-wide license key and its expiry date.
    This function is primarily called by superusers to set the overall system license.
    It updates the `app_settings['license']` and persists it.
    Returns (True, message) on success, (False, message) on failure.
    """
    if not license_key or not expiry_date_str:
        return False, "License key and expiry date are required for system license validation."

    try:
        # Basic validation for UUID format of the license key
        uuid.UUID(license_key)
    except ValueError:
        return False, "Invalid license key format. Must be a valid UUID (e.g., xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)."

    try:
        # Attempt to parse expiry date in ISO format, supporting with or without seconds.
        if 'T' not in expiry_date_str:
            return False, "Invalid expiry date format. Must include time with 'T' separator (e.g., 2025-12-31T23:59:59)."
        
        try:
            expiry_date = datetime.fromisoformat(expiry_date_str)
        except ValueError:
            if len(expiry_date_str) == 16: # Handle ISO-MM-DDTHH:MM by adding seconds
                expiry_date_str_with_seconds = f"{expiry_date_str}:00"
                expiry_date = datetime.fromisoformat(expiry_date_str_with_seconds)
            else:
                raise # If still no valid format, re-raise ValueError

        # Ensure the license expiry date is not in the past relative to current time.
        if expiry_date < datetime.now():
            return False, "License expiry date cannot be in the past. Please set a future date."

        # Update the global application settings with the new license information.
        app_settings['license']['key'] = license_key
        app_settings['license']['expiry'] = expiry_date_str # Store the original string format
        app_settings['license']['status'] = 'active' # Set system license status to active
        save_config(app_settings) # Persist the updated configuration
        logger.info(f"System license activated/renewed. Key: {license_key}, Expires: {expiry_date_str}")
        return True, "System license activated successfully!"
    except ValueError as ve:
        return False, f"Invalid expiry date format: {ve}. Use ISO-MM-DDTHH:MM:SS or ISO-MM-DDTHH:MM."
    except Exception as e:
        logger.error(f"Unexpected error during system license validation: {e}")
        return False, f"An internal error occurred during system license validation: {str(e)}"

def check_license_status():
    """
    Checks and updates the current status of the system-wide license.
    This function determines if the license is 'active', 'expired', 'unlicensed', or 'invalid_format'.
    The result is stored in `app_settings['license']['status']`.
    """
    license_info = app_settings['license']
    
    # If no license key is present, the system is unlicensed.
    if not license_info.get('key'):
        license_info['status'] = 'unlicensed'
        return 'unlicensed'

    expiry_str = license_info.get('expiry')
    # If a key exists but no expiry date, the license format is invalid or incomplete.
    if not expiry_str:
        license_info['status'] = 'unlicensed' # Treat as unlicensed if expiry is missing
        return 'unlicensed'

    try:
        # Attempt to parse the stored expiry date string.
        try:
            expiry_date = datetime.fromisoformat(expiry_str)
        except ValueError:
            # If parsing with seconds fails, try adding seconds (for ISO-MM-DDTHH:MM format).
            if len(expiry_str) == 16: # ISO-MM-DDTHH:MM
                expiry_date = datetime.fromisoformat(f"{expiry_str}:00")
            else:
                raise # If still not a valid format, raise the ValueError.

        current_time = datetime.now() # Get the current system time for comparison.

        if current_time < expiry_date:
            license_info['status'] = 'active' # License is currently valid.
            return 'active'
        else:
            license_info['status'] = 'expired' # License has passed its expiry date.
            return 'expired'
    except ValueError:
        license_info['status'] = 'invalid_format' # The expiry date string is malformed.
        logger.error(f"System license expiry date has an invalid format: {expiry_str}")
        return 'invalid_format'
    finally:
        # Note: save_config is not called here to avoid excessive file writes.
        # It should be called after any action that explicitly *changes* license data (e.g., update_license API).
        pass

# Decorator to restrict access to superusers.
# This ensures that only users with the 'superuser' role can access specific routes.
def superuser_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "info")
            return redirect(url_for('login'))
        # Check if the current user has the 'superuser' role.
        if not current_user.is_superuser:
            flash("You do not have sufficient permissions to access this page.", "error")
            return redirect(url_for('index')) # Redirect to dashboard if not authorized
        return f(*args, **kwargs)
    return decorated_function

# Decorator to check if premium features are activated for admin users.
# Superusers bypass this check, as their features are always active.
def features_activated_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Superusers are not subject to individual feature activation checks.
        if current_user.is_authenticated and current_user.is_superuser:
            return f(*args, **kwargs) # Superuser always has access to activated features

        # For 'admin' users, check if their individual features are activated.
        if current_user.is_authenticated and current_user.role == 'admin':
            if not current_user.user_settings.get('features_activated', False):
                flash("Please activate premium features to use this functionality. Your individual license is not active.", "error")
                return redirect(url_for('index'))
        
        # If not authenticated, or any other role that shouldn't access, fall through to login_required or specific redirects
        # (login_required should handle non-authenticated users before this decorator usually)
        return f(*args, **kwargs)
    return decorated_function

# --- Authentication Routes ---
@app.route("/login", methods=["GET", "POST"])
@handle_exceptions()
def login():
    """
    Handles user login. If already authenticated, redirects to the dashboard.
    On POST, attempts to authenticate the user against stored passwords for 'admin' and 'superuser'.
    """
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        password = request.form.get("password")
        if not password:
            # Return JSON for AJAX handling
            return jsonify({"status": "error", "message": "Password is required to log in."}), 400

        users_data = load_users_data() # Load all user data to check credentials
        
        # Attempt to authenticate as 'admin'
        admin_data = users_data.get('admin', {})
        admin_hash = admin_data.get('password_hash', '').encode('utf-8')
        
        # Attempt to authenticate as 'superuser'
        superuser_data = users_data.get('superuser', {})
        superuser_hash = superuser_data.get('password_hash', '').encode('utf-8')

        # Check system license status
        license_status = check_license_status()

        # Check if the user is attempting to log in as an admin
        # and if the system is not licensed.
        if bcrypt.checkpw(password.encode('utf-8'), admin_hash) and license_status in ['expired', 'unlicensed', 'invalid_format']:
            message = "Your system is not licensed. Please contact the superuser to license it."
            logger.warning(f"Admin login attempt blocked due to unlicensed system. Status: {license_status}")
            # Return JSON for AJAX handling
            return jsonify({"status": "error", "message": message}), 403 # Use 403 Forbidden for unauthorized access

        # Proceed with login attempts if not blocked by license for admin
        if admin_hash and bcrypt.checkpw(password.encode('utf-8'), admin_hash):
            user = User("admin", "admin", admin_data.get('user_settings', {}))
            login_user(user, remember=True) # Log in the user, remember their session
            session.permanent = True # Make the session permanent for 24 hours
            logger.info("Admin user logged in successfully.")
            # Return JSON for AJAX handling, indicating success and a redirect URL
            return jsonify({"status": "success", "message": "Logged in successfully as Admin.", "redirect_url": url_for("index")}), 200

        # Superuser login is allowed regardless of license status
        if superuser_hash and bcrypt.checkpw(password.encode('utf-8'), superuser_hash):
            user = User("superuser", "superuser", superuser_data.get('user_settings', {}))
            login_user(user, remember=True)
            session.permanent = True
            logger.info("Superuser logged in successfully.")
            # Return JSON for AJAX handling, indicating success and a redirect URL
            return jsonify({"status": "success", "message": "Logged in successfully as Superuser.", "redirect_url": url_for("index")}), 200

        logger.warning("Invalid login attempt with provided credentials.")
        # Return JSON for AJAX handling
        return jsonify({"status": "error", "message": "Invalid password. Please try again."}), 401 # Use 401 Unauthorized

    return render_template("index.html", is_logged_in=False) # Render login page on GET request

@app.route("/logout", methods=["GET", "POST"])
@login_required # Requires user to be logged in to access
@handle_exceptions()
def logout():
    """Handles user logout, clears the session, and redirects to the login page."""
    try:
        username = current_user.id if current_user.is_authenticated else "unknown"
        logout_user() # Flask-Login function to log out the current user
        session.clear() # Clear all session data for security
        logger.info(f"User {username} logged out successfully.")
        flash("You have been successfully logged out.", "success")
        return redirect(url_for("login"))
    except Exception as e:
        logger.error(f"An error occurred during logout process: {e}")
        flash("Logout completed, but an error occurred during the process.", "info")
        return redirect(url_for("login"))

@app.route("/change_password", methods=["GET", "POST"])
@login_required # Requires user to be logged in
@handle_exceptions()
def change_password():
    """
    Allows a logged-in user to change their password.
    Requires current password verification and new password confirmation.
    """
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not all([current_password, new_password, confirm_password]):
            flash("All password fields are required.", "error")
            return render_template("index.html", is_logged_in=True) # Stay on dashboard with modal open

        if new_password != confirm_password:
            flash("New passwords do not match. Please re-enter.", "error")
            return render_template("index.html", is_logged_in=True)

        if len(new_password) < 8:
            flash("New password must be at least 8 characters long for security.", "error")
            return render_template("index.html", is_logged_in=True)
        
        users_data = load_users_data() # Load all user accounts
        current_user_id = current_user.get_id()
        user_info = users_data.get(current_user_id)

        if not user_info:
            flash("User information not found. Please try logging in again.", "error")
            return redirect(url_for("index"))

        stored_hash = user_info.get('password_hash', '').encode('utf-8')

        # Verify current password against stored hash
        if not stored_hash or not bcrypt.checkpw(current_password.encode('utf-8'), stored_hash):
            flash("Current password is incorrect. Please verify and try again.", "error")
            return render_template("index.html", is_logged_in=True)

        # Hash the new password and update user data
        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user_info['password_hash'] = new_hash
        save_users_data(users_data) # Persist the updated user data
        logger.info(f"Password for user '{current_user_id}' changed successfully.")
        flash("Your password has been changed successfully.", "success")
        return redirect(url_for("index"))

    return render_template("index.html", is_logged_in=True) # Render dashboard for GET request

# --- Flask API Proxy Endpoints for Frontend to consume data from external service ---
@app.route("/api/status", methods=["GET"])
@login_required # Protect this endpoint, requires authentication
@handle_exceptions()
def api_status():
    """Proxies request to the external timer service to get its status."""
    status_data = safe_api_call("GET", "/api/status")
    return jsonify(status_data)

@app.route("/api/alarms", methods=["GET"])
@login_required # Protect this endpoint
@handle_exceptions()
def api_get_alarms():
    """Retrieves configured alarms directly from alarms.json."""
    alarms_data = load_alarms_data()
    logger.info(f"Retrieved {len(alarms_data)} alarms from {ALARMS_FILE}.")
    return jsonify({"alarms": alarms_data})

@app.route("/api/metrics", methods=["GET"])
@login_required # Protect this endpoint
@handle_exceptions()
def api_get_metrics():
    """Endpoint to get local system metrics (CPU, memory, uptime)."""
    # This calls the internal function, not the external API service.
    metrics = get_metrics_internal()
    return jsonify(metrics)

@app.route("/api/sounds", methods=["GET"])
@login_required # Protect this endpoint
@handle_exceptions()
def api_get_sounds():
    """Endpoint to get a list of available sound files for alarms."""
    # This calls the internal function to list local audio files.
    sounds_data = get_sounds_internal()
    return jsonify(sounds_data)

# --- API Endpoints for System Settings (Network, Time, API URL) ---
@app.route("/api/system_settings", methods=["GET"])
@login_required # Requires authentication to view settings
@handle_exceptions()
def get_system_settings():
    """
    Returns the current application settings including network, time, license info,
    and the current user's role and feature activation status.
    """
    check_license_status() # Ensure license status is up-to-date before sending
    # Return a copy to prevent accidental modification of the global app_settings.
    response_data = app_settings.copy()
    response_data['user_role'] = current_user.role if current_user.is_authenticated else 'guest'
    # Include the current user's individual feature activation status for frontend logic.
    response_data['current_user_features_activated'] = current_user.user_settings.get('features_activated', False)
    return jsonify(response_data)

@app.route("/api/system_settings", methods=["POST"])
@login_required # Requires authentication to modify settings
@handle_exceptions()
def apply_system_settings():
    """
    Receives updated system settings from the frontend and applies them.
    This includes API URL, network settings, time settings, and Ubuntu device IP.
    Requires authentication.
    """
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No JSON data provided in the request body.'}), 400

    global app_settings # Access and modify the global app_settings dictionary

    # Process API Service URL configuration.
    new_api_url = data.get('API_SERVICE_URL')
    if new_api_url is not None:
        new_api_url = new_api_url.strip()
        if not new_api_url:
            return jsonify({'status': 'error', 'message': "API Service URL cannot be empty. Please provide a valid URL."}), 400
        if not (new_api_url.startswith("http://") or new_api_url.startswith("https://")):
            return jsonify({'status': 'error', 'message': "API Service URL must start with 'http://' or 'https://'."}), 400
        app_settings['API_SERVICE_URL'] = new_api_url
        logger.info(f"API_SERVICE_URL updated to: {new_api_url}")

    # Determine the target URL for the Ubuntu config service
    # Prioritize environment variable (for Docker internal communication)
    # If not in Docker, use the IP from UI settings.
    ubuntu_config_service_base_url = os.getenv("UBUNTU_CONFIG_SERVICE_URL")
    ubuntu_device_ip_from_ui = data.get('ubuntuDeviceIpAddress')

    if ubuntu_config_service_base_url:
        # If running in Docker, use the internal Docker Compose service URL
        logger.info(f"Using UBUNTU_CONFIG_SERVICE_URL from environment: {ubuntu_config_service_base_url}")
        target_ubuntu_base_url = ubuntu_config_service_base_url
    elif ubuntu_device_ip_from_ui:
        # If not in Docker (or env var not set), use the IP configured in the UI
        # Ensure the IP address is stripped of any leading/trailing whitespace or accidental paths
        clean_ip = ubuntu_device_ip_from_ui.strip().split('/')[0]
        target_ubuntu_base_url = f"http://{clean_ip}:5002"
        app_settings['ubuntuDeviceIpAddress'] = clean_ip # Update app settings for persistence
        logger.info(f"Using Ubuntu Device IP Address from UI: {target_ubuntu_base_url}")
    else:
        # No IP configured, cannot proceed with Ubuntu device calls
        save_config(app_settings) # Save other settings if any
        return jsonify({'status': 'warning', 'message': 'Ubuntu Device IP Address not configured. Settings saved but not applied to device.'})

    # Process Network Settings for Ubuntu Device
    new_network_settings = data.get('networkSettings')
    if new_network_settings:
        app_settings['networkSettings'].update(new_network_settings)
        logger.info(f"Network settings updated in config file: {new_network_settings}")
        
        # --- Send Network Settings to Ubuntu Configuration Service ---
        ubuntu_network_url = f"{target_ubuntu_base_url}/apply_network_settings"
        logger.debug(f"Attempting to send network config to Ubuntu service at URL: {ubuntu_network_url}") # DEBUG LOG
        try:
            # Prepare payload for Ubuntu service
            ubuntu_network_payload = {
                'ipType': new_network_settings.get('ipType'),
                'ipAddress': new_network_settings.get('ipAddress'),
                'subnetMask': new_network_settings.get('subnetMask'),
                'gateway': new_network_settings.get('gateway'),
                'dnsServer': new_network_settings.get('dnsServer')
            }
            
            response = requests.post(ubuntu_network_url, json=ubuntu_network_payload, timeout=10)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            ubuntu_response = response.json()
            logger.info(f"Sent network config to Ubuntu device ({target_ubuntu_base_url}): {ubuntu_response}")
            if ubuntu_response.get('status') == 'error':
                # If Ubuntu service reported an error, propagate it.
                return jsonify({'status': 'error', 'message': f'Failed to apply network settings on Ubuntu device: {ubuntu_response.get("message", "Unknown error")}'}), 500
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send network config to Ubuntu device ({target_ubuntu_base_url}): {e}")
            return jsonify({'status': 'error', 'message': f'Failed to communicate with Ubuntu device for network settings: {e}'}), 500
        
    # Process Time Settings for Ubuntu Device
    new_time_settings = data.get('timeSettings')
    if new_time_settings:
        app_settings['timeSettings'].update(new_time_settings)
        logger.info(f"Time settings updated in config file: {new_time_settings}")

        # --- Send Time Settings to Ubuntu Configuration Service ---
        ubuntu_time_url = f"{target_ubuntu_base_url}/apply_time_settings"
        logger.debug(f"Attempting to send time config to Ubuntu service at URL: {ubuntu_time_url}") # DEBUG LOG
        try:
            # Prepare payload for Ubuntu service
            ubuntu_time_payload = {
                'timeType': new_time_settings.get('timeType'),
                'ntpServer': new_time_settings.get('ntpServer'),
                'manualDate': new_time_settings.get('manualDate'),
                'manualTime': new_time_settings.get('manualTime')
            }
            response = requests.post(ubuntu_time_url, json=ubuntu_time_payload, timeout=10)
            response.raise_for_status()
            ubuntu_response = response.json()
            logger.info(f"Sent time config to Ubuntu device ({target_ubuntu_base_url}): {ubuntu_response}")
            if ubuntu_response.get('status') == 'error':
                # If Ubuntu service reported an error, propagate it.
                return jsonify({'status': 'error', 'message': f'Failed to apply time settings on Ubuntu device: {ubuntu_response.get("message", "Unknown error")}'}), 500
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send time config to Ubuntu device ({target_ubuntu_base_url}): {e}")
            return jsonify({'status': 'error', 'message': f'Failed to communicate with Ubuntu device for time settings: {e}'}), 500

    # Save the updated application settings to the configuration file after all changes are applied.
    save_config(app_settings)
    return jsonify({'status': 'success', 'message': 'System settings saved and applied successfully to Ubuntu device.'})

# --- API Endpoint for System-Wide License Management ---
@app.route('/api/license', methods=['POST'])
@superuser_required # Only a superuser can update the system-wide license.
@handle_exceptions()
def update_license():
    """
    Receives system-wide license key and expiry from frontend, validates it, and applies it.
    This route is restricted to superusers.
    """
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No JSON data provided for license update.'}), 400

    license_key = data.get('licenseKey')
    expiry_date_str = data.get('expiryDate') # Expected ISO-MM-DDTHH:MM:SS or ISO-MM-DDTHH:MM format

    success, message = validate_license(license_key, expiry_date_str) # Perform system-wide license validation
    
    if success:
        # check_license_status() is implicitly called and updates app_settings['license'] within validate_license.
        return jsonify({'status': 'success', 'message': message, 'licenseInfo': app_settings['license']})
    else:
        return jsonify({'status': 'error', 'message': message}), 400

@app.route('/api/generate_license_key', methods=['GET'])
@superuser_required # Only a superuser can generate new license keys.
@handle_exceptions()
def api_generate_license_key():
    """
    Generates a new system-wide license key (UUID) and returns it to the frontend.
    This route is restricted to superusers.
    """
    new_key = generate_license_key()
    return jsonify({'status': 'success', 'licenseKey': new_key})

@app.route('/api/license_status', methods=['GET'])
@handle_exceptions()
def get_license_status_api():
    """
    Returns only the current system-wide license status and info.
    This endpoint can be accessed without full authentication if needed for public display
    (though currently protected by @login_required on the index page that calls it).
    """
    check_license_status() # Update status based on current time
    return jsonify({'licenseInfo': app_settings['license']})

@app.route('/api/licensed_users', methods=['GET'])
@superuser_required # Only a superuser can view the list of individually licensed (activated) users.
@handle_exceptions()
def get_licensed_users_api():
    """
    Returns a list of users who have individually activated premium features.
    This data is stored in the `activated_user_log` within the system's configuration.
    """
    return jsonify({'licensedUsers': app_settings.get('activated_user_log', [])})
@app.route('/api/users', methods=['GET'])
@superuser_required # Only superusers can view the list of users
@handle_exceptions()
def api_get_users():
    """
    Returns a list of all user accounts (username and role).
    Restricted to superusers for security.
    Does NOT return password hashes.
    """
    logger.info(f"Superuser '{current_user.id}' requested list of all users.")
    users_data = load_users_data()
    user_list = []
    for username, user_info in users_data.items():
        user_list.append({
            'username': username,
            'role': user_info.get('role', 'admin') # Default to 'admin' if role is missing
        })
    return jsonify({"users": user_list})

@app.route('/admin/add_user', methods=['POST'])
@superuser_required # Only superusers can add new users
@handle_exceptions()
def admin_add_user():
    """
    Allows a superuser to add a new user account.
    Requires username, password, and role. Hashes the password before saving.
    """
    logger.info(f"Superuser '{current_user.id}' attempting to add a new user.")
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    role = request.form.get('role', 'admin') # Default role to 'admin'

    if not all([username, password, confirm_password, role]):
        flash("All fields (username, password, confirm password, role) are required.", "error")
        return jsonify({"status": "error", "message": "All fields are required"}), 400

    if password != confirm_password:
        flash("Password and confirm password do not match.", "error")
        return jsonify({"status": "error", "message": "Passwords do not match"}), 400

    if len(password) < 8:
        flash("Password must be at least 8 characters long.", "error")
        return jsonify({"status": "error", "message": "Password must be at least 8 characters long"}), 400

    if role not in ['admin', 'superuser']:
        flash("Invalid role specified. Role must be 'admin' or 'superuser'.", "error")
        return jsonify({"status": "error", "message": "Invalid role"}), 400

    users_data = load_users_data()
    if username in users_data:
        flash(f"User '{username}' already exists. Please choose a different username.", "error")
        return jsonify({"status": "error", "message": f"User '{username}' already exists"}), 409 # 409 Conflict

    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        users_data[username] = {
            'password_hash': hashed_password,
            'role': role,
            'user_settings': {'features_activated': False} # New users start with features deactivated
        }
        save_users_data(users_data)
        flash(f"User '{username}' ({role}) added successfully.", "success")
        logger.info(f"Superuser '{current_user.id}' successfully added new user: '{username}' with role '{role}'.")
        return jsonify({"status": "success", "message": f"User '{username}' added successfully"}), 201 # 201 Created
    except Exception as e:
        flash(f"Failed to add user '{username}': {e}", "error")
        logger.error(f"Error adding user '{username}' by superuser '{current_user.id}': {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error during user creation"}), 500

# New endpoint for admin users to activate premium features for their individual account.
@app.route("/activate_features", methods=["POST"])
@login_required # User must be logged in to activate features.
@handle_exceptions()
def activate_features():
    """
    Allows an admin user to activate premium features for their account.
    This operation is only allowed if the overall system license is currently active.
    It updates the user's individual settings and logs the activation.
    """
    # Ensure only 'admin' role can activate features for themselves.
    if current_user.role != 'admin':
        flash("Only Admin users are eligible to activate premium features for their accounts.", "error")
        return redirect(url_for('index'))

    # Check if the overall system license is active.
    license_status = check_license_status()
    if license_status != 'active':
        flash(f"Cannot activate features: The system license is currently '{license_status}'. Please contact the superuser to resolve this.", "error")
        return redirect(url_for('index'))

    users_data = load_users_data() # Load all user accounts from the file.
    user_id = current_user.get_id() # Get the ID of the current logged-in user.
    
    if user_id in users_data:
        # Update the 'features_activated' flag in the current admin user's settings.
        users_data[user_id]['user_settings']['features_activated'] = True
        save_users_data(users_data) # Persist the updated user data.
        
        # Log the activation in the system's activated_user_log.
        log_entry = {'user_id': user_id, 'activated_at': datetime.now().isoformat()}
        
        # Prevent duplicate entries in the log for the same user.
        existing_log_entry_index = -1
        for i, entry in enumerate(app_settings['activated_user_log']):
            if entry.get('user_id') == user_id:
                existing_log_entry_index = i
                break
        
        if existing_log_entry_index != -1:
            app_settings['activated_user_log'][existing_log_entry_index] = log_entry # Update existing log
        else:
            app_settings['activated_user_log'].append(log_entry) # Add new log entry
        
        save_config(app_settings) # Save the updated app settings (including the log).
        
        # Re-load current user's data into session to immediately reflect the 'features_activated' status.
        # This is CRUCIAL for Flask-Login's `current_user` object to be updated.
        login_user(load_user(user_id), remember=True) 
        
        flash("Premium features activated successfully for your account!", "success")
    else:
        flash("Your user account was not found. Please contact support.", "error")

    return redirect(url_for('index'))


# --- Main Application Route Handlers ---
@app.route("/", methods=["GET"])
@login_required # Requires user to be logged in to access the dashboard.
@handle_exceptions()
def index():
    """
    Main index page. Renders the dashboard if authenticated, otherwise redirects to login.
    Performs system-wide license checks and sets flags for frontend display based on user role
    and individual feature activation status.
    """
    # Check the system-wide license status before rendering the dashboard.
    license_status = check_license_status()

    # If the system license is not active (expired, unlicensed, or invalid format)
    # and the current user is NOT a superuser, handle accordingly.
    if license_status in ['expired', 'unlicensed', 'invalid_format'] and not current_user.is_superuser:
        if current_user.role == 'admin':
            # For admin users, show a flash message but do not redirect.
            # The template will be rendered, and the JS will pick up this flash message.
            flash("Your system is not licensed. Please contact the superuser to license it, or enter a license key to activate.", "error")
        else:
            # For other non-superuser roles (e.g., guest if they somehow reach here), redirect to login.
            flash(f"System license is '{license_status}'. Access to features is restricted. Please contact support for licensing.", "error")
            return redirect(url_for("login")) # Redirect to login page

    # Pass current user's role and their individual feature activation status to the template.
    current_user_features_activated = current_user.user_settings.get('features_activated', False)

    return render_template(
        "index.html",
        is_logged_in=current_user.is_authenticated,
        current_user_role=current_user.role,
        current_user_features_activated=current_user_features_activated
    )

@app.route("/set_alarm", methods=["POST"])
@login_required # Requires authentication.
@features_activated_required # Requires individual feature activation for admins, bypassed by superusers.
@handle_exceptions()
def set_alarm():
    """
    Handles setting a new alarm. Requires system-wide active license (unless superuser)
    and individual feature activation (for admins).
    A unique 'id' (UUID) is generated for each new alarm.
    """
    # Additional system-wide license check for non-superusers.
    if not current_user.is_superuser and check_license_status() != 'active':
        flash("Cannot set alarm: System license is not active. Please contact superuser to reactivate.", "error")
        return redirect(url_for("index"))

    # Use request.form as the frontend is sending FormData
    form_data = {
        "id": str(uuid.uuid4()), # Generate a unique UUID for the new alarm
        "day": request.form.get("day"),
        "time": request.form.get("time"),
        "label": request.form.get("label", "Alarm").strip() or "Alarm", # Default label
        "sound": request.form.get("sound")
    }
    validate_input(request.form, ["day", "time", "sound"]) # Validate required fields from request.form

    if form_data["day"] not in DAYS:
        raise ValueError("Invalid day selected. Please choose from Monday to Sunday.")
    try:
        datetime.strptime(form_data["time"], "%H:%M") # Validate time format
    except ValueError:
        raise ValueError("Invalid time format. Please use HH:MM (e.g., 14:30).")
    
    # Load existing alarms, add the new one, and save.
    alarms = load_alarms_data()
    alarms.append(form_data) # Add the new alarm dictionary
    save_alarms_data(alarms) # Save the updated list back to file

    flash("Alarm set successfully.", "success")
    logger.info(f"Alarm set for {form_data['day']} at {form_data['time']} (ID: {form_data['id']}) by {current_user.id}. Total alarms: {len(alarms)}")
    return redirect(url_for("index"))

@app.route("/edit_alarm/<string:alarm_id>", methods=["POST"]) # Changed to use alarm_id
@login_required
@features_activated_required # Requires individual feature activation for admins.
@handle_exceptions()
def edit_alarm(alarm_id): # Function now takes alarm_id
    """
    Handles editing an existing alarm based on its unique ID.
    Requires system-wide active license (unless superuser) and individual feature activation (for admins).
    """
    if not current_user.is_superuser and check_license_status() != 'active':
        flash("Cannot edit alarm: System license is not active. Please contact superuser to reactivate.", "error")
        return redirect(url_for("index"))

    alarms = load_alarms_data() # Load existing alarms
    
    # Find the alarm by its unique ID
    found_alarm_index = -1
    for i, alarm in enumerate(alarms):
        if alarm.get("id") == alarm_id:
            found_alarm_index = i
            break

    if found_alarm_index == -1:
        raise ValueError(f"Alarm with ID '{alarm_id}' not found for editing.")
    
    # Use request.form as the frontend is sending FormData
    form_data = {
        "day": request.form.get("day"),
        "time": request.form.get("time"),
        "label": request.form.get("label", "Alarm").strip() or "Alarm",
        "sound": request.form.get("sound")
    }
    validate_input(request.form, ["day", "time", "sound"]) # Validate required fields from request.form
    
    if form_data["day"] not in DAYS:
        raise ValueError("Invalid day selected. Please choose from Monday to Sunday.")
    try:
        datetime.strptime(form_data["time"], "%H:%M") # Validate time format
    except ValueError:
        raise ValueError("Invalid time format. Please use HH:MM (e.g., 14:30).")

    # Update the alarm at the found index
    # IMPORTANT: Do NOT update the 'id' here, as it should remain immutable.
    alarms[found_alarm_index]['day'] = form_data['day']
    alarms[found_alarm_index]['time'] = form_data['time']
    alarms[found_alarm_index]['label'] = form_data['label']
    alarms[found_alarm_index]['sound'] = form_data['sound']

    save_alarms_data(alarms) # Save the updated list
    flash("Alarm updated successfully.", "success")
    logger.info(f"Alarm ID '{alarm_id}' updated by {current_user.id}.")
    return redirect(url_for("index"))

@app.route("/delete_alarm/<string:alarm_id>", methods=["POST"]) # Changed to use alarm_id
@login_required
@features_activated_required # Requires individual feature activation for admins.
@handle_exceptions()
def delete_alarm(alarm_id): # Function now takes alarm_id
    """
    Handles deleting an alarm based on its unique ID.
    Requires system-wide active license (unless superuser) and individual feature activation (for admins).
    """
    if not current_user.is_superuser and check_license_status() != 'active':
        flash("Cannot delete alarm: System license is not active. Please contact superuser to reactivate.", "error")
        return redirect(url_for("index"))

    alarms = load_alarms_data() # Load existing alarms
    
    # Find the alarm by its unique ID
    found_alarm_index = -1
    for i, alarm in enumerate(alarms):
        if alarm.get("id") == alarm_id:
            found_alarm_index = i
            break

    if found_alarm_index == -1:
        raise ValueError(f"Alarm with ID '{alarm_id}' not found for deletion.")
    
    # Delete the alarm at the found index
    deleted_alarm = alarms.pop(found_alarm_index)
    save_alarms_data(alarms) # Save the updated list

    flash("Alarm deleted successfully.", "success")
    logger.info(f"Alarm {deleted_alarm} (ID: {alarm_id}) deleted by {current_user.id}. Remaining alarms: {len(alarms)}")
    return redirect(url_for("index"))

# --- NEW: RESTful PATCH endpoint for partial alarm updates (if frontend uses JSON) ---
@app.route('/api/alarms/<string:alarm_id>', methods=['PATCH'])
@login_required
@features_activated_required
@handle_exceptions()
def api_update_alarm_patch(alarm_id): # Renamed to avoid clash with form-based edit_alarm
    """
    API endpoint to update an existing alarm by ID using a JSON payload (PATCH).
    Supports partial updates of alarm properties.
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No JSON data received for update."}), 400

    if not current_user.is_superuser and check_license_status() != 'active':
        return jsonify({"status": "error", "message": "Cannot update alarm: System license is not active."}), 403

    alarms = load_alarms_data()
    found_alarm_index = -1
    for i, alarm in enumerate(alarms):
        if alarm.get("id") == alarm_id:
            found_alarm_index = i
            break

    if found_alarm_index == -1:
        return jsonify({"status": "error", "message": "Alarm not found for update."}), 404

    found_alarm = alarms[found_alarm_index]

    for key, value in data.items():
        # Prevent client from changing the ID via PATCH
        if key == 'id':
            logger.warning(f"Attempted to change alarm ID for {alarm_id} via PATCH. Operation denied.")
            continue
        
        if key in found_alarm: # Only update existing keys. Consider allowing new keys for flexibility.
            if key in ['volume', 'duration']:
                try:
                    found_alarm[key] = int(value)
                except (ValueError, TypeError):
                    return jsonify({"status": "error", "message": f"Invalid format for '{key}'. Must be an integer."}), 400
            elif key == 'enabled':
                found_alarm[key] = bool(value)
            elif key == 'days':
                if not isinstance(value, list):
                    return jsonify({"status": "error", "message": "Invalid format for 'days'. Must be a list."}), 400
                found_alarm[key] = value
            else:
                found_alarm[key] = value

    alarms[found_alarm_index] = found_alarm # Update the alarm in the list
    save_alarms_data(alarms)
    
    logger.info(f"User {current_user.id} updated alarm with ID: {alarm_id} via API PATCH. Data: {data}")
    return jsonify({"status": "success", "message": "Alarm updated successfully.", "alarm": found_alarm})

@app.route("/upload", methods=["POST"])
@login_required
@features_activated_required # Requires individual feature activation for admins.
@handle_exceptions()
def upload():
    """
    Handles uploading sound files. Performs comprehensive validation on file type, size, and name.
    Requires system-wide active license (unless superuser) and individual feature activation (for admins).
    """
    if not current_user.is_superuser and check_license_status() != 'active':
        flash("Cannot upload sound: System license is not active. Please contact superuser to reactivate.", "error")
        return redirect(url_for("index"))

    if "file" not in request.files:
        raise ValueError("No file part in the request. Please select a file for upload.")
    
    file = request.files["file"]
    if not file.filename:
        raise ValueError("No file selected for upload. Please choose a file.")
    
    if not allowed_file(file.filename):
        raise ValueError(f"Only audio files with extensions {', '.join(ALLOWED_EXTENSIONS)} are allowed.")
    
    filename = Path(file.filename).name # Get base filename, strip path components.
    if not filename or filename.startswith('.'):
        raise ValueError("Invalid filename provided.")
    
    # Check file size without loading entire file into memory.
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0) # Reset file pointer to beginning after checking size.
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File size exceeds the maximum limit of {MAX_FILE_SIZE / (1024 * 1024):.0f}MB.")
    
    audio_dir = BASE_DIR / "static" / "audio"
    os.makedirs(audio_dir, exist_ok=True) # Ensure target directory exists.
    file_path = audio_dir / filename
    
    if file_path.exists():
        flash(f"File '{filename}' already exists on the server. Please rename and re-upload if you wish to upload a new version.", "warning")
        return redirect(url_for("index"))
    
    with safe_operation(f"Save uploaded file {filename}"):
        file.save(str(file_path)) # Save the file to disk.
    
    if not file_path.exists() or file_path.stat().st_size == 0:
        raise Exception("File upload failed - the file was not saved properly or is empty.")
    
    flash("Sound file uploaded successfully.", "success")
    logger.info(f"Sound file '{filename}' uploaded by {current_user.id}.")
    return redirect(url_for("index"))

@app.route("/delete_song/<filename>", methods=["POST"])
@login_required
@features_activated_required # Requires individual feature activation for admins.
@handle_exceptions()
def delete_song(filename):
    """
    Handles deleting a sound file. Performs path validation to prevent directory traversal attacks.
    Requires system-wide active license (unless superuser) and individual feature activation (for admins).
    """
    if not current_user.is_superuser and check_license_status() != 'active':
        flash("Cannot delete sound: System license is not active. Please contact superuser to reactivate.", "error")
        return redirect(url_for("index"))

    if not filename or '..' in filename or filename.startswith('/'):
        raise ValueError("Invalid filename provided for deletion. Filename cannot contain path traversal characters.")
    
    file_path = BASE_DIR / "static" / "audio" / filename
    
    # Crucial security check: ensure the resolved path is within the intended audio directory.
    try:
        file_path.resolve().relative_to((BASE_DIR / "static" / "audio").resolve())
    except ValueError:
        raise ValueError("Invalid file path. Attempted to access a file outside the designated audio directory.")
    
    if not file_path.exists():
        raise ValueError("Sound file not found on the server, cannot delete.")
    
    with safe_operation(f"Delete file {filename}"):
        file_path.unlink() # Delete the file from the filesystem.
    
    flash("Sound file deleted successfully.", "success")
    logger.info(f"Sound file '{filename}' deleted by {current_user.id}.")
    return redirect(url_for("index"))

@app.route("/test_sound", methods=["POST"])
@login_required
@features_activated_required # Requires individual feature activation for admins.
@handle_exceptions()
def test_sound():
    """
    Endpoint to prepare a sound for client-side testing.
    This action is allowed even if the system license is inactive, but a warning is issued.
    """
    if not current_user.is_superuser and check_license_status() != 'active':
        flash("System license is not active. Sound test may not function as expected or be limited.", "warning")

    sound = request.form.get("sound")
    if not sound:
        raise ValueError("No sound file selected for testing.")
    
    sound_path = BASE_DIR / "static" / "audio" / sound
    if not sound_path.exists():
        raise ValueError("The selected sound file was not found on the server.")
    
    # Prepare response for client-side JavaScript to play the sound.
    response = {
        "status": "success",
        "sound": sound,
        "url": f"/static/audio/{sound}", # URL for client-side audio playback.
        "message": "Sound test ready. Your browser should play the sound."
    }
    
    # If it's an AJAX request, return JSON directly. Otherwise, use Flask's flash message.
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        logger.info(f"Sound '{sound}' test initiated via AJAX by {current_user.id}.")
        return jsonify(response)
    
    session['test_sound'] = sound # Store sound in session if not AJAX, for potential redirect use.
    flash("Sound test ready - click play button on the frontend if not auto-played.", "success")
    logger.info(f"Sound '{sound}' test initiated via form submission by {current_user.id}.")
    return redirect(url_for("index"))

@app.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint for monitoring application status.
    Returns JSON indicating health status, timestamp, error count, and uptime.
    """
    return jsonify({
        "status": "healthy" if not app_state.recovery_mode else "recovery",
        "timestamp": datetime.now().isoformat(),
        "error_count": app_state.error_count,
        "uptime": get_metrics_internal().get("process", {}).get("uptime", "unknown")
    })

# --- Error Handlers ---
@app.errorhandler(404)
def not_found(error):
    """Custom error handler for 404 Not Found errors."""
    logger.warning(f"404 Not Found error encountered at: {request.url}")
    flash("The requested page could not be found.", "error")
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    return redirect(url_for("index"))

@app.errorhandler(500)
def internal_error(error):
    """Custom error handler for 500 Internal Server Errors."""
    logger.error(f"500 Internal Server Error: {error}", exc_info=True) # Log full traceback
    app_state.increment_error()
    flash("An internal server error occurred. Please try again later.", "error")
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    return redirect(url_for("index"))

@app.errorhandler(413)
def file_too_large(error):
    """Custom error handler for 413 Payload Too Large (e.g., file upload exceeding limit)."""
    flash(f"The uploaded file is too large. Maximum allowed size is {MAX_FILE_SIZE / (1024 * 1024):.0f}MB.", "error")
    return redirect(url_for("index"))

# --- Signal Handlers for Graceful Shutdown ---
def signal_handler(signum, frame):
    """
    Handles system signals (like SIGINT, SIGTERM) for graceful application shutdown.
    Sets a flag to inform other threads to stop.
    """
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    app_state.shutdown_requested = True
    sys.exit(0) # Exit the application process

# Register signal handlers.
signal.signal(signal.SIGINT, signal_handler) # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler) # Kill command

# --- Watchdog Thread for Application Monitoring ---
def watchdog():
    """
    A separate thread that periodically monitors the application's health.
    Checks for heartbeats and error counts to detect unresponsiveness or critical issues.
    """
    while not app_state.shutdown_requested:
        try:
            time.sleep(30) # Check every 30 seconds
            # If no heartbeat has been registered for 5 minutes, log a warning and increment error count.
            if time.time() - app_state.last_heartbeat > 300:
                logger.warning("No application heartbeat detected for 5 minutes. Possible unresponsiveness.")
                app_state.increment_error()
            
            # If errors have occurred but the application has been stable for a minute, reset errors.
            if app_state.error_count > 0 and (time.time() - app_state.last_heartbeat < 60): # Corrected to use app_state
                app_state.reset_errors()
                logger.info("Error count reset - application appears stable and responsive.")
        except Exception as e:
            logger.error(f"Watchdog thread encountered an error: {e}")

# --- Startup Validation and Initialization ---
def startup_checks():
    """
    Performs critical checks and initializations required before the Flask application starts.
    This includes directory creation, loading users, loading configuration, and API connectivity tests.
    """
    logger.info("Performing application startup checks and initializations...")
    
    # Ensure necessary directories exist.
    required_dirs = [LOG_DIR, BASE_DIR / "static" / "audio"]
    for directory in required_dirs:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")
    
    # Load users data first. This is crucial as it initializes default users if they don't exist,
    # ensuring 'superuser' and 'admin' accounts are ready.
    load_users_data() 
    
    # Load application settings. This also triggers the initial check of the system-wide license status.
    load_config() 
    
    # Test connectivity to the currently configured external API URL to ensure the backend service is reachable.
    try:
        safe_api_call("GET", "/api/status") # Make a simple status request.
        logger.info(f"API connectivity confirmed to the configured service URL: {app_settings['API_SERVICE_URL']}")
    except Exception as e:
        logger.warning(f"External API service not available at startup on {app_settings['API_SERVICE_URL']}: {e}. "
                       "Some features might be limited until connectivity is restored.")
    
    # Start the watchdog thread to continuously monitor application health.
    watchdog_thread = threading.Thread(target=watchdog, daemon=True)
    watchdog_thread.start()
    logger.info("Watchdog thread successfully started in the background.")

if __name__ == "__main__":
    try:
        startup_checks() # Run all necessary startup checks.
        logger.info("Attempting to start Flask web server...")
        print("--- Flask app.run() is about to be called ---") # Console print for clarity during startup.
        
        # Start the Flask development server.
        # host="0.0.0.0" makes it accessible from any IP (important in containers/VMs).
        # debug=False and use_reloader=False for production readiness.
        app.run(
            host="0.0.0.0",
            port=5000,
            debug=False, # Set to True for development for automatic code reloading and debugger.
            threaded=True, # Enables handling multiple requests concurrently.
            use_reloader=False, # Set to False for production; avoids double-loading in development.
            use_debugger=False # Set to False for production; prevents interactive debugger.
        )
        
        # This line will only be reached if app.run() exits cleanly (e.g., on graceful shutdown).
        print("--- Flask app.run() has finished (this should typically only print on graceful shutdown) ---\n") # Added newline for clarity.
        logger.info("Flask web server has gracefully shut down.")
    except Exception as e:
        # Log a critical error with full traceback if the Flask server fails to start or crashes unexpectedly.
        logger.critical(f"FATAL: Flask web server failed to start or crashed unexpectedly: {e}", exc_info=True)
        sys.exit(1) # Exit with a non-zero status code to indicate failure.
