// Global variables to store application state and data
export let alarms = []; // Array to store alarm objects fetched from the backend
export let sounds = []; // Array to store available sound file names
export let currentUserRole = document.getElementById('currentUserRoleInput') ? document.getElementById('currentUserRoleInput').value : 'guest';
export let currentUserFeaturesActivated = document.getElementById('currentUserFeaturesActivatedInput') ? JSON.parse(document.getElementById('currentUserFeaturesActivatedInput').value) : false;
export let licenseInfo = {}; // Object to store system-wide license details, fetched via API
export let systemSettings = {}; // Object to store system settings (network, time, etc.), fetched via API

// Setter functions for global variables
export function setAlarms(newAlarms) {
    alarms = newAlarms;
}

export function setSounds(newSounds) {
    sounds = newSounds;
}

export function setCurrentUserRole(role) {
    currentUserRole = role;
}

export function setCurrentUserFeaturesActivated(status) {
    currentUserFeaturesActivated = status;
}

export function setLicenseInfo(info) {
    licenseInfo = info;
}

export function setSystemSettings(settings) {
    systemSettings = settings;
}
