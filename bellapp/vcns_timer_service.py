#!/usr/bin/env python3
import os
import logging
import threading
import time
import gc
import signal
import sys
import traceback
import subprocess
from pathlib import Path
from flask import Flask, jsonify, request
import simpleaudio
import psutil
from datetime import datetime, timedelta
import pytz
import json
from threading import Lock
import weakref
import atexit
from functools import wraps

# Configure logging with rotation to prevent log files from growing too large
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "vcns_timer_service.log"
os.makedirs(LOG_DIR, exist_ok=True)

from logging.handlers import RotatingFileHandler

# Setup rotating log handler (max 5MB per file, keep 3 backup files)
log_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5*1024*1024, backupCount=3
)
log_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        log_handler,
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("VCNS-Timer-Service")

app = Flask(__name__)

# Constants
AUDIO_DIR = BASE_DIR / "static" / "audio"
ALARMS_FILE = BASE_DIR / "alarms.json"
CRASH_LOG_FILE = BASE_DIR / "crash.log"
RING_DURATION = 60  # seconds
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MAX_ALARMS = 50  # Prevent memory issues with too many alarms
MAX_MEMORY_PERCENT = 85  # Trigger cleanup at this memory usage
MAX_CPU_PERCENT = 95  # Log warning at this CPU usage
HEALTH_CHECK_INTERVAL = 300  # 5 minutes
WATCHDOG_TIMEOUT = 600  # 10 minutes

# Thread-safe alarm storage
ALARMS = []
alarms_lock = Lock()

# Global shutdown flag
shutdown_flag = threading.Event()

# Watchdog system
last_heartbeat = time.time()
heartbeat_lock = Lock()

# Critical error counter
critical_errors = 0
max_critical_errors = 5

# Sound cache to prevent repeated loading
sound_cache = weakref.WeakValueDictionary()
cache_lock = Lock()

# Initialize audio availability
AUDIO_AVAILABLE = True

def startup_checks():
    """Perform startup validation"""
    try:
        os.makedirs(AUDIO_DIR, exist_ok=True)
        if not AUDIO_DIR.is_dir():
            logger.critical(f"Audio directory {AUDIO_DIR} is not a directory")
            sys.exit(1)
        if not any(AUDIO_DIR.iterdir()):
            logger.warning(f"No audio files found in {AUDIO_DIR}")
        else:
            # Check for at least one valid .wav file
            wav_files = [f for f in AUDIO_DIR.iterdir() if f.suffix.lower() == '.wav']
            if not wav_files:
                logger.warning(f"No .wav files found in {AUDIO_DIR}. simpleaudio requires .wav files.")
    except Exception as e:
        logger.critical(f"Startup checks failed: {e}")
        sys.exit(1)

