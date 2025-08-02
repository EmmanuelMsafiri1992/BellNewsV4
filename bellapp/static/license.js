// Handles license management (generation, validation, licensed users).
import { showFlashMessage, openModal } from './ui.js';
import { licenseInfo, currentUserRole, setLicenseInfo } from './globals.js';
import { fetchSystemSettingsAndUpdateUI } from './main.js'; // Import main function for refresh

/**
 * Opens the license management modal.
 * Populates the system license fields and conditionally fetches/renders licensed users for superusers.
 * Also controls the visibility of 'Generate New Key' and 'Licensed Users' tab based on user role.
 */
export async function showLicenseManagement() {
    const licenseKeyElem = document.getElementById('licenseKey');
    const licenseExpiryElem = document.getElementById('licenseExpiry');
    const generateKeyBtn = document.getElementById('generateKeyBtn');
    const validateLicenseBtn = document.getElementById('validateLicenseBtn');
    const licensedUsersTabBtn = document.getElementById('licensedUsersTabBtn');

    if (!licenseKeyElem || !licenseExpiryElem || !generateKeyBtn || !validateLicenseBtn || !licensedUsersTabBtn) {
        console.warn("One or more critical license management elements not found. Cannot show license management modal.");
        return;
    }

    licenseKeyElem.value = licenseInfo.key || '';
    licenseExpiryElem.value = licenseInfo.expiry ? licenseInfo.expiry.substring(0, 16) : '';

    if (currentUserRole === 'superuser') {
        generateKeyBtn.classList.remove('hidden');
        validateLicenseBtn.classList.remove('hidden');
        licensedUsersTabBtn.classList.remove('hidden');
        await fetchAndRenderLicensedUsers();
    } else {
        generateKeyBtn.classList.add('hidden');
        validateLicenseBtn.classList.add('hidden');
        licensedUsersTabBtn.classList.add('hidden');
    }

    openModal('licenseModal');
    openLicenseTab('manageLicense');
}

/**
 * Sends a request to the backend to generate a new system-wide license key (UUID).
 * Updates the license key input field with the newly generated key.
 */
export async function generateLicenseKey() {
    try {
        const response = await fetch('/api/generate_license_key');
        const result = await response.json();
        if (result.status === 'success') {
            const licenseKeyElem = document.getElementById('licenseKey');
            if (licenseKeyElem) licenseKeyElem.value = result.licenseKey;
            showFlashMessage("New system license key generated successfully.", "info", 'dashboardFlashContainer');
        } else {
            showFlashMessage(result.message, "error", 'dashboardFlashContainer');
        }
    } catch (error) {
        console.error("Error generating license key:", error);
        showFlashMessage("Network error generating license key. " + error.message, "error", 'dashboardFlashContainer');
    }
}

/**
 * Event listener for the system license validation form submission.
 * Sends the license key and expiry date to the backend for validation and application.
 */
export async function handleLicenseSubmit(e) {
    e.preventDefault();
    console.log("License form submitted.");
    const licenseKeyElem = document.getElementById('licenseKey');
    const licenseExpiryElem = document.getElementById('licenseExpiry');

    const licenseKey = licenseKeyElem ? licenseKeyElem.value : '';
    const fullExpiry = licenseExpiryElem ? `${licenseExpiryElem.value}:00` : '';

    console.log("Sending license data:", { licenseKey: licenseKey, expiryDate: fullExpiry });

    try {
        const response = await fetch('/api/license', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ licenseKey: licenseKey, expiryDate: fullExpiry })
        });
        const result = await response.json();
        console.log("License Validation Response:", result);
        if (result.status === 'success') {
            showFlashMessage(result.message, "success", 'dashboardFlashContainer');
            setLicenseInfo(result.licenseInfo); // Update global system license info
            await fetchSystemSettingsAndUpdateUI();
            // closeModal('licenseModal'); // Removed to avoid circular dependency
        } else {
            showFlashMessage(result.message, "error", 'dashboardFlashContainer');
        }
    } catch (error) {
        console.error("Error validating license:", error);
        showFlashMessage("Network error validating license. " + error.message, "error", 'dashboardFlashContainer');
    }
}

/**
 * Updates the UI elements displaying the system-wide license status and expiry date.
 */
