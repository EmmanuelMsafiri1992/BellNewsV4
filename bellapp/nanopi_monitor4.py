#!/usr/bin/env python3
"""
NanoPi NEO OLED System Monitor with Time-Based Alarms
"""
import os
import sys
import time
import json
import threading
import subprocess
from datetime import datetime, timezone
import signal
import logging
from pathlib import Path

# Pygame import with error handling
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not available, sound playback disabled")

# Existing imports
try:
    from luma.core.interface.serial import i2c
    from luma.core.render import canvas
    from luma.oled.device import ssd1306
    from PIL import Image, ImageDraw, ImageFont
    LUMA_AVAILABLE = True
except ImportError as e:
    print(f"Warning: OLED display modules not available: {e}")
    LUMA_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    print("Warning: psutil not available, system monitoring disabled")
    PSUTIL_AVAILABLE = False

try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    print("Warning: pytz not available, using basic timezone support")
    PYTZ_AVAILABLE = False

# GPIO imports
GPIO_AVAILABLE = False
GPIO = None
try:
    import OPi.GPIO as GPIO
    GPIO_AVAILABLE = True
    GPIO_TYPE = "OPi"
    print("✓ Using OPi.GPIO")
except (ImportError, RuntimeError):
    try:
        import RPi.GPIO as GPIO
        GPIO_AVAILABLE = True
        GPIO_TYPE = "RPi"
        print("✓ Using RPi.GPIO")
    except (ImportError, RuntimeError):
        print("Warning: No GPIO library available, button functionality disabled")

# Mock classes
class MockDevice:
    def __init__(self): pass
    def contrast(self, value): pass
    def cleanup(self): pass

class MockCanvas:
    def __init__(self, device): self.device = device
    def __enter__(self): return MockDraw()
    def __exit__(self, *args): pass

class MockDraw:
    def text(self, position, text, fill="white"): print(f"Display: {text}")

def mock_canvas(device): return MockCanvas(device)

