#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VCNS Timer Service with Robust Time Sync, Auto-Start, and Permission Handling
Runs on Ubuntu-based small PCs (e.g., NanoPi) as a systemd service.
Optimized for reliability, accurate time, and no freezes with full auto-setup.
"""

import os
import sys
import time
import json
import logging.handlers
import datetime
import threading
import subprocess
import platform
import pytz
import socket
import psutil
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash
import pygame
from setup_timer_service import create_service_file
from threading import Lock
import shutil
import stat

# Auto-setup and module installation
def setup_environment():
    base_dir = Path(__file__).resolve().parent
    venv_dir = base_dir / "venv"
    required_modules = ["flask", "pygame", "psutil", "pytz", "requests"]
    is_wsl = "microsoft-standard" in platform.uname().release.lower()

    # Create virtual environment if missing
    if not venv_dir.exists():
        try:
            venv_path = str(venv_dir).replace("/mnt/c/", "/c/") if is_wsl else str(venv_dir)
            subprocess.run([sys.executable, "-m", "venv", venv_path], check=True, capture_output=True, text=True)
            logger.info(f"Created virtual environment at {venv_dir}")
            # Set permissions for venv directory
            os.chmod(venv_dir, 0o755)
            shutil.chown(venv_dir, user=os.getuid(), group=os.getgid())
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create virtual environment: {e.output}")
            sys.exit(1)
        except PermissionError as e:
            logger.error(f"Permission denied creating venv: {e}. Please run with sudo or adjust directory permissions.")
            sys.exit(1)

    # Determine pip path
    pip_path = venv_dir / "bin" / "pip3" if platform.system() != "Windows" else venv_dir / "Scripts" / "pip.exe"
    install_cmd = [str(pip_path) if pip_path.exists() else sys.executable, "-m", "pip"]
    logger.debug(f"Using pip command: {install_cmd}")

    try:
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                logger.info(f"Installing missing module: {module}")
                subprocess.run(install_cmd + ["install", module], check=True, capture_output=True, text=True)
                logger.info(f"Successfully installed {module}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e.output}")
        logger.warning("Attempting system-wide installation as fallback")
        subprocess.run([sys.executable, "-m", "pip", "install"] + required_modules, check=True, capture_output=True, text=True)
        logger.info("Fallback installation completed")

    # Ensure directories exist with proper permissions
    for directory in [base_dir / "static" / "audio", base_dir / "static" / "images"]:
        os.makedirs(directory, exist_ok=True)
        os.chmod(directory, 0o775)
        shutil.chown(directory, user=os.getuid(), group=os.getgid())
        logger.info(f"Ensured directory permissions for {directory}")

    logo_path = base_dir / "static" / "images" / "logo.png"
    if not logo_path.exists():
        try:
            from PIL import Image
            Image.new("RGB", (100, 100), color=(255, 255, 255)).save(logo_path)
            os.chmod(logo_path, 0o664)
            shutil.chown(logo_path, user=os.getuid(), group=os.getgid())
            logger.info(f"Created default logo at {logo_path}")
        except ImportError:
            logger.warning(f"PIL not available, logo.png not created. Ensure 'Pillow' is installed for default logo.")
    logger.info("Directories verified or created")

    if not platform.system() == "Windows" and not is_wsl:
        service_file = Path("/etc/systemd/system/vcns-timer.service")
        try:
            result = subprocess.run(["systemctl", "is-active", "vcns-timer.service"], capture_output=True, text=True, timeout=5)
            if result.returncode != 0 or result.stdout.strip() != "active":
                logger.info("Setting up systemd service...")
                subprocess.run(["sudo", sys.executable, str(base_dir / "setup_timer_service.py")], check=True, capture_output=True, text=True)
                os.chmod(service_file, 0o644)
                shutil.chown(service_file, user="root", group="root")
                logger.info("Service file created, starting service...")
                subprocess.run(["sudo", "systemctl", "start", "vcns-timer.service"], check=True, capture_output=True, text=True)
                logger.info("Service started")
            else:
                logger.info("Service already active, skipping setup")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set up or start service: {e.output}. Please run 'sudo python3 setup_timer_service.py' and 'sudo systemctl start vcns-timer.service' manually.")
        except PermissionError:
            logger.error("Permission denied for systemd setup. Run with sudo or adjust /etc/systemd/system/ permissions.")
        except Exception as e:
            logger.error(f"Unexpected error during service setup: {e}")

# Configure logging with rotation
BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "vcns_timer.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("VCNS-Timer")

# Run setup before anything else
setup_environment()

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()

# Paths and Locks
ALARM_FILE = BASE_DIR / "alarms.json"
UPLOAD_FOLDER = BASE_DIR / "static" / "audio"
LOGO_PATH = BASE_DIR / "static" / "images" / "logo.png"
file_lock = Lock()

# Constants
RING_DURATION = 20
IS_WINDOWS = platform.system() == "Windows"
IS_WSL = "microsoft-standard" in platform.uname().release.lower() if not IS_WINDOWS else False
MAX_RETRIES = 3
SYNC_INTERVAL = 3600
DRIFT_THRESHOLD = 30
HEALTH_CHECK_INTERVAL = 60

# Initialize pygame mixer
PYGAME_AVAILABLE = True
try:
    pygame.mixer.init()
    logger.info("Pygame mixer initialized")
except pygame.error as e:
    logger.warning(f"Failed to initialize pygame mixer: {e}. Sound playback disabled.")
    PYGAME_AVAILABLE = False

# Timezone detection with dynamic update
LOCAL_TZ = pytz.UTC
def update_timezone():
    global LOCAL_TZ
    try:
        if IS_WSL:
            LOCAL_TZ = pytz.UTC
            logger.warning("Running in WSL; using UTC timezone. Configure host timezone if needed.")
        else:
            new_tz = pytz.timezone(subprocess.check_output(["timedatectl", "show", "-p", "Timezone", "--value"], text=True).strip())
            if LOCAL_TZ.zone != new_tz.zone:
                logger.info(f"Timezone updated from {LOCAL_TZ.zone} to {new_tz.zone}")
                LOCAL_TZ = new_tz
    except Exception as e:
        logger.warning(f"Failed to update timezone: {e}, keeping {LOCAL_TZ.zone}")
    threading.Timer(86400, update_timezone).start()

update_timezone()

# ------------------ Helpers ------------------
def safe_file_write(file_path, content, is_binary=False, retries=MAX_RETRIES):
    mode = "wb" if is_binary else "w"
    temp_path = str(file_path) + ".tmp"
    for attempt in range(retries):
        with file_lock:
            try:
                with open(temp_path, mode) as f:
                    if is_binary:
                        f.write(content)
                    else:
                        f.write(content)
                    f.flush()
                    os.fsync(f.fileno())
                os.chmod(temp_path, 0o664)  # Set readable/writable by owner and group
                shutil.chown(temp_path, user=os.getuid(), group=os.getgid())
                os.replace(temp_path, file_path)
                os.chmod(file_path, 0o664)
                shutil.chown(file_path, user=os.getuid(), group=os.getgid())
                logger.debug(f"Successfully wrote to {file_path}")
                return True
            except PermissionError as e:
                logger.error(f"Permission denied writing {file_path} (attempt {attempt + 1}/{retries}): {e}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if attempt < retries - 1:
                    time.sleep(1)
                    # Attempt to fix permissions and retry
                    try:
                        os.chmod(file_path.parent, 0o775)
                        shutil.chown(file_path.parent, user=os.getuid(), group=os.getgid())
                    except PermissionError:
                        logger.warning(f"Cannot adjust parent directory permissions for {file_path.parent}. Try running with sudo.")
                else:
                    logger.critical(f"Failed to write {file_path} after {retries} attempts. Check directory permissions.")
                    return False
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{retries} failed to write {file_path}: {e}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if attempt < retries - 1:
                    time.sleep(1)
                else:
                    raise
    return False

def get_alarms():
    with file_lock:
        if ALARM_FILE.exists():
            try:
                os.chmod(ALARM_FILE, 0o664)
                shutil.chown(ALARM_FILE, user=os.getuid(), group=os.getgid())
                with open(ALARM_FILE) as f:
                    alarms = json.load(f)
                    if not isinstance(alarms, list):
                        logger.error("Alarms file is not a list, resetting to empty list")
                        return []
                    valid_alarms = []
                    valid_days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                    for alarm in alarms:
                        if not isinstance(alarm, dict):
                            logger.error(f"Invalid alarm entry (not a dict): {alarm}")
                            continue
                        if not all(key in alarm for key in ["day", "time", "label", "sound"]):
                            logger.error(f"Invalid alarm entry (missing keys): {alarm}")
                            continue
                        if alarm["day"] not in valid_days:
                            logger.error(f"Invalid day in alarm: {alarm['day']}")
                            continue
                        try:
                            datetime.datetime.strptime(alarm["time"], "%H:%M")
                        except ValueError:
                            logger.error(f"Invalid time format in alarm: {alarm['time']}")
                            continue
                        sound_path = BASE_DIR / alarm["sound"]
                        if not sound_path.exists():
                            logger.warning(f"Sound file not found for alarm: {alarm['sound']}")
                            continue
                        valid_alarms.append(alarm)
                    logger.debug(f"Loaded {len(valid_alarms)} valid alarms")
                    return valid_alarms
            except PermissionError as e:
                logger.error(f"Permission denied reading {ALARM_FILE}: {e}. Attempting to fix permissions.")
                try:
                    os.chmod(ALARM_FILE, 0o664)
                    shutil.chown(ALARM_FILE, user=os.getuid(), group=os.getgid())
                    return get_alarms()  # Retry after fixing
                except Exception as e2:
                    logger.critical(f"Failed to fix permissions for {ALARM_FILE}: {e2}. Resetting to empty list.")
                    return []
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in alarms file: {e}, resetting to empty list")
                return []
            except Exception as e:
                logger.error(f"Unexpected error reading alarms: {e}")
                return []
        logger.info("No alarms file found, returning empty list")
        return []

def save_alarms(alarms):
    with file_lock:
        try:
            content = json.dumps(alarms, indent=2)
            if not safe_file_write(ALARM_FILE, content):
                logger.error("Failed to save alarms after retries")
                return False
            logger.debug(f"Saved {len(alarms)} alarms to {ALARM_FILE}")
            return True
        except Exception as e:
            logger.error(f"Failed to save alarms: {e}")
            return False

def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def sync_time():
    if IS_WSL:
        logger.warning("Time sync skipped in WSL; relies on host system clock.")
        return True
    ntp_servers = ["pool.ntp.org", "time.google.com", "time.windows.com", "ntp.ubuntu.com"]
    for server in ntp_servers:
        for attempt in range(MAX_RETRIES):
            try:
                cmd = ["ntpdate", "-u", server]
                subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=10)
                logger.info(f"Time synced with {server} (attempt {attempt + 1})")
                return True
            except (subprocess.SubprocessError, FileNotFoundError) as e:
                logger.debug(f"Failed to sync with {server} (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2)
                else:
                    break
    logger.warning("NTP sync failed, attempting HTTP time sync")
    return sync_time_http()

def sync_time_http():
    if not is_connected():
        logger.warning("No internet connection for HTTP time sync")
        return False
    try:
        import requests
        response = requests.get("https://www.google.com", timeout=5)
        server_time = datetime.datetime.strptime(response.headers["date"], "%a, %d %b %Y %H:%M:%S %Z")
        local_time = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
        offset = (server_time - local_time).total_seconds()
        if abs(offset) > DRIFT_THRESHOLD:
            logger.info(f"Adjusting time by {offset} seconds via HTTP")
            os.system(f"date -u -s @{int(server_time.timestamp())}")
            return True
        return True
    except Exception as e:
        logger.error(f"HTTP time sync failed: {e}")
        return False

def check_time_offset():
    if IS_WSL:
        logger.debug("Time offset check skipped in WSL; relies on host system clock.")
        return False
    if not is_connected():
        logger.info("No internet connection - skipping time check")
        return False
    for server in ["pool.ntp.org", "time.google.com"]:
        try:
            output = subprocess.check_output(["ntpdate", "-q", server], universal_newlines=True, timeout=10)
            for line in output.split("\n"):
                if "offset" in line:
                    offset = float(line.split("offset")[1].split(",")[0].strip())
                    logger.info(f"Time offset from {server}: {offset}s")
                    return abs(offset) > DRIFT_THRESHOLD
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.debug(f"Failed to check offset with {server}: {e}")
    return False

def play_sound(sound_path):
    if not PYGAME_AVAILABLE:
        logger.warning("Pygame audio not available; sound playback skipped.")
        return
    sound_path_str = str(sound_path.resolve())
    logger.debug(f"Attempting to play sound: {sound_path_str}")
    try:
        pygame.mixer.music.load(sound_path_str)
        pygame.mixer.music.play()
        start_time = time.time()
        while pygame.mixer.music.get_busy() and (time.time() - start_time) < RING_DURATION:
            time.sleep(0.1)
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            logger.info(f"Sound stopped after {RING_DURATION}s")
        else:
            logger.info("Sound completed")
    except pygame.error as e:
        logger.error(f"Pygame sound playback failed: {e}")

def ring_alarm(path):
    path = Path(path)
    if path.exists():
        logger.info(f"Playing alarm sound: {path}")
        try:
            play_sound(path)
        except Exception as e:
            logger.error(f"Sound playback failed: {e}")
    else:
        logger.error(f"Sound file not found: {path}")

def alarm_loop():
    last_triggered = set()
    while True:
        try:
            now = datetime.datetime.now(LOCAL_TZ)
            current_day = now.strftime("%A")
            current_time = now.strftime("%H:%M")
            current_minute = now.hour * 60 + now.minute

            alarms = get_alarms()
            with file_lock:
                for alarm in alarms:
                    try:
                        alarm_id = f"{alarm['day']}_{alarm['time']}_{alarm['sound']}"
                        alarm_time = datetime.datetime.strptime(alarm["time"], "%H:%M")
                        alarm_minute = alarm_time.hour * 60 + alarm_time.minute
                        time_diff = current_minute - alarm_minute
                        if (
                            alarm["day"] == current_day
                            and 0 <= time_diff <= 1
                            and alarm_id not in last_triggered
                        ):
                            sound_path = BASE_DIR / alarm["sound"]
                            if sound_path.exists():
                                threading.Thread(target=ring_alarm, args=(sound_path,), daemon=True).start()
                                last_triggered.add(alarm_id)
                                logger.info(f"Triggered alarm: {alarm_id}")
                            else:
                                logger.error(f"Sound file not found: {sound_path}")
                        elif time_diff > 1 and alarm_id in last_triggered:
                            last_triggered.remove(alarm_id)
                    except (KeyError, ValueError) as e:
                        logger.error(f"Invalid alarm: {alarm}, error: {e}")
            if now.second == 0:
                last_triggered.clear()
            time.sleep(1)
        except Exception as e:
            logger.error(f"Alarm loop error: {e}")
            time.sleep(5)

def time_sync_watchdog():
    last_sync = time.time()
    while True:
        try:
            if time.time() - last_sync >= SYNC_INTERVAL or check_time_offset():
                logger.warning("Large time offset or sync interval exceeded, syncing...")
                if sync_time():
                    last_sync = time.time()
                else:
                    logger.error("Time sync failed, retrying in 5 minutes")
                    time.sleep(300)
            else:
                logger.debug("Time in sync")
            time.sleep(60)
        except Exception as e:
            logger.error(f"Time sync watchdog error: {e}")
            time.sleep(300)

def process_watchdog():
    while True:
        try:
            process = psutil.Process()
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = process.memory_info()
            memory_used = memory_info.rss / (1024 * 1024)
            if cpu_percent > 80 or memory_used > 500:
                logger.critical(f"High resource usage detected: CPU={cpu_percent}%, Memory={memory_used}MB, restarting...")
                os._exit(1)
            time.sleep(HEALTH_CHECK_INTERVAL)
        except Exception as e:
            logger.error(f"Process watchdog error: {e}")
            time.sleep(HEALTH_CHECK_INTERVAL)

def get_service_status():
    if IS_WSL:
        return {"status": "N/A", "message": "Systemd not available in WSL"}
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "vcns-timer.service"],
            capture_output=True,
            text=True,
            timeout=5
        )
        status = result.stdout.strip()
        if status == "active":
            return {"status": "Running", "message": "VCNS Timer service is active"}
        else:
            return {"status": "Not Running", "message": f"VCNS Timer service is {status}"}
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.error(f"Failed to check service status: {e}")
        return {"status": "Error", "message": f"Could not check service status: {e}"}

def get_performance_metrics():
    try:
        process = psutil.Process()
        with process.oneshot():
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_info = process.memory_info()
            memory_used = memory_info.rss / (1024 * 1024)
            create_time = process.create_time()
            uptime_seconds = time.time() - create_time
            uptime_formatted = str(datetime.timedelta(seconds=int(uptime_seconds)))
        return {
            "process": {
                "cpu_percent": round(cpu_percent, 2),
                "memory_mb": round(memory_used, 2),
                "uptime_formatted": uptime_formatted
            },
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=0.1, percpu=True),
                "memory_percent": psutil.virtual_memory().percent
            }
        }
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        return {
            "process": {
                "cpu_percent": 0,
                "memory_mb": 0,
                "uptime_formatted": "0:00:00"
            },
            "system": {
                "cpu_percent": [0],
                "memory_percent": 0
            }
        }

# ------------------ Routes ------------------
@app.route("/", methods=["GET", "POST"])
def index():
    current_time = datetime.datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
    next_alarm = get_next_alarm().get("next_alarm")
    alarms = get_alarms()
    sounds = get_sounds()
    day_order = {
        "Sunday": 0,
        "Monday": 1,
        "Tuesday": 2,
        "Wednesday": 3,
        "Thursday": 4,
        "Friday": 5,
        "Saturday": 6,
    }
    alarms.sort(
        key=lambda x: (
            day_order.get(x.get("day"), 7),
            datetime.datetime.strptime(x["time"], "%H:%M"),
        )
    )
    service_status = get_service_status()
    metrics = get_performance_metrics()
    return render_template(
        "index.html",
        current_time=current_time,
        timezone=str(LOCAL_TZ),
        next_alarm=next_alarm,
        alarms=alarms,
        sounds=sounds,
        days=["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
        service_status=service_status,
        metrics=metrics,
        logo_path=url_for('static', filename='images/logo.png') if LOGO_PATH.exists() else None
    )

@app.route("/set_alarm", methods=["POST"])
def set_alarm():
    try:
        day = request.form.get("day")
        time_str = request.form.get("time")  # Comes as HH:MM from <input type="time">
        label = request.form.get("label", "").strip() or "Alarm"
        sound = request.form.get("sound")

        logger.debug(f"Received form data: day={day}, time={time_str}, label={label}, sound={sound}")

        valid_days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        if day not in valid_days:
            logger.error(f"Invalid day provided: {day}")
            flash("Invalid day selected", "error")
            return redirect(url_for("index"))

        try:
            time_obj = datetime.datetime.strptime(time_str, "%H:%M")
            time_str = time_obj.strftime("%H:%M")
        except ValueError as e:
            logger.error(f"Invalid time format: {time_str}, error: {e}")
            flash("Invalid time format. Use HH:MM (24-hour)", "error")
            return redirect(url_for("index"))

        sound_path = BASE_DIR / sound
        if not sound_path.exists():
            logger.error(f"Sound file not found: {sound}")
            flash("Selected sound file not found", "error")
            return redirect(url_for("index"))

        new_alarm = {"day": day, "time": time_str, "label": label, "sound": sound}

        alarms = get_alarms()
        with file_lock:
            alarms.append(new_alarm)
            if not save_alarms(alarms):
                logger.error(f"Failed to save alarms after adding {new_alarm}")
                flash("Failed to save alarm due to I/O or permission issue. Check logs.", "error")
                return redirect(url_for("index"), code=302)

        logger.info(f"Added new alarm: {new_alarm}")
        flash(f"Alarm set for {day} at {time_str}", "success")
        return redirect(url_for("index"), code=302)
    except PermissionError as e:
        logger.error(f"Permission error in set_alarm: {e}")
        flash("Permission denied while saving alarm. Try running with sudo or adjust permissions.", "error")
        return redirect(url_for("index"), code=302)
    except Exception as e:
        logger.error(f"Error setting alarm: {e}")
        flash(f"Failed to set alarm: {str(e)}", "error")
        return redirect(url_for("index"), code=302)

@app.route("/get_next_alarm")
def get_next_alarm():
    alarms = get_alarms()
    if not alarms:
        return {"next_alarm": None}
    now = datetime.datetime.now(LOCAL_TZ)
    current_day = now.strftime("%A")
    current_time = now.strftime("%H:%M")
    day_order = {"Sunday": 0, "Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4, "Friday": 5, "Saturday": 6}
    alarm_times = []
    for alarm in alarms:
        try:
            alarm_time = datetime.datetime.strptime(alarm["time"], "%H:%M")
            day_index = day_order[alarm["day"]]
            alarm_times.append({
                "day": alarm["day"],
                "time": alarm["time"],
                "label": alarm["label"],
                "sound": alarm["sound"],
                "sort_key": (day_index, alarm_time.hour, alarm_time.minute)
            })
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid alarm format: {alarm}, error: {e}")
    current_day_index = day_order[current_day]
    current_hour, current_minute = map(int, current_time.split(":"))
    next_alarm = None
    min_days_ahead = 8
    for alarm in alarm_times:
        alarm_day_index = day_order[alarm["day"]]
        alarm_hour, alarm_minute = map(int, alarm["time"].split(":"))
        days_ahead = alarm_day_index - current_day_index
        if days_ahead < 0:
            days_ahead += 7
        time_diff = (alarm_hour * 60 + alarm_minute) - (current_hour * 60 + current_minute)
        if days_ahead == 0 and time_diff <= 0:
            days_ahead += 7
        if days_ahead < min_days_ahead or (days_ahead == min_days_ahead and time_diff < 0):
            min_days_ahead = days_ahead
            next_alarm = alarm
    return {"next_alarm": next_alarm}

@app.route("/delete_alarm/<int:index>", methods=["POST"])
def delete_alarm(index):
    alarms = get_alarms()
    if 0 <= index < len(alarms):
        deleted_alarm = alarms[index]
        with file_lock:
            del alarms[index]
            if not save_alarms(alarms):
                flash("Failed to delete alarm due to I/O or permission issue", "error")
                return redirect(url_for("index"))
        flash(f"Alarm for {deleted_alarm['day']} at {deleted_alarm['time']} deleted", "success")
    else:
        flash("Invalid alarm index", "error")
    return redirect(url_for("index"))

@app.route("/edit_alarm/<int:index>", methods=["POST"])
def edit_alarm(index):
    alarms = get_alarms()
    if 0 <= index < len(alarms):
        alarms[index] = {
            "day": request.form["day"],
            "time": request.form["time"],
            "label": request.form["label"],
            "sound": request.form["sound"],
        }
        day_order = {"Sunday": 0, "Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4, "Friday": 5, "Saturday": 6}
        with file_lock:
            alarms.sort(key=lambda x: (day_order.get(x.get("day"), 7), datetime.datetime.strptime(x["time"], "%H:%M")))
            if not save_alarms(alarms):
                flash("Failed to edit alarm due to I/O or permission issue", "error")
                return redirect(url_for("index"))
        flash(f"Alarm for {alarms[index]['day']} at {alarms[index]['time']} updated", "success")
    else:
        flash("Invalid alarm index", "error")
    return redirect(url_for("index"))

@app.route("/upload", methods=["POST"])
def upload():
    try:
        file = request.files.get("file")
        if not file:
            logger.error("No file uploaded")
            flash("No file uploaded", "error")
            return redirect(url_for("index"))
        if not file.filename.lower().endswith(".mp3"):
            logger.error(f"Invalid file type: {file.filename}")
            flash("Only .mp3 files allowed", "error")
            return redirect(url_for("index"))
        file_content = file.read()
        if len(file_content) > 2 * 1024 * 1024:
            logger.error(f"File too large: {len(file_content)} bytes")
            flash("File too large (max 2MB)", "error")
            return redirect(url_for("index"))
        file.seek(0)
        safe_filename = os.path.basename(file.filename)
        save_path = UPLOAD_FOLDER / safe_filename
        with file_lock:
            with open(save_path, "wb") as f:
                f.write(file_content)
                f.flush()
                os.fsync(f.fileno())
            os.chmod(save_path, 0o664)
            shutil.chown(save_path, user=os.getuid(), group=os.getgid())
        logger.info(f"Uploaded: {save_path}")
        flash(f"Uploaded {safe_filename}", "success")
    except PermissionError as e:
        logger.error(f"Permission denied uploading file to {save_path}: {e}")
        flash("Permission denied while uploading file. Try running with sudo or adjust permissions.", "error")
        return redirect(url_for("index"))
    except Exception as e:
        logger.error(f"Upload error: {e}")
        flash(f"Upload failed: {e}", "error")
    return redirect(url_for("index"))

@app.route("/delete_song/<filename>", methods=["POST"])
def delete_song(filename):
    safe_filename = os.path.basename(filename)
    path = UPLOAD_FOLDER / safe_filename
    if path.exists():
        try:
            with file_lock:
                path.unlink()
            logger.info(f"Deleted song: {safe_filename}")
            flash(f"Deleted {safe_filename}", "success")
        except PermissionError as e:
            logger.error(f"Permission denied deleting {path}: {e}")
            flash("Permission denied while deleting file. Try running with sudo or adjust permissions.", "error")
        except Exception as e:
            logger.error(f"Failed to delete song: {e}")
            flash(f"Failed to delete {safe_filename}", "error")
    else:
        flash(f"File {safe_filename} not found", "error")
    return redirect(url_for("index"))

@app.route("/test_sound", methods=["POST"])
def test_sound():
    sound_path = BASE_DIR / request.form["sound"]
    if sound_path.exists():
        logger.info(f"Testing sound: {sound_path}")
        threading.Thread(target=ring_alarm, args=(sound_path,), daemon=True).start()
        flash("Playing sound...", "success")
    else:
        logger.error(f"Sound file not found: {sound_path}")
        flash(f"Sound file not found: {sound_path}", "error")
    return redirect(url_for("index"))

def get_sounds():
    with file_lock:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        os.chmod(UPLOAD_FOLDER, 0o775)
        shutil.chown(UPLOAD_FOLDER, user=os.getuid(), group=os.getgid())
        return [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith(".mp3")]

def start_background_threads():
    threading.Thread(target=alarm_loop, daemon=True).start()
    if not IS_WSL:
        threading.Thread(target=time_sync_watchdog, daemon=True).start()
        threading.Thread(target=process_watchdog, daemon=True).start()

if __name__ == "__main__":
    try:
        logger.info(f"Starting VCNS Timer on {platform.system()} (Python {platform.python_version()})")
        logger.info(f"Using timezone: {LOCAL_TZ}")
        if IS_WSL:
            logger.warning("Running in WSL; audio and time sync may be limited. Skipping systemd setup.")
        else:
            logger.info("Attempting to set up systemd service automatically...")
            try:
                create_service_file()
            except Exception as e:
                logger.error(f"Failed to set up systemd service: {e}. Run setup_timer_service.py with sudo manually.")
        start_background_threads()
        app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
    except Exception as e:
        logger.critical(f"Application crashed: {e}")
        raise