// Manages system settings (network, time).
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
        const manualDateElem = document.getElementById('manualDate');
        const manualTimeElem = document.getElementById('manualTime');

        if (ipAddressElem) ipAddressElem.value = systemSettings.networkSettings.ipAddress || '';
        if (subnetMaskElem) subnetMaskElem.value = systemSettings.networkSettings.subnetMask || '';
        if (gatewayElem) gatewayElem.value = systemSettings.networkSettings.gateway || '';
        if (dnsServerElem) dnsServerElem.value = systemSettings.networkSettings.dnsServer || '';
        if (ntpServerElem) ntpServerElem.value = systemSettings.timeSettings.ntpServer || '';
        if (manualDateElem) manualDateElem.value = systemSettings.timeSettings.manualDate || '';
        if (manualTimeElem) manualTimeElem.value = systemSettings.timeSettings.manualTime || '';

        // Select the correct time type radio button
        const timeType = systemSettings.timeSettings.timeType || 'ntp';
        selectTimeType(timeType);

        openModal('settingsModal');

    } catch (error) {
        console.error("Error fetching system settings:", error);
        showFlashMessage('Failed to fetch system settings. See console for details.', 'error', 'dashboardFlashContainer');
    }
}


/**
 * Handles the submission of the settings form.
 * @param {Event} event - The form submission event.
 */
export async function handleSettingsSubmit(event) {
    event.preventDefault();
    console.log("Settings form submitted.");

    // --- FIX FOR ReferenceError: ipType is not defined ---
    // Get the value of the selected IP type radio button before trying to use it.
    const ipType = document.querySelector('input[name="ipType"]:checked').value;
    // --- END OF FIX ---

    const form = event.target;
    const networkSettings = {
        ipType: ipType, // Use the defined ipType variable here
        ipAddress: form.ipAddress.value,
        subnetMask: form.subnetMask.value,
        gateway: form.gateway.value,
        dnsServer: form.dnsServer.value,
    };

    const timeType = document.querySelector('input[name="timeType"]:checked').value;
    const timeSettings = {
        timeType: timeType,
        ntpServer: form.ntpServer.value,
        manualDate: form.manualDate.value,
        manualTime: form.manualTime.value,
    };
    
    // Determine which API endpoint to call based on the selected IP type
    let apiUrl;
    if (ipType === 'static') {
        apiUrl = '/api/configure_static_ip';
    } else { // ipType === 'dynamic'
        apiUrl = '/api/configure_dynamic_ip';
    }

    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ networkSettings, timeSettings }),
        });

        const data = await response.json();
        
        if (data.status === 'success') {
            showFlashMessage(data.message, 'success', 'settingsModalFlashContainer');
            // Re-fetch and update UI to reflect new settings
            fetchSystemSettingsAndUpdateUI();
        } else {
            showFlashMessage(data.message, 'error', 'settingsModalFlashContainer');
        }

    } catch (error) {
        console.error("Error submitting settings:", error);
        showFlashMessage('Failed to save settings. An unexpected error occurred.', 'error', 'settingsModalFlashContainer');
    }
}
/**
 * Toggles the visibility and required status of the static IP input fields.
 */
export function toggleStaticIpFields() {
    const staticIpFields = document.getElementById('staticIpFields');
    const staticIpRadio = document.getElementById('staticIp');
    const ipAddressInput = document.getElementById('ipAddress');
    const subnetMaskInput = document.getElementById('subnetMask');
    const gatewayInput = document.getElementById('gateway');
    const dnsServerInput = document.getElementById('dnsServer');

    if (!staticIpFields || !ipAddressInput || !subnetMaskInput || !gatewayInput || !dnsServerInput || !staticIpRadio) {
        console.warn("Missing elements for toggleStaticIpFields. Skipping function.");
        return;
    }

    if (staticIpRadio.checked) {
        staticIpFields.classList.remove('hidden');
        ipAddressInput.setAttribute('required', 'required');
        subnetMaskInput.setAttribute('required', 'required');
        gatewayInput.setAttribute('required', 'required');
        // DNS is optional
        dnsServerInput.removeAttribute('required');
    } else {
        staticIpFields.classList.add('hidden');
        ipAddressInput.removeAttribute('required');
        subnetMaskInput.removeAttribute('required');
        gatewayInput.removeAttribute('required');
        dnsServerInput.removeAttribute('required');
    }
}

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
    } else { // type === 'manual'
        manualOption.classList.add('active');
        ntpSettingsFields.classList.add('hidden');
        manualTimeFields.classList.remove('hidden');
        manualDateInput.setAttribute('required', 'required');
        manualTimeInput.setAttribute('required', 'required');
    }
}
/**
 * Toggles between NTP server and Manual time setting options in the settings modal.
 * Updates active class for buttons and shows/hides relevant input fields.
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
