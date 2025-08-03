import { showFlashMessage, openModal, closeModal } from './ui.js';
import { systemSettings, setSystemSettings } from './globals.js';
import { fetchSystemSettingsAndUpdateUI } from './main.js'; 

/**
 * Opens the system settings modal and fetches/populates current settings from the backend.
 */
export async function showSettings() {
    try {
        const response = await fetch('/api/system_settings');
        const data = await response.json();
        if (data.status === 'error') {
            showFlashMessage(data.message, 'error', 'dashboardFlashContainer');
            return;
        }
        setSystemSettings(data); // Update global systemSettings object
        console.log("Fetched System Settings:", systemSettings);

        const dynamicIpRadio = document.getElementById('dynamicIp');
        const staticIpRadio = document.getElementById('staticIp');

        if (dynamicIpRadio && staticIpRadio) {
            if (systemSettings.networkSettings.ipType === 'static') {
                staticIpRadio.checked = true;
            } else {
                dynamicIpRadio.checked = true;
            }
        }
        toggleStaticIpFields();

        const ipAddressElem = document.getElementById('ipAddress');
        const subnetMaskElem = document.getElementById('subnetMask');
        const gatewayElem = document.getElementById('gateway');
        const dnsServerElem = document.getElementById('dnsServer');
        const ntpServerElem = document.getElementById('ntpServer');
        const timezoneElem = document.getElementById('timezone');
        const manualDateElem = document.getElementById('manualDate');
        const manualTimeElem = document.getElementById('manualTime');
        const timeType = systemSettings.timeSettings.timeType;

        if (ipAddressElem) ipAddressElem.value = systemSettings.networkSettings.ipAddress || '';
        if (subnetMaskElem) subnetMaskElem.value = systemSettings.networkSettings.subnetMask || '';
        if (gatewayElem) gatewayElem.value = systemSettings.networkSettings.gateway || '';
        if (dnsServerElem) dnsServerElem.value = systemSettings.networkSettings.dnsServer || '';
        if (ntpServerElem) ntpServerElem.value = systemSettings.timeSettings.ntpServer || '';
        if (timezoneElem) timezoneElem.value = systemSettings.timeSettings.timezone || 'UTC';
        if (manualDateElem) manualDateElem.value = systemSettings.timeSettings.manualDate || '';
        if (manualTimeElem) manualTimeElem.value = systemSettings.timeSettings.manualTime || '';

        // Correctly set the time type option
        if (timeType) {
            selectTimeType(timeType);
        }

        openModal('settingsModal');

    } catch (error) {
        console.error('Failed to fetch system settings:', error);
        showFlashMessage('Failed to load system settings. Please try again.', 'error', 'dashboardFlashContainer');
    }
}  

/**
 * Handles the submission of the settings form.
 * @param {Event} event - The form submission event.
 */
export async function handleSettingsSubmit(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // Reconstruct the nested data structure for the API call
    const payload = {
        networkSettings: {
            ipType: data.ipType,
            ipAddress: data.ipAddress,
            subnetMask: data.subnetMask,
            gateway: data.gateway,
            dnsServer: data.dnsServer,
        },
        timeSettings: {
            timeType: data.timeType,
            ntpServer: data.ntpServer,
            timezone: data.timezone,
            manualDate: data.manualDate,
            manualTime: data.manualTime,
        },
    };

    try {
        const response = await fetch('/api/system_settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload),
        });

        const result = await response.json();
        if (result.status === 'success') {
            showFlashMessage(result.message, 'success', 'dashboardFlashContainer');
            setSystemSettings(result.system_settings); // Update global state
            closeModal('settingsModal');
            // Re-fetch and update the current time display
            fetchSystemSettingsAndUpdateUI();
        } else {
            showFlashMessage(result.message, 'error', 'dashboardFlashContainer');
        }
    } catch (error) {
        console.error('Failed to save system settings:', error);
        showFlashMessage('Failed to save settings. Please check your connection.', 'error', 'dashboardFlashContainer');
    }
}  
/**
 * Toggles the visibility of static IP address input fields based on the selected radio button.
 */
export function toggleStaticIpFields() {
    const staticIpFields = document.getElementById('staticIpFields');
    const staticIpRadio = document.getElementById('staticIp');

    if (staticIpFields && staticIpRadio) {
        if (staticIpRadio.checked) {
            staticIpFields.classList.remove('hidden');
        } else {
            staticIpFields.classList.add('hidden');
        }
    }
}

/**
 * Manages the UI state for NTP vs. Manual time settings,
 * showing and hiding the relevant input fields.
 * @param {string} type - The type of time setting to activate ('ntp' or 'manual').
 */
/**
 * Manages the UI state for NTP vs. Manual time settings,
 * showing and hiding the relevant input fields.
 * @param {string} type - The type of time setting to activate ('ntp' or 'manual').
 */
export function selectTimeType(type) {
    const ntpOption = document.getElementById('ntpOption');
    const manualOption = document.getElementById('manualOption');
    const ntpSettingsFields = document.getElementById('ntpSettingsFields');
    const manualTimeFields = document.getElementById('manualTimeFields');
    const manualDateInput = document.getElementById('manualDate');
    const manualTimeInput = document.getElementById('manualTime');

    if (!ntpOption || !manualOption || !ntpSettingsFields || !manualTimeFields || !manualDateInput || !manualTimeInput) {
        console.warn("Missing elements for selectTimeType. Skipping function.");
        return;
    }

    ntpOption.classList.remove('active');
    manualOption.classList.remove('active');

    if (type === 'ntp') {
        ntpOption.classList.add('active');
        ntpSettingsFields.classList.remove('hidden');
        manualTimeFields.classList.add('hidden');
        manualDateInput.removeAttribute('required');
        manualTimeInput.removeAttribute('required');
    } else {
        manualOption.classList.add('active');
        ntpSettingsFields.classList.add('hidden');
        manualTimeFields.classList.remove('hidden');
        manualDateInput.setAttribute('required', 'required');
        manualTimeInput.setAttribute('required', 'required');
    }
}