class NanoPiOLEDMonitor:
    def __init__(self):
        self.config_file = Path.home() / '.nanopi_monitor_config.json'
        self.log_file = Path.home() / '.nanopi_monitor.log'
        self.sound_dir = Path.home() / '.nanopi_sounds'
        self.sound_dir.mkdir(exist_ok=True)

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.config = self.load_config()
        self.alarms = self.config.get('alarms', {
            'temperature': 70.0, 'cpu': 90.0, 'memory': 90.0, 'disk': 90.0
        })
        self.time_alarms = self.config.get('time_alarms', [])

        # Display modes
        self.display_modes = ['datetime', 'system_info', 'network_info', 'temperature']
        self.current_mode = 0

        # GPIO setup
        self.button_pins = [6, 1, 67]
        self.gpio_initialized = False
        if GPIO_AVAILABLE:
            self.setup_gpio()

        # OLED setup
        self.setup_display()

        # Time zone
        try:
            if PYTZ_AVAILABLE:
                self.timezone = pytz.timezone(self.config.get('timezone', 'Africa/Johannesburg'))
            else:
                self.timezone = timezone.utc
        except:
            self.timezone = pytz.UTC if PYTZ_AVAILABLE else timezone.utc

        # Threading
        self.running = True
        self.display_lock = threading.Lock()

        # NTP sync
        self.last_ntp_sync = 0
        self.ntp_sync_interval = 3600

        # Initialize pygame mixer
        global PYGAME_AVAILABLE
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
                self.logger.info("Pygame mixer initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize pygame mixer: {e}")
                PYGAME_AVAILABLE = False

        self.logger.info("NanoPi OLED Monitor initialized")

    def load_config(self):
        """Load configuration from file"""
        default_config = {
            'timezone': 'Africa/Johannesburg',
            'display_brightness': 255,
            'auto_brightness': True,
            'ntp_servers': ['pool.ntp.org', 'time.google.com'],
            'display_timeout': 0,
            'refresh_rate': 1.0,
            'mock_mode': not LUMA_AVAILABLE,
            'alarms': {
                'temperature': 70.0, 'cpu': 90.0, 'memory': 90.0, 'disk': 90.0
            },
            'time_alarms': []
        }
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    default_config.update(config)
            except Exception as e:
                self.logger.warning(f"Could not load config: {e}")
        return default_config

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save config: {e}")

    def play_sound(self, sound_file):
        """Play the specified sound file"""
        if not PYGAME_AVAILABLE:
            self.logger.warning("pygame not available or not initialized, cannot play sound")
            return
        sound_path = self.sound_dir / sound_file
        if sound_path.exists():
            try:
                pygame.mixer.music.load(str(sound_path))
                pygame.mixer.music.play()
                self.logger.info(f"Playing sound: {sound_file}")
            except Exception as e:
                self.logger.error(f"Error playing sound {sound_file}: {e}")
        else:
            self.logger.warning(f"Sound file not found: {sound_file}")

    def check_time_alarms(self):
        """Check and trigger time-based alarms"""
        while self.running:
            try:
                now = datetime.now(self.timezone)
                current_time = now.strftime("%H:%M")
                for alarm in self.time_alarms:
                    if alarm['time'] == current_time and alarm.get('enabled', True):
                        self.play_sound(alarm['sound'])
                        self.logger.info(f"Time alarm triggered: {alarm['time']} with {alarm['sound']}")
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error checking time alarms: {e}")
                time.sleep(60)

    def setup_gpio(self):
        if not GPIO_AVAILABLE:
            self.logger.warning("GPIO not available, button functionality disabled")
            return
        try:
            if GPIO_TYPE == "OPi":
                GPIO.setmode(GPIO.BCM)
            else:
                GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            for pin in self.button_pins:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.add_event_detect(pin, GPIO.FALLING, callback=self.button_callback, bouncetime=200)
            self.gpio_initialized = True
            self.logger.info("GPIO setup completed")
        except Exception as e:
            self.logger.warning(f"GPIO setup failed: {e}")

    def setup_display(self):
        if not LUMA_AVAILABLE or self.config.get('mock_mode', False):
            self.logger.info("Using mock display (hardware not available)")
            self.device = MockDevice()
            self.canvas_func = mock_canvas
            return
        try:
            addresses = [0x3C, 0x3D]
            self.device = None
            for addr in addresses:
                try:
                    serial = i2c(port=1, address=addr)
                    self.device = ssd1306(serial, width=128, height=64)
                    self.device.contrast(self.config['display_brightness'])
                    self.canvas_func = canvas
                    self.logger.info(f"OLED initialized at address 0x{addr:02X}")
                    break
                except Exception as e:
                    self.logger.debug(f"Failed to initialize OLED at 0x{addr:02X}: {e}")
            if not self.device:
                self.logger.warning("Could not initialize OLED display, using mock mode")
                self.device = MockDevice()
                self.canvas_func = mock_canvas
        except Exception as e:
            self.logger.error(f"Display setup failed: {e}")
            self.device = MockDevice()
            self.canvas_func = mock_canvas

    def button_callback(self, channel):
        try:
            if channel == self.button_pins[0]:
                self.current_mode = (self.current_mode + 1) % len(self.display_modes)
                self.logger.info(f"Switched to mode: {self.display_modes[self.current_mode]}")
            elif channel == self.button_pins[1]:
                self.cycle_timezone()
            elif channel == self.button_pins[2]:
                self.sync_ntp()
        except Exception as e:
            self.logger.error(f"Button callback error: {e}")

    def cycle_timezone(self):
        if not PYTZ_AVAILABLE:
            self.logger.warning("pytz not available, timezone cycling disabled")
            return
        timezones = ['UTC', 'Africa/Johannesburg', 'US/Eastern', 'US/Pacific', 'Europe/London',
                     'Europe/Berlin', 'Asia/Shanghai', 'Asia/Tokyo', 'Australia/Sydney']
        try:
            current_tz = self.config['timezone']
            current_index = timezones.index(current_tz) if current_tz in timezones else 0
            next_index = (current_index + 1) % len(timezones)
            self.config['timezone'] = timezones[next_index]
            self.timezone = pytz.timezone(timezones[next_index])
            self.save_config()
            self.logger.info(f"Timezone changed to: {timezones[next_index]}")
        except Exception as e:
            self.logger.error(f"Timezone change error: {e}")

    def sync_ntp(self):
        try:
            if os.geteuid() != 0:
                self.logger.debug("NTP sync skipped: requires root privileges")
                self.last_ntp_sync = time.time()
                return False
            for server in self.config['ntp_servers']:
                try:
                    result = subprocess.run(['which', 'ntpdate'], capture_output=True, text=True)
                    if result.returncode == 0:
                        subprocess.check_call(['ntpdate', '-s', server], timeout=10,
                                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        subprocess.check_call(['systemctl', 'restart', 'systemd-timesyncd'], timeout=10,
                                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.last_ntp_sync = time.time()
                    self.logger.info(f"NTP sync successful with {server}")
                    return True
                except Exception as e:
                    self.logger.debug(f"NTP sync failed with {server}: {e}")
            self.logger.warning("All NTP sync attempts failed")
            self.last_ntp_sync = time.time()
            return False
        except Exception as e:
            self.logger.error(f"NTP sync error: {e}")
            self.last_ntp_sync = time.time()
            return False

    def auto_ntp_sync(self):
        if self.config.get('mock_mode', False):
            return
        if time.time() - self.last_ntp_sync > self.ntp_sync_interval:
            self.sync_ntp()

    def get_system_info(self):
        if not PSUTIL_AVAILABLE:
            return {'cpu': 0, 'memory_percent': 0, 'memory_used': 0, 'memory_total': 0,
                    'disk_percent': 0, 'disk_used': 0, 'disk_total': 0}
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            return {
                'cpu': cpu_percent, 'memory_percent': memory.percent,
                'memory_used': memory.used // (1024**2), 'memory_total': memory.total // (1024**2),
                'disk_percent': disk.percent, 'disk_used': disk.used // (1024**3),
                'disk_total': disk.total // (1024**3)
            }
        except Exception as e:
            self.logger.error(f"System info error: {e}")
            return None

    def get_network_info(self):
        try:
            ip_addresses = []
            try:
                result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
                ip_addresses = result.stdout.strip().split()
            except:
                try:
                    import socket
                    hostname = socket.gethostname()
                    ip_addresses = [socket.gethostbyname(hostname)]
                except:
                    ip_addresses = ['Unknown']
            bytes_sent = bytes_recv = 0
            if PSUTIL_AVAILABLE:
                try:
                    net_io = psutil.net_io_counters()
                    bytes_sent = net_io.bytes_sent // (1024**2)
                    bytes_recv = net_io.bytes_recv // (1024**2)
                except:
                    pass
            return {'ip_addresses': ip_addresses, 'bytes_sent': bytes_sent, 'bytes_recv': bytes_recv}
        except Exception as e:
            self.logger.error(f"Network info error: {e}")
            return None

    def get_temperature(self):
        try:
            temp_files = ['/sys/class/thermal/thermal_zone0/temp',
                          '/sys/class/hwmon/hwmon0/temp1_input',
                          '/sys/class/hwmon/hwmon1/temp1_input']
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    with open(temp_file, 'r') as f:
                        temp = int(f.read().strip()) / 1000.0
                        return temp
            if PSUTIL_AVAILABLE:
                try:
                    temps = psutil.sensors_temperatures()
                    if temps:
                        for name, entries in temps.items():
                            if entries:
                                return entries[0].current
                except:
                    pass
            return None
        except Exception as e:
            self.logger.error(f"Temperature reading error: {e}")
            return None

    def draw_datetime(self, draw, width, height):
        try:
            if PYTZ_AVAILABLE:
                now = datetime.now(self.timezone)
                tz_str = str(self.timezone).split('/')[-1]
            else:
                now = datetime.now()
                tz_str = "Local"
            date_str = now.strftime("%a, %b %d %Y")
            time_str = now.strftime("%H:%M:%S")
            draw.text((0, 0), date_str, fill="white")
            draw.text((0, 20), time_str, fill="white")
            draw.text((0, 40), f"TZ: {tz_str}", fill="white")
        except Exception as e:
            draw.text((0, 0), f"Time Error: {str(e)[:15]}", fill="white")

    def draw_system_info(self, draw, width, height):
        try:
            info = self.get_system_info()
            if not info:
                draw.text((0, 0), "System info unavailable", fill="white")
                return
            cpu_alarm = info['cpu'] > self.alarms.get('cpu', 100)
            mem_alarm = info['memory_percent'] > self.alarms.get('memory', 100)
            disk_alarm = info['disk_percent'] > self.alarms.get('disk', 100)
            cpu_text = f"CPU: {info['cpu']:.1f}% {'ALARM' if cpu_alarm else ''}"
            mem_text = f"RAM: {info['memory_percent']:.1f}% {'ALARM' if mem_alarm else ''}"
            disk_text = f"Disk: {info['disk_percent']:.1f}% {'ALARM' if disk_alarm else ''}"
            draw.text((0, 0), cpu_text, fill="white")
            draw.text((0, 12), mem_text, fill="white")
            draw.text((0, 24), f"     {info['memory_used']}MB/{info['memory_total']}MB", fill="white")
            draw.text((0, 36), disk_text, fill="white")
            draw.text((0, 48), f"      {info['disk_used']}GB/{info['disk_total']}GB", fill="white")
        except Exception as e:
            draw.text((0, 0), f"Sys Error: {str(e)[:15]}", fill="white")

    def draw_network_info(self, draw, width, height):
        try:
            info = self.get_network_info()
            if not info:
                draw.text((0, 0), "Network info unavailable", fill="white")
                return
            draw.text((0, 0), "Network Info", fill="white")
            y_pos = 12
            for ip in info['ip_addresses'][:2]:
                draw.text((0, y_pos), f"IP: {ip}", fill="white")
                y_pos += 12
            draw.text((0, y_pos), f"TX: {info['bytes_sent']}MB", fill="white")
            draw.text((0, y_pos + 12), f"RX: {info['bytes_recv']}MB", fill="white")
        except Exception as e:
            draw.text((0, 0), f"Net Error: {str(e)[:15]}", fill="white")

    def draw_temperature(self, draw, width, height):
        try:
            temp = self.get_temperature()
            draw.text((0, 0), "Temperature", fill="white")
            if temp is not None:
                temp_alarm = temp > self.alarms.get('temperature', 100)
                temp_text = f"CPU: {temp:.1f}°C {'ALARM' if temp_alarm else ''}"
                draw.text((0, 20), temp_text, fill="white")
                if temp < 50:
                    status = "COOL"
                elif temp < 70:
                    status = "WARM"
                else:
                    status = "HOT!"
                draw.text((0, 40), f"Status: {status}", fill="white")
            else:
                draw.text((0, 20), "Temperature sensor", fill="white")
                draw.text((0, 32), "not available", fill="white")
        except Exception as e:
            draw.text((0, 0), f"Temp Error: {str(e)[:15]}", fill="white")

    def update_display(self):
        try:
            with self.display_lock:
                if not self.device:
                    return
                with self.canvas_func(self.device) as draw:
                    mode = self.display_modes[self.current_mode]
                    if mode == 'datetime':
                        self.draw_datetime(draw, 128, 64)
                    elif mode == 'system_info':
                        self.draw_system_info(draw, 128, 64)
                    elif mode == 'network_info':
                        self.draw_network_info(draw, 128, 64)
                    elif mode == 'temperature':
                        self.draw_temperature(draw, 128, 64)
        except Exception as e:
            self.logger.error(f"Display update error: {e}")

    def display_thread(self):
        while self.running:
            try:
                self.auto_ntp_sync()
                self.update_display()
                time.sleep(self.config['refresh_rate'])
            except Exception as e:
                self.logger.error(f"Display thread error: {e}")
                time.sleep(5)

    def signal_handler(self, signum, frame):
        self.logger.info("Shutdown signal received")
        self.running = False

    def run(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        if os.geteuid() == 0:
            self.sync_ntp()
        else:
            self.logger.info("Running without root privileges, NTP sync disabled")
        display_thread = threading.Thread(target=self.display_thread)
        display_thread.daemon = True
        display_thread.start()
        alarm_thread = threading.Thread(target=self.check_time_alarms)
        alarm_thread.daemon = True
        alarm_thread.start()
        self.logger.info("NanoPi OLED Monitor started")
        if self.config.get('mock_mode', False):
            self.logger.info("Running in mock mode (no hardware)")
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

    def cleanup(self):
        self.logger.info("Cleaning up...")
        self.running = False
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.quit()
            except:
                pass
        try:
            if self.device and hasattr(self.device, 'cleanup'):
                self.device.cleanup()
        except:
            pass
        try:
            if GPIO_AVAILABLE and self.gpio_initialized:
                GPIO.cleanup()
        except:
            pass
        self.logger.info("Cleanup completed")

def install_packages():
    required_packages = ['luma.oled', 'psutil', 'pytz', 'Pillow', 'pygame']
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_').replace('.', '_'))
            print(f"✓ {package} already installed")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} not found")
    if missing_packages:
        print("\nPlease install missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    return True

if __name__ == "__main__":
    print("Checking and installing required packages...")
    packages_ok = install_packages()
    if not packages_ok:
        response = input("\nDo you want to continue anyway? (y/N): ").lower().strip()
        if response != 'y':
            sys.exit(1)
    monitor = NanoPiOLEDMonitor()
    monitor.run()