export function updateLicenseUI() {
    const statusBadge = document.getElementById('licenseStatusBadge');
    const expiryDateElem = document.getElementById('licenseExpiryDate');

    if (!statusBadge || !expiryDateElem) {
        console.warn("License UI elements not found. Skipping updateLicenseUI.");
        return;
    }

    if (!licenseInfo || !licenseInfo.status) {
        statusBadge.textContent = "Unknown";
        statusBadge.className = `license-status-badge unlicensed`;
        expiryDateElem.textContent = 'N/A';
        return;
    }

    statusBadge.textContent = licenseInfo.status.replace(/_/g, ' ');
    statusBadge.className = `license-status-badge ${licenseInfo.status}`;

    if (licenseInfo.expiry) {
        try {
            const expiryDate = new Date(licenseInfo.expiry);
            expiryDateElem.textContent = expiryDate.toLocaleDateString() + ' ' + expiryDate.toLocaleTimeString();
        } catch (e) {
            console.error("Error parsing license expiry date:", e);
            expiryDateElem.textContent = 'Invalid Date Format';
        }
    } else {
        expiryDateElem.textContent = 'N/A';
    }
}

/**
 * Controls the visibility and enabled/disabled state of various UI elements
 * based on the current user's role (admin, superuser) and their feature activation status.
 * This function centralized all permission-based UI adjustments.
 */
export async function checkUserRoleAndFeatureActivation() {
    const resetPasswordBtn = document.getElementById('resetPasswordBtn');
    const licenseBtn = document.getElementById('licenseManagementBtn');
    const addAlarmBtn = document.getElementById('addAlarmBtn');
    const uploadSoundBtn = document.getElementById('uploadSoundBtn');
    const featureActivationCard = document.getElementById('featureActivationCard');
    const generateKeyBtn = document.getElementById('generateKeyBtn');
    const validateLicenseBtn = document.getElementById('validateLicenseBtn');
    const licensedUsersTabBtn = document.getElementById('licensedUsersTabBtn');

    const elements = { licenseBtn, addAlarmBtn, uploadSoundBtn, featureActivationCard, generateKeyBtn, validateLicenseBtn, licensedUsersTabBtn };
    for (const key in elements) {
        if (!elements[key]) {
            console.warn(`UI element '${key}' not found during permission check.`);
        }
    }

    if (currentUserRole === "superuser") {
        if (licenseBtn) licenseBtn.classList.remove('hidden');
        if (addAlarmBtn) addAlarmBtn.disabled = false;
        if (uploadSoundBtn) uploadSoundBtn.disabled = false;
        if (featureActivationCard) featureActivationCard.classList.add('hidden');
        if (generateKeyBtn) generateKeyBtn.classList.remove('hidden');
        if (validateLicenseBtn) validateLicenseBtn.classList.remove('hidden');
        if (licensedUsersTabBtn) licensedUsersTabBtn.classList.remove('hidden');

    }
    else if (currentUserRole === "admin") {
        if (licenseBtn) licenseBtn.classList.add('hidden');
        if (generateKeyBtn) generateKeyBtn.classList.add('hidden');
        if (validateLicenseBtn) validateLicenseBtn.classList.add('hidden');
        if (licensedUsersTabBtn) licensedUsersTabBtn.classList.add('hidden');

        if (licenseInfo.status === 'active' && !currentUserFeaturesActivated) {
            if (featureActivationCard) featureActivationCard.classList.remove('hidden');
            if (addAlarmBtn) addAlarmBtn.disabled = true;
            if (uploadSoundBtn) uploadSoundBtn.disabled = true;
        }
        else if (licenseInfo.status === 'active' && currentUserFeaturesActivated) {
            if (featureActivationCard) featureActivationCard.classList.add('hidden');
            if (addAlarmBtn) addAlarmBtn.disabled = false;
            if (uploadSoundBtn) uploadSoundBtn.disabled = false;
        }
        else {
            if (featureActivationCard) featureActivationCard.classList.add('hidden');
            if (addAlarmBtn) addAlarmBtn.disabled = true;
            if (uploadSoundBtn) uploadSoundBtn.disabled = true;

            if (currentUserRole === 'admin') {
                showFlashMessage("System is not yet licensed or license expired, please contact your superadmin for the license.", "error", 'dashboardFlashContainer');
            }
        }
    }
    else {
        if (licenseBtn) licenseBtn.classList.add('hidden');
        if (featureActivationCard) featureActivationCard.classList.add('hidden');
        if (addAlarmBtn) addAlarmBtn.disabled = true;
        if (uploadSoundBtn) uploadSoundBtn.disabled = true;
        if (generateKeyBtn) generateKeyBtn.classList.add('hidden');
        if (validateLicenseBtn) validateLicenseBtn.classList.add('hidden');
        if (licensedUsersTabBtn) licensedUsersTabBtn.classList.add('hidden');
    }
    if (resetPasswordBtn) {
        if (currentUserRole === 'superuser') {
            resetPasswordBtn.classList.remove('hidden');
        } else {
            resetPasswordBtn.classList.add('hidden');
        }
    }
}

