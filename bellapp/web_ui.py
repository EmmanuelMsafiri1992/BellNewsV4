#!/usr/bin/env python3
"""
Flask web UI for setting time-based alarms in NanoPi OLED Monitor
"""
from flask import Flask, render_template, request, jsonify, send_from_directory
from pathlib import Path
import json
import logging
import os

app = Flask(__name__)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / '.nanopi_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

CONFIG_FILE = Path.home() / '.nanopi_monitor_config.json'
SOUND_DIR = Path.home() / '.nanopi_sounds'

def ensure_sound_dir():
    """Ensure the sound directory exists with correct permissions"""
    try:
        SOUND_DIR.mkdir(exist_ok=True)
        os.chmod(SOUND_DIR, 0o755)
        logger.info(f"Sound directory ensured: {SOUND_DIR}")
    except Exception as e:
        logger.error(f"Failed to create sound directory {SOUND_DIR}: {e}")
        raise

def load_config():
    """Load configuration from file"""
    default_config = {
        'timezone': 'Africa/Johannesburg',
        'time_alarms': []
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                default_config.update(config)
        except Exception as e:
            logger.error(f"Could not load config: {e}")
    return default_config

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info("Alarm settings saved successfully")
        return True
    except Exception as e:
        logger.error(f"Could not save config: {e}")
        return False

@app.route('/')
def index():
    """Render the main UI"""
    ensure_sound_dir()
    config = load_config()
    sounds = [f.name for f in SOUND_DIR.iterdir() if f.suffix.lower() in ['.mp3', '.wav']]
    return render_template('index.html', alarms=config['time_alarms'], sounds=sounds)

@app.route('/save_alarm', methods=['POST'])
def save_alarm():
    """Save a new or updated alarm"""
    try:
        data = request.json
        time = data.get('time')
        sound = data.get('sound')
        enabled = data.get('enabled', True)
        # Validate time format (HH:MM)
        try:
            from datetime import datetime
            datetime.strptime(time, '%H:%M')
        except ValueError:
            return jsonify({'error': 'Invalid time format (use HH:MM)'}), 400
        # Validate sound file
        if not (SOUND_DIR / sound).exists():
            return jsonify({'error': 'Selected sound file not found'}), 400
        config = load_config()
        # Update or add alarm
        alarms = config['time_alarms']
        for alarm in alarms:
            if alarm['time'] == time:
                alarm.update({'sound': sound, 'enabled': enabled})
                break
        else:
            alarms.append({'time': time, 'sound': sound, 'enabled': enabled})
        config['time_alarms'] = alarms
        logger.info(f"Saving alarm: {time} with {sound}")
        if save_config(config):
            return jsonify({'message': 'Alarm saved successfully'})
        else:
            return jsonify({'error': 'Failed to save alarm'}), 500
    except Exception as e:
        logger.error(f"Error saving alarm: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/delete_alarm/<time>', methods=['DELETE'])
def delete_alarm(time):
    """Delete an alarm"""
    try:
        config = load_config()
        config['time_alarms'] = [alarm for alarm in config['time_alarms'] if alarm['time'] != time]
        logger.info(f"Deleting alarm: {time}")
        if save_config(config):
            return jsonify({'message': 'Alarm deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete alarm'}), 500
    except Exception as e:
        logger.error(f"Error deleting alarm: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/upload_sound', methods=['POST'])
def upload_sound():
    """Upload a sound file"""
    try:
        ensure_sound_dir()
        if 'sound' not in request.files:
            logger.warning("No file part in request")
            return jsonify({'error': 'No file uploaded'}), 400
        file = request.files['sound']
        if file.filename == '':
            logger.warning("No file selected")
            return jsonify({'error': 'No file selected'}), 400
        if file and file.filename.lower().endswith(('.mp3', '.wav')):
            # Sanitize filename
            filename = file.filename.replace('/', '_').replace('\\', '_')
            file_path = SOUND_DIR / filename
            file.save(file_path)
            # Verify file was saved
            if file_path.exists():
                logger.info(f"Sound file saved: {filename} at {file_path}")
                return jsonify({'message': 'Sound uploaded successfully'})
            else:
                logger.error(f"Sound file not saved: {filename}")
                return jsonify({'error': 'Failed to save sound file'}), 500
        else:
            logger.warning(f"Invalid file format: {file.filename}")
            return jsonify({'error': 'Invalid file format (use MP3 or WAV)'}), 400
    except Exception as e:
        logger.error(f"Error uploading sound: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/sounds/<filename>')
def serve_sound(filename):
    """Serve sound files"""
    try:
        return send_from_directory(SOUND_DIR, filename)
    except Exception as e:
        logger.error(f"Error serving sound {filename}: {e}")
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    logger.info("Starting Flask web UI on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)