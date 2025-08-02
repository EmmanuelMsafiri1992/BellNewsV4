# main.py for ESP32 MicroPython
# This script runs on the ESP32 to manage Wi-Fi, NTP time, and expose an HTTP API.

import network
import machine
import time
import ujson
import ntptime
from microdot import Microdot, Response
import gc

# --- Configuration File Path ---
CONFIG_FILE = 'config.json'

# --- Default Settings ---
# These defaults are used if no config.json is found or is corrupted.
DEFAULT_CONFIG = {
    'network': {
        'ipType': 'dynamic',
        'ssid': 'YOUR_WIFI_SSID',  # !!! IMPORTANT: CHANGE THIS TO YOUR WIFI SSID
        'password': 'YOUR_WIFI_PASSWORD', # !!! IMPORTANT: CHANGE THIS TO YOUR WIFI PASSWORD
        'ipAddress': '',
        'subnetMask': '',
        'gateway': '',
        'dnsServer': ''
    },
    'time': {
        'timeType': 'ntp',
        'ntpServer': 'pool.ntp.org',
        'manualDate': '',
        'manualTime': ''
    }
}

# --- Global Variables ---
app = Microdot()
current_config = {}
wlan = network.WLAN(network.STA_IF)

# --- Logging (Basic for MicroPython) ---
def log_message(level, message):
    """Simple logging function for MicroPython."""
    print(f"[{time.time()}] [{level.upper()}] {message}")

# --- Configuration Management ---
def load_config():
    """Loads configuration from CONFIG_FILE, or returns default if not found/invalid."""
    global current_config
    try:
        with open(CONFIG_FILE, 'r') as f:
            loaded = ujson.load(f)
            # Simple deep merge to ensure all default keys are present
            config = DEFAULT_CONFIG.copy()
            for key, value in DEFAULT_CONFIG.items():
                if key in loaded and isinstance(value, dict) and isinstance(loaded[key], dict):
                    config[key].update(loaded[key])
                elif key in loaded:
                    config[key] = loaded[key]
            current_config = config
            log_message("info", f"Configuration loaded from {CONFIG_FILE}")
    except (OSError, ValueError) as e:
        log_message("warning", f"Failed to load config from {CONFIG_FILE}: {e}. Using default config.")
        current_config = DEFAULT_CONFIG.copy()
    return current_config