/**
 * Sends a request to the backend to activate premium features for the current admin user.
 * Updates UI and redirects based on the response.
 */
export async function activateFeatures() {
    try {
        const response = await fetch('/activate_features', { method: 'POST' });
        const html = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const newFlashMessagesContainer = doc.getElementById('dashboardFlashMessages');

        if (newFlashMessagesContainer) {
            const flaskGeneratedMessages = Array.from(newFlashMessagesContainer.querySelectorAll('ul.flashes li'));
            flaskGeneratedMessages.forEach(msgElement => {
                const message = msgElement.textContent.trim();
                let type = 'info';
                if (msgElement.classList.contains('success')) type = 'success';
                else if (msgElement.classList.contains('error')) type = 'error';
                else if (msgElement.classList.contains('warning')) type = 'warning';
                else if (msgElement.classList.contains('info')) type = 'info';
                showFlashMessage(message, type, 'dashboardFlashContainer');
            });
        }
        if (response.redirected) {
            window.location.href = response.url;
        } else if (response.ok) {
            await fetchSystemSettingsAndUpdateUI();
        }
    } catch (error) {
        console.error("Error activating features:", error);
        showFlashMessage("Network error during feature activation. " + error.message, "error", 'dashboardFlashContainer');
    }
}

/**
 * Manages the tabbed interface within the License Management Modal.
 * Activates the selected tab and hides others.
 * @param {string} tabId - The ID of the tab content to display (e.g., 'manageLicense', 'licensedUsers').
 */
export function openLicenseTab(tabId) {
    const tabs = document.querySelectorAll('.tab-content');
    const buttons = document.querySelectorAll('.tab-button');

    tabs.forEach(tab => tab.classList.remove('active'));
    buttons.forEach(button => button.classList.remove('active'));

    const targetTab = document.getElementById(tabId);
    const targetButton = document.querySelector(`.tab-button[onclick="openLicenseTab('${tabId}')"]`);

    if (targetTab) targetTab.classList.add('active');
    if (targetButton) targetButton.classList.add('active');

    if (tabId === 'licensedUsers' && currentUserRole !== 'superuser') {
        if (document.getElementById('manageLicense')) {
            document.getElementById('manageLicense').classList.add('active');
        }
        if (document.querySelector('.tab-button[onclick="openLicenseTab(\'manageLicense\')"]')) {
            document.querySelector('.tab-button[onclick="openLicenseTab(\'manageLicense\')"]').classList.add('active');
        }
        showFlashMessage("You do not have permission to view licensed users. Only superusers can access this information.", "error", 'dashboardFlashContainer');
    }
}

/**
 * Fetches the list of individually licensed users from the backend
 * and renders them into the 'Licensed Users' table.
 * Only accessible by superusers.
 */
export async function fetchAndRenderLicensedUsers() {
    const tbody = document.getElementById('licensedUsersTableBody');
    const noUsersDiv = document.getElementById('noLicensedUsers');

    if (!tbody || !noUsersDiv) {
        console.warn("Missing licensed users UI elements (table body or 'no users' div). Skipping fetchAndRenderLicensedUsers.");
        return;
    }

    tbody.innerHTML = '';
    noUsersDiv.classList.add('hidden');

    try {
        const response = await fetch('/api/licensed_users');
        const data = await response.json();

        if (data.status === 'error') {
            showFlashMessage(data.message, 'error', 'dashboardFlashContainer');
            noUsersDiv.classList.remove('hidden');
            return;
        }

        const licensedUsers = data.licensedUsers || [];
        console.log("Fetched licensed users:", licensedUsers);

        if (licensedUsers.length === 0) {
            noUsersDiv.classList.remove('hidden');
        } else {
            licensedUsers.forEach(user => {
                const row = document.createElement('tr');
                row.className = 'bg-white border-b hover:bg-gray-50';
                const activatedAt = user.activated_at ? new Date(user.activated_at).toLocaleString() : 'N/A';
                row.innerHTML = `
                    <td class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap">${user.user_id}</td>
                    <td class="px-6 py-4">${activatedAt}</td>
                `;
                tbody.appendChild(row);
            });
        }

    } catch (error) {
        console.error("Error fetching licensed users:", error);
        showFlashMessage("Failed to load licensed users list. " + error.message, "error", 'dashboardFlashContainer');
        noUsersDiv.classList.remove('hidden');
    }
}