def crash_handler(func):
    """Decorator to handle crashes and continue operation"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        global critical_errors
        try:
            return func(*args, **kwargs)
        except Exception as e:
            critical_errors += 1
            error_msg = f"CRITICAL ERROR in {func.__name__}: {str(e)}\n{traceback.format_exc()}"
            logger.critical(error_msg)
            
            # Log to crash file
            try:
                with open(CRASH_LOG_FILE, 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - {error_msg}\n")
            except:
                pass  # Don't crash while logging a crash
            
            # If too many critical errors, trigger emergency save and restart
            if critical_errors >= max_critical_errors:
                emergency_save_and_restart()
            
            return None
    return wrapper

def emergency_save_and_restart():
    """Emergency save and restart procedure"""
    try:
        logger.critical("Too many critical errors - triggering emergency restart")
        save_alarms()
        
        # Try to restart the service
        python_exe = sys.executable
        script_path = __file__
        
        # Restart command
        restart_cmd = [python_exe, script_path]
        
        logger.critical("Attempting to restart service...")
        subprocess.Popen(restart_cmd, start_new_session=True)
        
    except Exception as e:
        logger.critical(f"Emergency restart failed: {e}")
    finally:
        os._exit(1)  # Force exit even if threads are stuck

def update_heartbeat():
    """Update the watchdog heartbeat"""
    global last_heartbeat
    with heartbeat_lock:
        last_heartbeat = time.time()

def watchdog_thread():
    """Monitor system health and restart if needed"""
    logger.info("Watchdog thread started")
    
    while not shutdown_flag.is_set():
        try:
            with heartbeat_lock:
                time_since_heartbeat = time.time() - last_heartbeat
            
            if time_since_heartbeat > WATCHDOG_TIMEOUT:
                logger.critical(f"Watchdog timeout - no heartbeat for {time_since_heartbeat:.1f}s")
                emergency_save_and_restart()
            
            # Check system health
            memory = psutil.virtual_memory()
            if memory.percent > 95:  # Critical memory usage
                logger.critical(f"Critical memory usage: {memory.percent:.1f}% - forcing cleanup")
                force_cleanup()
            
            # Check if main thread is still alive
            main_thread = threading.main_thread()
            if not main_thread.is_alive():
                logger.critical("Main thread died - restarting service")
                emergency_save_and_restart()
                
        except Exception as e:
            logger.error(f"Watchdog error: {e}")
        
        time.sleep(30)  # Check every 30 seconds
    
    logger.info("Watchdog thread stopped")

def force_cleanup():
    """Force memory cleanup"""
    try:
        # Clear sound cache
        with cache_lock:
            sound_cache.clear()
        
        # Force garbage collection
        gc.collect()
        
        logger.info("Forced cleanup completed")
    except Exception as e:
        logger.error(f"Force cleanup failed: {e}")

@crash_handler
def load_alarms():
    """Load alarms from persistent storage"""
    global ALARMS
    try:
        if ALARMS_FILE.exists():
            with open(ALARMS_FILE, 'r') as f:
                data = json.load(f)
                with alarms_lock:
                    ALARMS = data.get('alarms', [])
                logger.info(f"Loaded {len(ALARMS)} alarms from file")
        else:
            logger.info("No existing alarms file found")
    except Exception as e:
        logger.error(f"Failed to load alarms: {e}")
        ALARMS = []

@crash_handler
def save_alarms():
    """Save alarms to persistent storage"""
    try:
        # Create backup first
        if ALARMS_FILE.exists():
            backup_file = ALARMS_FILE.with_suffix('.bak')
            ALARMS_FILE.rename(backup_file)
        
        with alarms_lock:
            data = {'alarms': ALARMS}
        
        # Write to temporary file first, then rename (atomic operation)
        temp_file = ALARMS_FILE.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        temp_file.rename(ALARMS_FILE)
        logger.debug("Alarms saved to file")
    except Exception as e:
        logger.error(f"Failed to save alarms: {e}")
        # Try to restore backup if it exists
        backup_file = ALARMS_FILE.with_suffix('.bak')
        if backup_file.exists():
            backup_file.rename(ALARMS_FILE)
            logger.info("Restored alarms from backup")

@crash_handler
def get_cached_sound(sound_path):
    """Get sound from cache or load it"""
    with cache_lock:
        sound = sound_cache.get(str(sound_path))
        if sound is None:
            try:
                sound = simpleaudio.WaveObject.from_wave_file(str(sound_path))
                sound_cache[str(sound_path)] = sound
                logger.debug(f"Cached sound: {sound_path}")
            except Exception as e:
                logger.error(f"Failed to load sound {sound_path}: {e}")
                return None
        return sound

@crash_handler
def play_sound(sound_path):
    """Play sound with improved error handling and resource management"""
    if not AUDIO_AVAILABLE:
        logger.error("Audio not available, cannot play sound")
        return
    
    try:
        if not sound_path.exists():
            logger.error(f"Sound file not found: {sound_path}")
            return
        
        sound = get_cached_sound(sound_path)
        if sound is None:
            return
            
        play_obj = sound.play()
        start_time = time.time()
        while play_obj.is_playing() and time.time() - start_time < RING_DURATION:
            if shutdown_flag.is_set():
                break
            time.sleep(0.1)
            
        if play_obj.is_playing():
            play_obj.stop()
            logger.info(f"Sound stopped after {RING_DURATION}s")
        else:
            logger.info("Sound completed naturally")
            
    except Exception as e:
        logger.error(f"Sound playback failed: {e}")
    finally:
        gc.collect()
        update_heartbeat()

@crash_handler
def check_system_resources():
    """Monitor system resources and log warnings if getting low"""
    try:
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        if memory.percent > MAX_MEMORY_PERCENT:
            logger.warning(f"High memory usage: {memory.percent:.1f}%")
            force_cleanup()
            
        if cpu_percent > MAX_CPU_PERCENT:
            logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
            
        # Log resource usage every hour
        current_time = datetime.now()
        if current_time.minute == 0:
            logger.info(f"Resources - Memory: {memory.percent:.1f}%, CPU: {cpu_percent:.1f}%")
            
    except Exception as e:
        logger.error(f"Failed to check system resources: {e}")

@crash_handler
def check_alarms():
    """Main alarm checking loop with improved error handling"""
    logger.info("Alarm checking thread started")
    last_minute = None
    health_check_counter = 0
    
    while not shutdown_flag.is_set():
        try:
            now = datetime.now(pytz.UTC)
            current_minute = now.strftime("%Y-%m-%d %H:%M")
            
            # Update heartbeat
            update_heartbeat()
            
            # Only process if we're in a new minute to prevent duplicate triggers
            if current_minute != last_minute:
                last_minute = current_minute
                current_day = now.strftime("%A")
                current_time = now.strftime("%H:%M")
                
                # Periodic health checks
                health_check_counter += 1
                if health_check_counter >= 5:  # Every 5 minutes
                    check_system_resources()
                    health_check_counter = 0
                
                with alarms_lock:
                    alarms_to_check = ALARMS.copy()
                
                for i, alarm in enumerate(alarms_to_check):
                    if shutdown_flag.is_set():
                        break
                        
                    try:
                        if alarm.get("day") == current_day and alarm.get("time") == current_time:
                            sound_path = BASE_DIR / alarm.get("sound", "")
                            if sound_path.exists():
                                logger.info(f"Triggering alarm {i}: {alarm}")
                                sound_thread = threading.Thread(
                                    target=play_sound, 
                                    args=(sound_path,), 
                                    daemon=True,
                                    name=f"SoundPlayer-{i}"
                                )
                                sound_thread.start()
                            else:
                                logger.error(f"Sound file missing for alarm {i}: {sound_path}")
                    except Exception as e:
                        logger.error(f"Error processing alarm {i}: {e}")
                        
        except Exception as e:
            logger.error(f"Error in alarm checking loop: {e}")
            
        # Sleep for 30 seconds instead of 60 for more responsive checking
        for _ in range(30):
            if shutdown_flag.is_set():
                break
            time.sleep(1)
    
    logger.info("Alarm checking thread stopped")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down...")
    shutdown_flag.set()
    save_alarms()
    sys.exit(0)

def cleanup_on_exit():
    """Cleanup function called on exit"""
    logger.info("Performing exit cleanup...")
    save_alarms()

# Register signal handlers and exit cleanup
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
atexit.register(cleanup_on_exit)

@app.route("/api/status", methods=["GET"])
def status():
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        cpu_percent = process.cpu_percent()
        
        system_memory = psutil.virtual_memory()
        
        return jsonify({
            "status": "Running",
            "pid": process.pid,
            "memory_mb": round(memory_info.rss / 1024 / 1024, 2),
            "cpu_percent": cpu_percent,
            "system_memory_percent": system_memory.percent,
            "alarm_count": len(ALARMS),
            "audio_available": AUDIO_AVAILABLE,
            "uptime_seconds": int(time.time() - process.create_time()),
            "critical_errors": critical_errors,
            "last_heartbeat": last_heartbeat,
            "watchdog_active": True
        })
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route("/api/alarms", methods=["GET"])
def get_alarms():
    with alarms_lock:
        return jsonify({"alarms": ALARMS.copy()})

@app.route("/api/alarms", methods=["POST"])
def add_alarm():
    try:
        data = request.get_json()
        if not data or not all(key in data for key in ["day", "time", "sound"]):
            logger.error("Invalid alarm data")
            return jsonify({"error": "Missing required fields: day, time, sound"}), 400

        with alarms_lock:
            if len(ALARMS) >= MAX_ALARMS:
                return jsonify({"error": f"Maximum {MAX_ALARMS} alarms allowed"}), 400

        if data["day"] not in DAYS:
            logger.error(f"Invalid day: {data['day']}")
            return jsonify({"error": "Invalid day"}), 400

        try:
            time.strptime(data["time"], "%H:%M")
        except ValueError:
            logger.error(f"Invalid time format: {data['time']}")
            return jsonify({"error": "Invalid time format (use HH:MM)"}), 400

        sound_path = BASE_DIR / data["sound"]
        if not sound_path.exists():
            logger.error(f"Sound file not found: {sound_path}")
            return jsonify({"error": "Sound file not found"}), 400
        if sound_path.suffix.lower() != '.wav':
            logger.error(f"Invalid sound file format: {sound_path}. Only .wav files are supported")
            return jsonify({"error": "Only .wav files are supported"}), 400

        alarm = {
            "day": data["day"],
            "time": data["time"],
            "label": data.get("label", "Alarm"),
            "sound": data["sound"]
        }
        
        with alarms_lock:
            ALARMS.append(alarm)
        
        save_alarms()
        logger.info(f"Added alarm: {alarm}")
        return jsonify({"message": "Alarm added", "alarm": alarm}), 201
        
    except Exception as e:
        logger.error(f"Error adding alarm: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/alarms/<int:index>", methods=["PUT"])
def edit_alarm(index):
    try:
        with alarms_lock:
            if index < 0 or index >= len(ALARMS):
                logger.error(f"Invalid alarm index: {index}")
                return jsonify({"error": "Alarm not found"}), 404

        data = request.get_json()
        if not data or not all(key in data for key in ["day", "time", "sound"]):
            logger.error("Invalid alarm data")
            return jsonify({"error": "Missing required fields: day, time, sound"}), 400

        if data["day"] not in DAYS:
            logger.error(f"Invalid day: {data['day']}")
            return jsonify({"error": "Invalid day"}), 400

        try:
            time.strptime(data["time"], "%H:%M")
        except ValueError:
            logger.error(f"Invalid time format: {data['time']}")
            return jsonify({"error": "Invalid time format (use HH:MM)"}), 400

        sound_path = BASE_DIR / data["sound"]
        if not sound_path.exists():
            logger.error(f"Sound file not found: {sound_path}")
            return jsonify({"error": "Sound file not found"}), 400
        if sound_path.suffix.lower() != '.wav':
            logger.error(f"Invalid sound file format: {sound_path}. Only .wav files are supported")
            return jsonify({"error": "Only .wav files are supported"}), 400

        updated_alarm = {
            "day": data["day"],
            "time": data["time"],
            "label": data.get("label", "Alarm"),
            "sound": data["sound"]
        }
        
        with alarms_lock:
            ALARMS[index] = updated_alarm
        
        save_alarms()
        logger.info(f"Updated alarm at index {index}: {updated_alarm}")
        return jsonify({"message": "Alarm updated", "alarm": updated_alarm})
        
    except Exception as e:
        logger.error(f"Error editing alarm: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/alarms/<int:index>", methods=["DELETE"])
def delete_alarm(index):
    try:
        with alarms_lock:
            if index < 0 or index >= len(ALARMS):
                logger.error(f"Invalid alarm index: {index}")
                return jsonify({"error": "Alarm not found"}), 404

            alarm = ALARMS.pop(index)
        
        save_alarms()
        logger.info(f"Deleted alarm: {alarm}")
        return jsonify({"message": "Alarm deleted"})
        
    except Exception as e:
        logger.error(f"Error deleting alarm: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/test_sound", methods=["POST"])
def test_sound():
    try:
        data = request.get_json()
        if not data or "sound" not in data:
            logger.error("Invalid sound data")
            return jsonify({"error": "Missing sound field"}), 400

        sound_path = BASE_DIR / data["sound"]
        if not sound_path.exists():
            logger.error(f"Sound file not found: {sound_path}")
            return jsonify({"error": "Sound file not found"}), 400
        if sound_path.suffix.lower() != '.wav':
            logger.error(f"Invalid sound file format: {sound_path}. Only .wav files are supported")
            return jsonify({"error": "Only .wav files are supported"}), 400

        threading.Thread(
            target=play_sound, 
            args=(sound_path,), 
            daemon=True,
            name="SoundTest"
        ).start()
        
        logger.info(f"Testing sound: {sound_path}")
        return jsonify({"message": "Sound test triggered"})
        
    except Exception as e:
        logger.error(f"Error testing sound: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/clear_cache", methods=["POST"])
def clear_cache():
    """Clear sound cache to free memory"""
    try:
        force_cleanup()
        logger.info("Sound cache cleared")
        return jsonify({"message": "Cache cleared"})
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/health", methods=["GET"])
def health_check():
    """Comprehensive health check endpoint"""
    try:
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        disk_usage = psutil.disk_usage('/')
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "memory_percent": memory.percent,
            "cpu_percent": cpu_percent,
            "disk_percent": (disk_usage.used / disk_usage.total) * 100,
            "critical_errors": critical_errors,
            "audio_available": AUDIO_AVAILABLE,
            "alarms_loaded": len(ALARMS),
            "threads_active": threading.active_count(),
            "last_heartbeat_ago": time.time() - last_heartbeat
        }
        
        if (memory.percent > 90 or cpu_percent > 95 or 
            critical_errors > 3 or time.time() - last_heartbeat > 300):
            health_status["status"] = "degraded"
        
        if (memory.percent > 95 or critical_errors >= max_critical_errors or 
            time.time() - last_heartbeat > WATCHDOG_TIMEOUT):
            health_status["status"] = "critical"
            
        return jsonify(health_status)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/api/restart", methods=["POST"])
def restart_service():
    """Controlled restart endpoint"""
    try:
        logger.info("Manual restart requested")
        threading.Thread(target=emergency_save_and_restart, daemon=True).start()
        return jsonify({"message": "Restart initiated"})
    except Exception as e:
        logger.error(f"Restart failed: {e}")
        return jsonify({"error": "Restart failed"}), 500

if __name__ == "__main__":
    try:
        startup_checks()
        load_alarms()
        
        watchdog_thread_obj = threading.Thread(target=watchdog_thread, daemon=True, name="Watchdog")
        watchdog_thread_obj.start()
        
        alarm_thread = threading.Thread(target=check_alarms, daemon=True, name="AlarmChecker")
        alarm_thread.start()
        
        logger.info("Starting Flask service on 0.0.0.0:5001")
        logger.info(f"Watchdog timeout: {WATCHDOG_TIMEOUT}s")
        logger.info(f"Max critical errors: {max_critical_errors}")
        
        update_heartbeat()
        
        app.run(
            host="0.0.0.0", 
            port=5001, 
            debug=False, 
            threaded=True,
            use_reloader=False,
            processes=1
        )
        
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.critical(f"Service failed to start: {e}")
        logger.critical(traceback.format_exc())
        try:
            with open(CRASH_LOG_FILE, 'a') as f:
                f.write(f"{datetime.now().isoformat()} - STARTUP CRASH: {str(e)}\n{traceback.format_exc()}\n")
        except:
            pass
    finally:
        shutdown_flag.set()
        save_alarms()
        logger.info("Service stopped")