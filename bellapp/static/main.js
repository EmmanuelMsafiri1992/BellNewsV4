// main.js
// The entry point that orchestrates the initialization and event listener setup,
// importing from other modules.

import { handleLogin, logout, showChangePassword, handleChangePassword } from './auth.js';
import { fetchUsers, showUserManagementTab, showResetPasswordModal, handleResetPassword, handleAddUser } from './userManagement.js';
import { showSettings, handleSettingsSubmit, toggleStaticIpFields, selectTimeType } from './settings.js';
import { showLicenseManagement, generateLicenseKey, handleLicenseSubmit, updateLicenseUI, checkUserRoleAndFeatureActivation, openLicenseTab, fetchAndRenderLicensedUsers, activateFeatures } from './license.js';
import { updateCurrentTime, updateMetrics } from './dashboard.js';
import { populateSounds, testSound, deleteSound, handleSoundUpload } from './sounds.js';
import { handleAddAlarm, fetchAlarmsAndRender, renderAlarms, removeAlarm, editAlarm, handleEditAlarm, renderWeeklyAlarms } from './alarms.js';
import { showFlashMessage, closeModal, openModal } from './ui.js';
import { setCurrentUserRole, setCurrentUserFeaturesActivated, setLicenseInfo, setSystemSettings, licenseInfo, currentUserRole, currentUserFeaturesActivated } from './globals.js';


// Expose functions to the global scope for inline HTML event handlers
// This is necessary because imported functions are not directly accessible from global scope (e.g., onclick attributes)
window.logout = logout;
window.showChangePassword = showChangePassword;
window.showSettings = showSettings;
window.showLicenseManagement = showLicenseManagement;
window.generateLicenseKey = generateLicenseKey;
window.openLicenseTab = openLicenseTab;
window.openModal = openModal; // Expose openModal for general use
window.closeModal = closeModal; // Expose closeModal for general use
window.showUserManagementTab = showUserManagementTab; // Expose for tab switching
window.showResetPasswordModal = showResetPasswordModal; // Expose for button click
window.testSound = testSound; // Expose for sound testing
window.deleteSound = deleteSound; // Expose for sound deletion
window.editAlarm = editAlarm; // Expose for alarm editing
window.removeAlarm = removeAlarm; // Expose for alarm removal
window.activateFeatures = activateFeatures; // Expose for feature activation button


/**
 * Displays the login page and hides the dashboard.
 */
export function showLogin() {
    document.getElementById('loginPage').style.display = 'flex';
    document.getElementById('dashboardPage').style.display = 'none';
}

/**
 * Displays the dashboard and hides the login page.
 * Calls the `init()` function to load and update dashboard content.
 */
export function showDashboard() {
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('dashboardPage').style.display = 'block';
    init(); // Initialize dashboard components and fetch data when shown
}


/**
 * Fetches all system settings from the backend, including license info
 * and current user's roles/feature activation, then updates the UI.
 * This function is crucial for synchronizing frontend state with backend.
 */
export async function fetchSystemSettingsAndUpdateUI() {
    console.log("Fetching system settings and updating UI...");
    try {
        const response = await fetch('/api/system_settings');
        const data = await response.json();
        console.log("System Settings fetched:", data);
        if (data.status === 'error') {
            showFlashMessage(data.message, 'error', 'dashboardFlashContainer');
            return;
        }
        setSystemSettings(data);
        setLicenseInfo(data.license);
        console.log("License Info Status (after fetch):", licenseInfo.status);

        setCurrentUserRole(data.user_role);
        setCurrentUserFeaturesActivated(data.current_user_features_activated);
        console.log(`Current User Role: ${currentUserRole}, Features Activated: ${currentUserFeaturesActivated}`);

        updateLicenseUI();
        checkUserRoleAndFeatureActivation();

        selectTimeType(data.timeSettings.timeType); // Use data directly for this
        const ntpServerInput = document.getElementById('ntpServer');
        const manualDateInput = document.getElementById('manualDate');
        const manualTimeInput = document.getElementById('manualTime');

        if (ntpServerInput) ntpServerInput.value = data.timeSettings.ntpServer || '';
        if (manualDateInput) manualDateInput.value = data.timeSettings.manualDate || '';
        if (manualTimeInput) manualTimeInput.value = data.timeSettings.manualTime || '';

        toggleStaticIpFields();
        console.log("System settings UI updated successfully.");
    } catch (error) {
        console.error("Error fetching system settings for UI update:", error);
        showFlashMessage("Failed to load system settings for dashboard display. " + error.message, "error", 'dashboardFlashContainer');
    }
}

