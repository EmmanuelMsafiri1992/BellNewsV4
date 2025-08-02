import json
import base64
import hmac
import hashlib
from datetime import datetime, timedelta
import pytz
import os

# Ensure this secret key matches the one used in vcns_timer_web.py for validation
LICENSE_SIGNING_SECRET = os.environ.get("LICENSE_SIGNING_SECRET", "super_secret_signing_key_change_me_in_prod")
LICENSES_FILE = "licenses.json"
LICENSE_EXPIRATION_DAYS = 365 # Licenses valid for 1 year by default
NUMBER_OF_LICENSES = 100

def generate_license_signature(data, secret_key):
    """Generates a HMAC-SHA256 signature for the given data."""
    h = hmac.new(secret_key.encode('utf-8'), data.encode('utf-8'), hashlib.sha256)
    return base64.urlsafe_b64encode(h.digest()).decode('utf-8')

def create_single_license_key(days_valid=LICENSE_EXPIRATION_DAYS):
    """Generates a single new license key with an expiration date."""
    issue_date = datetime.now(pytz.utc)
    expiration_date = issue_date + timedelta(days=days_valid)
    license_data = {
        "issued_at": issue_date.isoformat(),
        "expires_at": expiration_date.isoformat(),
        "type": "standard",
        "version": "1.0",
        "id": os.urandom(8).hex() # Unique ID for each license
    }
    license_json = json.dumps(license_data, sort_keys=True) # Ensure consistent order for signing
    
    signature = generate_license_signature(license_json, LICENSE_SIGNING_SECRET)
    
    encoded_license_data = base64.urlsafe_b64encode(license_json.encode('utf-8')).decode('utf-8')
    full_license_key = f"{encoded_license_data}.{signature}"
    
    return full_license_key, license_data["expires_at"]

def generate_and_save_licenses(num_licenses=NUMBER_OF_LICENSES, filename=LICENSES_FILE):
    """Generates a specified number of licenses and saves them to a JSON file."""
    licenses = []
    print(f"Generating {num_licenses} licenses...")
    for i in range(num_licenses):
        key, expires_at = create_single_license_key(days_valid=LICENSE_EXPIRATION_DAYS)
        licenses.append({"key": key, "expires_at": expires_at, "is_used": False, "used_by": None, "last_used": None})
        if (i + 1) % 10 == 0:
            print(f"Generated {i + 1}/{num_licenses} licenses.")

    try:
        with open(filename, 'w') as f:
            json.dump({"licenses": licenses}, f, indent=4)
        print(f"Successfully generated and saved {num_licenses} licenses to {filename}")
        print("IMPORTANT: Store this file securely and ensure LICENSE_SIGNING_SECRET is consistent.")
    except Exception as e:
        print(f"Error saving licenses to {filename}: {e}")

if __name__ == "__main__":
    generate_and_save_licenses()