// Handles login, logout, and password change functionalities.
import { showFlashMessage, openModal } from './ui.js';
import { fetchSystemSettingsAndUpdateUI, showDashboard, showLogin } from './main.js'; // Import main functions for navigation/refresh

/**
 * Event listener for the login form submission.
 * Prevents default form submission, handles AJAX login, and updates UI based on response.
 */
export async function handleLogin(e) {
    e.preventDefault(); // Prevent default form submission
    console.log("Login form submitted."); // Debug log
    const loginBtn = document.getElementById('loginBtn');
    const btnIcon = loginBtn ? loginBtn.querySelector('i') : null;

    if (btnIcon) {
        btnIcon.className = 'fas fa-spinner fa-spin mr-2'; // Spinner icon
        loginBtn.textContent = 'Authenticating...'; // Update button text
    }
    if (loginBtn) loginBtn.disabled = true; // Disable button to prevent multiple submissions

    const formData = new FormData(this);

    try {
        const response = await fetch('/login', {
            method: 'POST',
            body: formData
        });
        console.log("Login Response Status:", response.status);

        if (response.redirected) {
            console.log("Login: Backend initiated redirect. Navigating to:", response.url);
            window.location.href = response.url;
            return;
        } else {
            let result;
            let isJson = false;
            try {
                result = await response.json();
                isJson = true;
                console.log("Login: Parsed JSON response:", result);
            } catch (jsonError) {
                const html = await response.text();
                console.log("Login: Parsed HTML body for debugging:", html);
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');

                let messageDisplayed = false;
                const flaskFlashList = doc.querySelector('ul.flashes');
                if (flaskFlashList) {
                    const messages = Array.from(flaskFlashList.children);
                    if (messages.length > 0) {
                        messages.forEach(msgElement => {
                            const message = msgElement.textContent.trim();
                            let type = 'info';
                            if (msgElement.classList.contains('success')) type = 'success';
                            else if (msgElement.classList.contains('error')) type = 'error';
                            else if (msgElement.classList.contains('warning')) type = 'warning';
                            else if (msgElement.classList.contains('info')) type = 'info';
                            showFlashMessage(message, type, 'loginFlashContainer', true);
                            messageDisplayed = true;
                        });
                    }
                }
                if (!messageDisplayed) {
                    showFlashMessage("Login failed. Please check your username and password.", "error", 'loginFlashContainer', false);
                }
                console.log("Login: Backend did not redirect. Displaying flash message from HTML.");
            }

            if (isJson) {
                if (result.status === 'success' && result.redirect_url) {
                    console.log("Login: JSON success with redirect. Navigating to:", result.redirect_url);
                    window.location.href = result.redirect_url;
                } else if (result.status === 'error' && result.message) {
                    showFlashMessage(result.message, "error", 'loginFlashContainer', false);
                    console.log("Login: JSON error. Displaying flash message.");
                } else {
                    showFlashMessage("Login failed due to an unexpected server response.", "error", 'loginFlashContainer', false);
                    console.error("Login: Unexpected JSON response structure.", result);
                }
            }
        }
    } catch (error) {
        console.error("Login fetch error:", error);
        if (error.message.includes("too many redirects")) {
            showFlashMessage("Network error: Too many redirects. Please check server configuration.", "error", 'loginFlashContainer', false);
        } else {
            showFlashMessage("Network error during login attempt. Please check your connection and try again.", "error", 'loginFlashContainer', false);
        }
    } finally {
        if (loginBtn) {
            if (btnIcon) {
                btnIcon.className = 'fas fa-sign-in-alt mr-2';
            }
            loginBtn.textContent = 'Sign In';
            loginBtn.disabled = false;
            console.log("Login button state reset.");
        }
    }
}

/**
 * Logs out the current user by sending a POST request to the logout endpoint.
 * Redirects to the login page on success.
 */
export async function logout() {
    showFlashMessage("Logging out of the system...", "info", 'dashboardFlashContainer');
    try {
        const response = await fetch('/logout', { method: 'POST' });
        if (response.redirected) {
            window.location.href = response.url;
        } else {
            showLogin();
            showFlashMessage("You have been successfully logged out.", "success", 'loginFlashContainer');
        }
    } catch (error) {
        console.error("Logout fetch error:", error);
        showFlashMessage("Network error occurred during logout. Please try again.", "error", 'dashboardFlashContainer');
        showLogin();
    }
}

/**
 * Opens the change password modal.
 */
export function showChangePassword() {
    openModal('changePasswordModal');
}

/**
 * Event listener for the change password form submission.
 * Validates new passwords, sends to backend, and handles UI updates.
 */
export async function handleChangePassword(e) {
    e.preventDefault();
    console.log("Change Password form submitted.");
    const currentPasswordInput = document.getElementById('currentPassword');
    const newPasswordInput = document.getElementById('newPassword');
    const confirmPasswordInput = document.getElementById('confirmPassword');

    if (!currentPasswordInput || !newPasswordInput || !confirmPasswordInput) {
        console.error("Missing password input elements in the form.");
        showFlashMessage("An internal error occurred: Password fields not found.", "error", 'dashboardFlashContainer');
        return;
    }

    if (newPasswordInput.value.length < 8) {
        showFlashMessage("New password must be at least 8 characters long for security.", "error", 'dashboardFlashContainer');
        return;
    }
    if (newPasswordInput.value !== confirmPasswordInput.value) {
        showFlashMessage("New passwords do not match. Please re-enter them carefully.", "error", 'dashboardFlashContainer');
        return;
    }

    const formData = new FormData(this);
    try {
        const response = await fetch('/change_password', {
            method: 'POST',
            body: formData
        });
        console.log("Change Password Response Status:", response.status);
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
            closeModal('changePasswordModal');
            this.reset();
        } else {
            showFlashMessage("Failed to change password. Please check your current password and try again.", "error", 'dashboardFlashContainer');
        }
    } catch (error) {
        console.error("Password change fetch error:", error);
        showFlashMessage("Network error during password change. Please ensure you are connected to the server.", "error", 'dashboardFlashContainer');
    }
}