/**
 * Initializes all dashboard components: updates current time, fetches system metrics,
 * populates sound library, fetches and renders alarms, and updates system settings related UI.
 * Also sets up recurring intervals for real-time updates.
 */
async function init() {
    console.log("Initializing dashboard...");
    updateCurrentTime();
    await updateMetrics();
    await populateSounds();
    await fetchAlarmsAndRender();
    await fetchSystemSettingsAndUpdateUI();

    setInterval(updateCurrentTime, 1000);
    setInterval(updateMetrics, 5000);
    console.log("Dashboard initialization complete. Real-time updates started.");
}

/**
 * Event listener for when the DOM content is fully loaded.
 * Determines whether to show the login page or the dashboard based on Flask's initial login status.
 */
document.addEventListener('DOMContentLoaded', () => {
    const loginStatusElement = document.getElementById('flaskLoginStatus');
    const isLoggedInFromFlask = loginStatusElement ? loginStatusElement.value === 'true' : false;

    const resetPasswordDashboardBtn = document.getElementById('resetPasswordBtn');
    if (resetPasswordDashboardBtn) {
        resetPasswordDashboardBtn.addEventListener('click', showResetPasswordModal);
        console.log("Event listener attached to dashboard's 'resetPasswordBtn'.");
    } else {
        console.error("Dashboard button with ID 'resetPasswordBtn' not found.");
    }

    if (isLoggedInFromFlask) {
        console.log("User is already logged in (from Flask status). Showing dashboard.");
        showDashboard();
    } else {
        console.log("User is not logged in (from Flask status). Showing login page.");
        showLogin();
    }

    const dynamicIpRadio = document.getElementById('dynamicIp');
    const staticIpRadio = document.getElementById('staticIp');
    if (dynamicIpRadio) {
        dynamicIpRadio.addEventListener('change', toggleStaticIpFields);
    }
    if (staticIpRadio) {
        staticIpRadio.addEventListener('change', toggleStaticIpFields);
    }

    // Attach event listeners for forms
    document.getElementById('loginForm')?.addEventListener('submit', handleLogin);
    document.getElementById('changePasswordForm')?.addEventListener('submit', handleChangePassword);
    document.getElementById('resetPasswordForm')?.addEventListener('submit', handleResetPassword);
    document.getElementById('addUserForm')?.addEventListener('submit', handleAddUser);
    document.getElementById('settingsForm')?.addEventListener('submit', handleSettingsSubmit);
    document.getElementById('licenseForm')?.addEventListener('submit', handleLicenseSubmit);
    document.getElementById("uploadForm")?.addEventListener("submit", handleSoundUpload);
    document.getElementById("addAlarmForm")?.addEventListener("submit", handleAddAlarm);
    document.getElementById("editAlarmForm")?.addEventListener("submit", handleEditAlarm);

    // Attach event listeners for time setting toggles
    const ntpOption = document.getElementById('ntpOption');
    const manualOption = document.getElementById('manualOption');
    if (ntpOption) {
        ntpOption.addEventListener('click', () => selectTimeType('ntp'));
    }
    if (manualOption) {
        manualOption.addEventListener('click', () => selectTimeType('manual'));
    }

    // Attach event listener for feature activation button
    document.getElementById('activateFeaturesBtn')?.addEventListener('click', activateFeatures);

    // Attach event listeners for modal close buttons
    document.getElementById('closeLoginFlashBtn')?.addEventListener('click', () => closeModal('loginFlashContainer'));
    document.getElementById('closeDashboardFlashBtn')?.addEventListener('click', () => closeModal('dashboardFlashContainer'));
    document.getElementById('closeAddModalBtn')?.addEventListener('click', () => closeModal('addModal'));
    document.getElementById('closeEditModalBtn')?.addEventListener('click', () => closeModal('editModal'));
    document.getElementById('closeResetPasswordModalBtn')?.addEventListener('click', () => closeModal('resetPasswordModal'));
    document.getElementById('closeAddUserModalBtn')?.addEventListener('click', () => closeModal('resetPasswordModal')); // Add User is part of resetPasswordModal
    document.getElementById('closeChangePasswordModalBtn')?.addEventListener('click', () => closeModal('changePasswordModal'));
    document.getElementById('closeSettingsModalBtn')?.addEventListener('click', () => closeModal('settingsModal'));
    document.getElementById('closeLicenseModalBtn')?.addEventListener('click', () => closeModal('licenseModal'));
});