def save_config(config_data):
    """Saves the current configuration to CONFIG_FILE."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            ujson.dump(config_data, f)
        log_message("info", f"Configuration saved to {CONFIG_FILE}")
        return True
    except OSError as e:
        log_message("error", f"Failed to save config to {CONFIG_FILE}: {e}")
        return False

# --- Wi-Fi Management ---
def connect_wifi(config):
    """Connects to Wi-Fi based on the provided configuration."""
    log_message("info", "Connecting to Wi-Fi...")
    wlan.active(True)
    wlan.disconnect() # Ensure a clean start

    ssid = config['network']['ssid']
    password = config['network']['password']
    ip_type = config['network']['ipType']

    if ip_type == 'static':
        ip = config['network']['ipAddress']
        subnet = config['network']['subnetMask']
        gateway = config['network']['gateway']
        dns = config['network']['dnsServer'] if config['network']['dnsServer'] else '8.8.8.8' # Fallback DNS
        
        if not all([ip, subnet, gateway]):
            log_message("error", "Static IP configuration incomplete (IP, Subnet, Gateway required). Falling back to dynamic.")
            wlan.ifconfig('dhcp') # Fallback to DHCP if static config is bad
        else:
            try:
                wlan.ifconfig((ip, subnet, gateway, dns))
                log_message("info", f"Attempting static IP: {ip}, Subnet: {subnet}, Gateway: {gateway}, DNS: {dns}")
            except Exception as e:
                log_message("error", f"Error setting static IP configuration: {e}. Falling back to dynamic.")
                wlan.ifconfig('dhcp') # Fallback to DHCP if setting static fails
    else:
        wlan.ifconfig('dhcp')
        log_message("info", "Attempting dynamic IP (DHCP)")

    wlan.connect(ssid, password)

    max_attempts = 20 # ~10 seconds with time.sleep(0.5)
    for i in range(max_attempts):
        if wlan.isconnected():
            ip_info = wlan.ifconfig()
            log_message("info", f"Wi-Fi connected! Active IP: {ip_info[0]}, Subnet: {ip_info[1]}, Gateway: {ip_info[2]}, DNS: {ip_info[3]}")
            return True
        log_message("info", f"Waiting for Wi-Fi... ({i+1}/{max_attempts}) - Current status: {wlan.status()}")
        time.sleep(0.5)
    
    log_message("error", f"Wi-Fi connection failed! Final status: {wlan.status()}")
    wlan.active(False)
    return False

# --- Time Synchronization ---
def sync_time(config):
    """Synchronizes ESP32 time using NTP or sets manually."""
    if not wlan.isconnected():
        log_message("warning", "Cannot sync time: Wi-Fi not connected.")
        return False

    time_type = config['time']['timeType']

    if time_type == 'ntp':
        ntp_server = config['time']['ntpServer'] if config['time']['ntpServer'] else 'pool.ntp.org'
        try:
            log_message("info", f"Synchronizing time with NTP server: {ntp_server}")
            ntptime.host = ntp_server
            ntptime.settime()
            log_message("info", f"Time synchronized: {time.localtime()}")
            return True
        except Exception as e:
            log_message("error", f"NTP time sync failed: {e}")
            return False
    else: # Manual time
        manual_date = config['time']['manualDate']
        manual_time = config['time']['manualTime']
        
        if not manual_date or not manual_time:
            log_message("warning", "Manual date or time missing. Cannot set time.")
            return False

        try:
            # Parse date and time strings
            year, month, day = map(int, manual_date.split('-'))
            hour, minute = map(int, manual_time.split(':'))
            
            rtc = machine.RTC()
            # (year, month, day, weekday, hour, minute, second, microsecond)
            # We'll set weekday to 0 (Monday) and microsecond to 0.
            # The actual weekday will be calculated by the RTC based on the date.
            
            rtc.datetime((year, month, day, 0, hour, minute, 0, 0))
            log_message("info", f"Time manually set to: {manual_date} {manual_time}")
            log_message("info", f"Current RTC time: {rtc.datetime()}")
            return True
        except Exception as e:
            log_message("error", f"Manual time set failed: {e}")
            return False

# --- HTTP API Endpoints ---

@app.route('/api/network_config', methods=['POST'])
async def api_network_config(request):
    """API endpoint to receive and apply network configuration."""
    global current_config
    gc.collect() # Force garbage collection before processing request

    try:
        data = request.json
        if not data:
            return Response('{"message": "No JSON data provided"}', status_code=400, headers={'Content-Type': 'application/json'})

        log_message("info", f"Received network config: {data}")

        # Validate and update network settings in current_config
        if 'ipType' in data and data['ipType'] in ['dynamic', 'static']:
            current_config['network']['ipType'] = data['ipType']
        if 'ssid' in data:
            current_config['network']['ssid'] = data['ssid']
        if 'password' in data:
            current_config['network']['password'] = data['password']
        if 'ipAddress' in data:
            current_config['network']['ipAddress'] = data['ipAddress']
        if 'subnetMask' in data:
            current_config['network']['subnetMask'] = data['subnetMask']
        if 'gateway' in data:
            current_config['network']['gateway'] = data['gateway']
        if 'dnsServer' in data:
            current_config['network']['dnsServer'] = data['dnsServer']

        if save_config(current_config):
            log_message("info", "Network config saved. Rebooting to apply changes.")
            # Reboot is necessary for network changes to take full effect
            machine.reset() # This will restart the ESP32 and run main.py again
            return Response('{"message": "Network configuration saved. Device rebooting to apply changes."}', status_code=200, headers={'Content-Type': 'application/json'})
        else:
            return Response('{"message": "Failed to save network configuration."}', status_code=500, headers={'Content-Type': 'application/json'})

    except Exception as e:
        log_message("error", f"Error in network_config API: {e}")
        return Response(ujson.dumps({"message": f"Internal server error: {e}"}), status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/time_config', methods=['POST'])
async def api_time_config(request):
    """API endpoint to receive and apply time configuration."""
    global current_config
    gc.collect()

    try:
        data = request.json
        if not data:
            return Response('{"message": "No JSON data provided"}', status_code=400, headers={'Content-Type': 'application/json'})

        log_message("info", f"Received time config: {data}")

        # Validate and update time settings in current_config
        if 'timeType' in data and data['timeType'] in ['ntp', 'manual']:
            current_config['time']['timeType'] = data['timeType']
        if 'ntpServer' in data:
            current_config['time']['ntpServer'] = data['ntpServer']
        if 'manualDate' in data:
            current_config['time']['manualDate'] = data['manualDate']
        if 'manualTime' in data:
            current_config['time']['manualTime'] = data['manualTime']

        if save_config(current_config):
            # Attempt to apply time immediately, but also saved for reboot persistence
            if sync_time(current_config):
                return Response('{"message": "Time configuration saved and applied successfully."}', status_code=200, headers={'Content-Type': 'application/json'})
            else:
                return Response('{"message": "Time configuration saved, but failed to apply immediately. Will try on next boot."}', status_code=200, headers={'Content-Type': 'application/json'})
        else:
            return Response('{"message": "Failed to save time configuration."}', status_code=500, headers={'Content-Type': 'application/json'})

    except Exception as e:
        log_message("error", f"Error in time_config API: {e}")
        return Response(ujson.dumps({"message": f"Internal server error: {e}"}), status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/status', methods=['GET'])
async def api_status(request):
    """API endpoint to get current ESP32 status (Wi-Fi, IP, Time)."""
    gc.collect()
    try:
        status_data = {
            'wifi_connected': wlan.isconnected(),
            'ip_address': wlan.ifconfig()[0] if wlan.isconnected() else 'N/A',
            'current_time_tuple': time.localtime(),
            'current_config': current_config,
            'heap_free_bytes': gc.mem_free(),
            'heap_alloc_bytes': gc.mem_alloc()
        }
        return Response(ujson.dumps(status_data), status_code=200, headers={'Content-Type': 'application/json'})
    except Exception as e:
        log_message("error", f"Error in status API: {e}")
        return Response(ujson.dumps({"message": f"Internal server error: {e}"}), status_code=500, headers={'Content-Type': 'application/json'})

@app.route('/api/current_network_config', methods=['GET'])
async def api_current_network_config(request):
    """API endpoint to get the currently active network configuration of the ESP32."""
    gc.collect()
    try:
        ip_info = wlan.ifconfig()
        active_network_config = {
            'ipType': current_config['network']['ipType'], # This is what we *tried* to set
            'ssid': current_config['network']['ssid'],
            'active_ip_address': ip_info[0] if wlan.isconnected() else 'N/A',
            'active_subnet_mask': ip_info[1] if wlan.isconnected() else 'N/A',
            'active_gateway': ip_info[2] if wlan.isconnected() else 'N/A',
            'active_dns_server': ip_info[3] if wlan.isconnected() else 'N/A',
            'wifi_connected': wlan.isconnected(),
            'wlan_status': wlan.status() # Raw WLAN status code
        }
        return Response(ujson.dumps(active_network_config), status_code=200, headers={'Content-Type': 'application/json'})
    except Exception as e:
        log_message("error", f"Error in current_network_config API: {e}")
        return Response(ujson.dumps({"message": f"Internal server error: {e}"}), status_code=500, headers={'Content-Type': 'application/json'})


# --- Main Application Logic ---
if __name__ == '__main__':
    log_message("info", "ESP32 Timer MicroPython Firmware starting...")
    
    # Load configuration on startup
    load_config()

    # Attempt to connect to Wi-Fi using the loaded configuration
    if connect_wifi(current_config):
        # If Wi-Fi connects, try to synchronize time
        sync_time(current_config)
    else:
        log_message("error", "Failed to connect to Wi-Fi on startup. API may not be reachable.")

    # Start the Microdot web server
    try:
        log_message("info", "Starting Microdot web server on 0.0.0.0:80")
        app.run(host='0.0.0.0', port=80, debug=True) # debug=True for development, set to False for production
    except Exception as e:
        log_message("critical", f"Failed to start Microdot server: {e}")
        # In a real scenario, you might want to retry or enter a low-power mode
        # For now, just log and let the script potentially exit or hang.
    finally:
        log_message("info", "ESP32 MicroPython Firmware stopped.")

