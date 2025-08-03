# config_service_client.py
# Enhanced client for bellapp integration

import os
import socket
import subprocess
import requests
import logging
import time
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class DynamicConfigServiceClient:
    def __init__(self):
        self.port = int(os.getenv('CONFIG_SERVICE_PORT', '5002'))
        self.auto_detect = os.getenv('AUTO_DETECT_CONFIG_SERVICE', 'true').lower() == 'true'
        self._current_url = None
        self._last_ip_check = 0
        self._ip_cache_duration = 30  # seconds
        
    def _detect_host_ips(self) -> List[str]:
        """Detect all possible host IP addresses to try"""
        ips = []
        
        # Method 1: Try host.docker.internal (works in newer Docker)
        try:
            ip = socket.gethostbyname('host.docker.internal')
            ips.append(ip)
            logger.debug(f"Found host.docker.internal: {ip}")
        except:
            pass
        
        # Method 2: Try to get host IP from container's default gateway
        try:
            result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Parse: default via 172.17.0.1 dev eth0
                parts = result.stdout.split()
                if 'via' in parts:
                    gateway_ip = parts[parts.index('via') + 1]
                    ips.append(gateway_ip)
                    logger.debug(f"Found gateway IP: {gateway_ip}")
        except:
            pass
        
        # Method 3: Try common Docker gateway IPs
        common_gateways = ['172.17.0.1', '172.18.0.1', '172.19.0.1', '172.20.0.1']
        ips.extend(common_gateways)
        
        # Method 4: Try to detect from /proc/net/route
        try:
            with open('/proc/net/route', 'r') as f:
                for line in f:
                    fields = line.strip().split('\t')
                    if len(fields) >= 3 and fields[1] == '00000000':  # Default route
                        gateway_hex = fields[2]
                        # Convert hex to IP
                        gateway_ip = socket.inet_ntoa(bytes.fromhex(gateway_hex)[::-1])
                        ips.append(gateway_ip)
                        logger.debug(f"Found gateway from route table: {gateway_ip}")
                        break
        except:
            pass
        
        # Method 5: Environment variable fallback
        env_host = os.getenv('CONFIG_SERVICE_HOST')
        if env_host:
            ips.append(env_host)
        
        # Add localhost as final fallback
        ips.extend(['localhost', '127.0.0.1'])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_ips = []
        for ip in ips:
            if ip not in seen:
                seen.add(ip)
                unique_ips.append(ip)
        
        logger.info(f"Will try IPs in order: {unique_ips}")
        return unique_ips
    
    def _test_connection(self, ip: str) -> bool:
        """Test if config service is reachable at given IP"""
        url = f"http://{ip}:{self.port}"
        try:
            response = requests.get(f"{url}/health", timeout=3)
            if response.status_code == 200:
                logger.info(f"Config service responding at {url}")
                return True
        except:
            pass
        
        # Try root endpoint if /health doesn't exist
        try:
            response = requests.get(url, timeout=3)
            # Accept any response (even 404) as long as we can connect
            logger.info(f"Config service reachable at {url} (status: {response.status_code})")
            return True
        except Exception as e:
            logger.debug(f"Connection failed to {url}: {e}")
            return False
    
    def _refresh_connection(self) -> str:
        """Find and return the current working config service URL"""
        current_time = time.time()
        
        # Use cached result if recent
        if (self._current_url and 
            current_time - self._last_ip_check < self._ip_cache_duration):
            return self._current_url
        
        if not self.auto_detect:
            # Use hardcoded localhost if auto-detect is disabled
            url = f"http://localhost:{self.port}"
            if self._test_connection("localhost"):
                self._current_url = url
                self._last_ip_check = current_time
                return url
            else:
                logger.error("Config service not reachable at localhost and auto-detect is disabled")
                return url  # Return anyway, let caller handle the error
        
        # Auto-detect mode
        possible_ips = self._detect_host_ips()
        
        for ip in possible_ips:
            if self._test_connection(ip):
                self._current_url = f"http://{ip}:{self.port}"
                self._last_ip_check = current_time
                logger.info(f"Config service found at: {self._current_url}")
                return self._current_url
        
        # Fallback to localhost if nothing worked
        fallback_url = f"http://localhost:{self.port}"
        logger.warning(f"No working config service found, using fallback: {fallback_url}")
        self._current_url = fallback_url
        self._last_ip_check = current_time
        return fallback_url
    
    @property
    def base_url(self) -> str:
        """Get current config service base URL"""
        return self._refresh_connection()
    
    def apply_network_settings(self, settings: Dict) -> bool:
        """Apply network settings through config service"""
        url = f"{self.base_url}/apply_network_settings"
        
        try:
            logger.info(f"Applying network settings to {url}")
            logger.debug(f"Settings: {settings}")
            
            response = requests.post(url, json=settings, timeout=30)
            
            if response.status_code == 200:
                logger.info("Network settings applied successfully")
                return True
            else:
                logger.error(f"Failed to apply settings: HTTP {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            logger.warning("Connection failed, refreshing and retrying...")
            # Force refresh connection and retry once
            self._current_url = None
            self._last_ip_check = 0
            
            try:
                url = f"{self.base_url}/apply_network_settings"
                response = requests.post(url, json=settings, timeout=30)
                
                if response.status_code == 200:
                    logger.info("Network settings applied successfully (after retry)")
                    return True
                else:
                    logger.error(f"Retry failed: HTTP {response.status_code}")
                    return False
                    
            except Exception as e:
                logger.error(f"Retry also failed: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error applying network settings: {e}")
            return False
    
    def get_current_network_settings(self) -> Optional[Dict]:
        """Get current network configuration from config service"""
        url = f"{self.base_url}/get_network_settings"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get current settings: HTTP {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting current network settings: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test if config service is currently reachable"""
        try:
            url = self.base_url  # This will trigger connection refresh
            response = requests.get(url, timeout=5)
            return True
        except:
            return False


# Initialize global client instance
config_client = DynamicConfigServiceClient()

# Convenience functions for use in your Flask app
def change_network_to_static(ip_address: str, netmask: str, gateway: str, 
                           dns_servers: List[str] = None) -> bool:
    """Change network configuration to static IP"""
    if dns_servers is None:
        dns_servers = ["8.8.8.8", "8.8.4.4"]
    
    settings = {
        "mode": "static",
        "ip_address": ip_address,
        "netmask": netmask,
        "gateway": gateway,
        "dns_servers": dns_servers
    }
    
    return config_client.apply_network_settings(settings)

def change_network_to_dhcp() -> bool:
    """Change network configuration to DHCP"""
    settings = {
        "mode": "dhcp"
    }
    
    return config_client.apply_network_settings(settings)

def get_current_ip() -> Optional[str]:
    """Get current IP address from config service"""
    settings = config_client.get_current_network_settings()
    if settings:
        return settings.get('current_ip')
    return None

def is_config_service_available() -> bool:
    """Check if config service is currently reachable"""
    return config_client.test_connection()


# Example usage in Flask route
def example_flask_route():
    """Example of how to use in your Flask app"""
    from flask import request, jsonify
    
    @app.route('/change_network', methods=['POST'])
    def change_network():
        data = request.get_json()
        
        if data.get('mode') == 'static':
            success = change_network_to_static(
                ip_address=data['ip_address'],
                netmask=data.get('netmask', '255.255.255.0'),
                gateway=data['gateway'],
                dns_servers=data.get('dns_servers', ["8.8.8.8", "8.8.4.4"])
            )
        elif data.get('mode') == 'dhcp':
            success = change_network_to_dhcp()
        else:
            return jsonify({"error": "Invalid mode"}), 400
        
        if success:
            return jsonify({"message": "Network settings applied successfully"})
        else:
            return jsonify({"error": "Failed to apply network settings"}), 500
    
    @app.route('/current_network', methods=['GET'])
    def get_current_network():
        settings = config_client.get_current_network_settings()
        if settings:
            return jsonify(settings)
        else:
            return jsonify({"error": "Could not retrieve network settings"}), 500
    
    @app.route('/config_service_status', methods=['GET'])
    def config_service_status():
        available = is_config_service_available()
        return jsonify({
            "available": available,
            "url": config_client.base_url if available else None
        })


if __name__ == "__main__":
    # Test the client
    logging.basicConfig(level=logging.INFO)
    
    print(f"Config service URL: {config_client.base_url}")
    print(f"Connection test: {config_client.test_connection()}")
    
    # Example: Get current settings
    current = config_client.get_current_network_settings()
    if current:
        print(f"Current settings: {current}")
    
    # Example: Change to static IP
    # success = change_network_to_static("192.168.33.200", "255.255.255.0", "192.168.33.1")
    # print(f"Static IP change: {success}")