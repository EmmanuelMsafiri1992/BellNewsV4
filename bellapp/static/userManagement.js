// Manages user fetching, adding, and resetting passwords (superuser features).
import { showFlashMessage, openModal, closeModal } from './ui.js';

/**
 * Fetches the list of users from the backend and populates the dropdown
 * in the reset password form.
 */
export async function fetchUsers() {
    const resetUsernameSelect = document.getElementById('resetUsername');
    if (!resetUsernameSelect) {
        console.error("User select dropdown not found.");
        return;
    }
    resetUsernameSelect.innerHTML = '<option value="">Loading users...</option>';

    try {
        const response = await fetch('/api/users');
        const data = await response.json();

        if (response.ok && data.users) {
            resetUsernameSelect.innerHTML = '<option value="">Select a user</option>';
            data.users.forEach(user => {
                const option = document.createElement('option');
                option.value = user.username;
                option.textContent = `${user.username} (${user.role})`;
                resetUsernameSelect.appendChild(option);
            });
            console.log("Users fetched and populated:", data.users);
        } else {
            showFlashMessage(data.message || 'Failed to load users.', 'error', 'dashboardFlashContainer');
            resetUsernameSelect.innerHTML = '<option value="">Failed to load users</option>';
            console.error("Failed to fetch users:", data.message);
        }
    } catch (error) {
        console.error("Network error fetching users:", error);
        showFlashMessage('An error occurred while fetching users.', "error", 'dashboardFlashContainer');
        resetUsernameSelect.innerHTML = '<option value="">Network error</option>';
    }
}

/**
 * Manages the tabbed interface within the User Management Modal (Reset Password/Add User).
 * Activates the selected tab and hides others.
 * @param {string} tabId - The ID of the tab content to display ('resetPasswordView' or 'addUserView').
 */
export function showUserManagementTab(tabId) {
    const tabs = document.querySelectorAll('#resetPasswordModal .tab-content');
    const buttons = document.querySelectorAll('#resetPasswordModal .tab-button');

    tabs.forEach(tab => tab.classList.add('hidden'));
    buttons.forEach(button => button.classList.remove('active'));

    const targetTab = document.getElementById(tabId);
    const targetButton = document.getElementById(tabId.replace('View', 'TabBtn'));

    if (targetTab) targetTab.classList.remove('hidden');
    if (targetButton) targetButton.classList.add('active');

    if (tabId === 'resetPasswordView') {
        fetchUsers();
    }
}

/**
 * Displays the User Management Modal (for superusers), defaulting to the Reset Password view.
 * Fetches the list of users when opened.
 */
export async function showResetPasswordModal() {
    console.log("Showing User Management modal for superuser.");
    openModal('resetPasswordModal');
    await fetchUsers();
    showUserManagementTab('resetPasswordView');
}

/**
 * Event listener for the superadmin password reset form submission.
 * Validates new passwords, sends to backend, and handles UI updates.
 */
export async function handleResetPassword(e) {
    e.preventDefault();
    console.log("Reset Password form submitted by superadmin.");
    const resetUsernameInput = document.getElementById('resetUsername');
    const resetNewPasswordInput = document.getElementById('resetNewPassword');
    const resetConfirmPasswordInput = document.getElementById('resetConfirmPassword');

    if (!resetUsernameInput || !resetNewPasswordInput || !resetConfirmPasswordInput) {
        console.error("Missing input elements in the reset password form.");
        showFlashMessage("An internal error occurred: Reset password fields not found.", "error", 'dashboardFlashContainer');
        return;
    }

    if (resetNewPasswordInput.value.length < 8) {
        showFlashMessage("New password must be at least 8 characters long for security.", "error", 'dashboardFlashContainer');
        return;
    }
    if (resetNewPasswordInput.value !== resetConfirmPasswordInput.value) {
        showFlashMessage("New passwords do not match. Please re-enter them carefully.", "error", 'dashboardFlashContainer');
        return;
    }

    const formData = new FormData(this);
    try {
        const response = await fetch('/admin/reset_password', {
            method: 'POST',
            body: formData
        });
        console.log("Reset Password Response Status:", response.status);
        const result = await response.json();

        if (result.status === 'success') {
            showFlashMessage(result.message, "success", 'dashboardFlashContainer');
            closeModal('resetPasswordModal');
            this.reset();
        } else {
            showFlashMessage(result.message, "error", 'dashboardFlashContainer');
        }
    } catch (error) {
        console.error("Password reset fetch error:", error);
        showFlashMessage("Network error during password reset. Please ensure you are connected to the server.", "error", 'dashboardFlashContainer');
    }
}

/**
 * Handles the "Add New User" form submission.
 * Validates inputs, sends data to the backend, and updates the UI.
 */
export async function handleAddUser(e) {
    e.preventDefault();
    console.log("Add User form submitted.");

    const newUsernameInput = document.getElementById('newUsername');
    const newUserPasswordInput = document.getElementById('newUserPassword');
    const confirmNewUserPasswordInput = document.getElementById('confirmNewUserPassword');
    const newUserRoleSelect = document.getElementById('newUserRole');

    if (!newUsernameInput || !newUserPasswordInput || !confirmNewUserPasswordInput || !newUserRoleSelect) {
        console.error("Missing input elements in the add user form.");
        showFlashMessage("An internal error occurred: Add user fields not found.", "error", 'dashboardFlashContainer');
        return;
    }

    if (newUserPasswordInput.value.length < 8) {
        showFlashMessage("Password must be at least 8 characters long for security.", "error", 'dashboardFlashContainer');
        return;
    }
    if (newUserPasswordInput.value !== confirmNewUserPasswordInput.value) {
        showFlashMessage("Passwords do not match. Please re-enter them carefully.", "error", 'dashboardFlashContainer');
        return;
    }

    const formData = new FormData(this);
    try {
        const response = await fetch('/admin/add_user', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();

        if (response.ok && result.status === 'success') {
            showFlashMessage(result.message, "success", 'dashboardFlashContainer');
            this.reset();
            await fetchUsers();
            showUserManagementTab('resetPasswordView');
        } else {
            showFlashMessage(result.message || "Failed to add user.", "error", 'dashboardFlashContainer');
        }
    } catch (error) {
        console.error("Add user fetch error:", error);
        showFlashMessage("Network error during user creation. Please ensure you are connected to the server.", "error", 'dashboardFlashContainer');
    }
}
