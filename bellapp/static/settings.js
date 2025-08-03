// Manages system settings (network, time).
import { showFlashMessage, openModal, closeModal } from './ui.js';
import { systemSettings, setSystemSettings } from './globals.js';

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

        if (ipAddressElem) ipAddressElem.value = systemSettings.networkSettings.ipAddress || '';
        if (subnetMaskElem) subnetMaskElem.value = systemSettings.networkSettings.subnetMask || '';
        if (gatewayElem) gatewayElem.value = systemSettings.networkSettings.gateway || '';
        if (dnsServerElem) dnsServerElem.value = systemSettings.networkSettings.dnsServer || '';

        // Populate time settings
        const ntpOption = document.getElementById('ntpOption');
        const manualOption = document.getElementById('manualOption');
        const ntpServerInput = document.getElementById('ntpServer');
        const manualDateInput = document.getElementById('manualDate');
        const manualTimeInput = document.getElementById('manualTime');
        const timezoneSelect = document.getElementById('timezone');

        if (systemSettings.timeSettings.timeType === 'ntp') {
            ntpOption.click(); // Use click() to trigger the event listener
        } else {
            manualOption.click();
        }

        if (ntpServerInput) ntpServerInput.value = systemSettings.timeSettings.ntpServer || '';
        if (timezoneSelect) timezoneSelect.value = systemSettings.timeSettings.timezone || 'UTC';

        // Open the modal after all fields are populated
        openModal('settingsModal');

    } catch (error) {
        console.error('Error fetching system settings:', error);
        showFlashMessage('Failed to fetch system settings.', 'error', 'dashboardFlashContainer');
    }
}

/**
 * Handles the form submission for system settings, sending the data to the backend API.
 */
export async function handleSettingsSubmit(event) {
    event.preventDefault(); // Prevent the default form submission

    const form = event.target;
    const ipType = form.querySelector('input[name="ipType"]:checked')?.value;
    const ipAddress = form.querySelector('#ipAddress')?.value;
    const subnetMask = form.querySelector('#subnetMask')?.value;
    const gateway = form.querySelector('#gateway')?.value;
    const dnsServer = form.querySelector('#dnsServer')?.value;

    const timeType = form.querySelector('input[name="timeType"]:checked')?.value;
    const ntpServer = form.querySelector('#ntpServer')?.value;
    const manualDate = form.querySelector('#manualDate')?.value;
    const manualTime = form.querySelector('#manualTime')?.value;
    const timezone = form.querySelector('#timezone')?.value;

    // Client-side validation for static IP settings
    if (ipType === 'static' && (!ipAddress || !subnetMask || !gateway || !dnsServer)) {
        showFlashMessage('All static IP fields are required.', 'error', 'settingsFlashContainer');
        return;
    }

    const networkSettings = {
        ipType,
        ipAddress: ipAddress || null,
        subnetMask: subnetMask || null,
        gateway: gateway || null,
        dnsServer: dnsServer || null
    };

    const timeSettings = {
        timeType,
        timezone,
        ntpServer: ntpServer || null,
        manualDate: manualDate || null,
        manualTime: manualTime || null
    };

    try {
        // Send network settings
        let networkResponse;
        if (ipType) {
            networkResponse = await fetch('/api/apply_network_settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(networkSettings)
            });
            const networkResult = await networkResponse.json();
            showFlashMessage(networkResult.message, networkResult.status, 'settingsFlashContainer');
        }

        // Send time settings
        let timeResponse;
        if (timeType) {
            timeResponse = await fetch('/api/apply_time_settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(timeSettings)
            });
            const timeResult = await timeResponse.json();
            showFlashMessage(timeResult.message, timeResult.status, 'settingsFlashContainer');
        }

    } catch (error) {
        console.error('Error applying settings:', error);
        showFlashMessage('An error occurred while applying settings.', 'error', 'settingsFlashContainer');
    }
}

/**
 * Toggles the visibility of the static IP input fields based on the selected radio button.
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
 * Handles the visual state of the time setting options and their associated input fields.
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
    } else { // type === 'manual'
        manualOption.classList.add('active');
        ntpSettingsFields.classList.add('hidden');
        manualTimeFields.classList.remove('hidden');
        manualDateInput.setAttribute('required', 'required');
        manualTimeInput.setAttribute('required', 'required');
    }
}
