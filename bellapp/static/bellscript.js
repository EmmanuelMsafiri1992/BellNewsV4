        // Global variables to store application state and data
        let alarms = []; // Array to store alarm objects fetched from the backend
        let sounds = []; // Array to store available sound file names
        // These variables are initialized from hidden inputs rendered by Flask, providing initial state
        let currentUserRole = document.getElementById('currentUserRoleInput') ? document.getElementById('currentUserRoleInput').value : 'guest';
        let currentUserFeaturesActivated = document.getElementById('currentUserFeaturesActivatedInput') ? JSON.parse(document.getElementById('currentUserFeaturesActivatedInput').value) : false;
        let licenseInfo = {}; // Object to store system-wide license details, fetched via API
        let systemSettings = {}; // Object to store system settings (network, time, etc.), fetched via API

        // --- Authentication & Page Navigation Functions ---

        /**
         * Displays the login page and hides the dashboard.
         */
        function showLogin() {
            document.getElementById('loginPage').style.display = 'flex'; // Use flex to center login card
            document.getElementById('dashboardPage').style.display = 'none';
        }

        /**
         * Displays the dashboard and hides the login page.
         * Calls the `init()` function to load and update dashboard content.
         */
        function showDashboard() {
            document.getElementById('loginPage').style.display = 'none';
            document.getElementById('dashboardPage').style.display = 'block';
            init(); // Initialize dashboard components and fetch data when shown
        }

        /**
         * Event listener for the login form submission.
         * Prevents default form submission, handles AJAX login, and updates UI based on response.
         */
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault(); // Prevent default form submission
            console.log("Login form submitted."); // Debug log
            const loginBtn = document.getElementById('loginBtn');
            const btnIcon = loginBtn ? loginBtn.querySelector('i') : null;

            // Show loading state on the button
            if (btnIcon) {
                btnIcon.className = 'fas fa-spinner fa-spin mr-2'; // Spinner icon
                loginBtn.textContent = 'Authenticating...'; // Update button text
            }
            if (loginBtn) loginBtn.disabled = true; // Disable button to prevent multiple submissions

            const formData = new FormData(this); // Moved formData definition here

            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    body: formData
                });
                console.log("Login Response Status:", response.status); // Debug log
                
                // If Flask redirects, let the browser handle it.
                if (response.redirected) {
                    console.log("Login: Backend initiated redirect. Navigating to:", response.url);
                    window.location.href = response.url;
                    // Important: Code after window.location.href might not execute due to navigation.
                    return; // Exit function early as browser will navigate.
                } else {
                    // If not redirected, it means Flask returned an HTML response (e.g., with flash messages)
                    // or a JSON response. Try JSON first.
                    let result;
                    let isJson = false;
                    try {
                        result = await response.json();
                        isJson = true;
                        console.log("Login: Parsed JSON response:", result); // Debug log for JSON
                    } catch (jsonError) {
                        // Not JSON, so it must be HTML
                        const html = await response.text();
                        console.log("Login: Parsed HTML body for debugging:", html); // Log the raw HTML response
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');
                        
                        let messageDisplayed = false;
                        // Look for common Flask flash message patterns (e.g., ul.flashes li)
                        const flaskFlashList = doc.querySelector('ul.flashes');
                        if (flaskFlashList) {
                            const messages = Array.from(flaskFlashList.children); // Get all li elements
                            if (messages.length > 0) { // Only iterate if messages exist
                                messages.forEach(msgElement => {
                                    const message = msgElement.textContent.trim();
                                    let type = 'info'; // Default type
                                    if (msgElement.classList.contains('success')) type = 'success';
                                    else if (msgElement.classList.contains('error')) type = 'error';
                                    else if (msgElement.classList.contains('warning')) type = 'warning';
                                    else if (msgElement.classList.contains('info')) type = 'info';
                                    
                                    // Call our custom flash message display function
                                    // For HTML-based flash messages on login, we still auto-hide as they are usually for general info
                                    showFlashMessage(message, type, 'loginFlashContainer', true); 
                                    messageDisplayed = true;
                                });
                            }
                        } 
                        
                        // Fallback for generic login failure if no specific Flask flash message was found
                        if (!messageDisplayed) {
                            // If Flask didn't redirect, and didn't provide a specific flash message,
                            // assume it's a generic login failure.
                            showFlashMessage("Login failed. Please check your username and password.", "error", 'loginFlashContainer', false); // Keep this persistent
                        }
                        console.log("Login: Backend did not redirect. Displaying flash message from HTML.");
                    }

                    if (isJson) {
                        if (result.status === 'success' && result.redirect_url) {
                            console.log("Login: JSON success with redirect. Navigating to:", result.redirect_url);
                            window.location.href = result.redirect_url;
                        } else if (result.status === 'error' && result.message) {
                            // For JSON errors on login, make the message persistent
                            showFlashMessage(result.message, "error", 'loginFlashContainer', false); 
                            console.log("Login: JSON error. Displaying flash message.");
                        } else {
                            // Generic JSON response, not handled specifically, make it persistent
                            showFlashMessage("Login failed due to an unexpected server response.", "error", 'loginFlashContainer', false);
                            console.error("Login: Unexpected JSON response structure.", result);
                        }
                    }
                }
            } catch (error) {
                console.error("Login fetch error:", error);
                if (error.message.includes("too many redirects")) {
                    showFlashMessage("Network error: Too many redirects. Please check server configuration.", "error", 'loginFlashContainer', false); // Persistent
                } else {
                    showFlashMessage("Network error during login attempt. Please check your connection and try again.", "error", 'loginFlashContainer', false); // Persistent
                }
            } finally {
                // Always reset button state
                if (loginBtn) {
                    if (btnIcon) {
                        btnIcon.className = 'fas fa-sign-in-alt mr-2';
                    }
                    loginBtn.textContent = 'Sign In';
                    loginBtn.disabled = false;
                    console.log("Login button state reset.");
                }
            }
        });

        /**
         * Logs out the current user by sending a POST request to the logout endpoint.
         * Redirects to the login page on success.
         */
        async function logout() {
            showFlashMessage("Logging out of the system...", "info", 'dashboardFlashContainer'); // Pass container ID
            try {
                const response = await fetch('/logout', { method: 'POST' });
                if (response.redirected) {
                    window.location.href = response.url; // Follow Flask's redirect
                } else {
                    // Fallback in case Flask doesn't redirect or there's an issue
                    showLogin(); // Force show login page
                    showFlashMessage("You have been successfully logged out.", "success", 'loginFlashContainer'); // Pass container ID
                }
            } catch (error) {
                console.error("Logout fetch error:", error);
                showFlashMessage("Network error occurred during logout. Please try again.", "error", 'dashboardFlashContainer'); // Pass container ID
                showLogin(); // Ensure login page is shown even on network error
            }
        }

        /**
         * Opens the change password modal.
         */
        function showChangePassword() {
            openModal('changePasswordModal');
        }

        /**
         * Event listener for the change password form submission.
         * Validates new passwords, sends to backend, and handles UI updates.
         */
        document.getElementById('changePasswordForm').addEventListener('submit', async function(e) {
            e.preventDefault(); // Prevent default form submission
            console.log("Change Password form submitted."); // Debug log
            const currentPasswordInput = document.getElementById('currentPassword');
            const newPasswordInput = document.getElementById('newPassword');
            const confirmPasswordInput = document.getElementById('confirmPassword');

            // Basic client-side validation for password fields
            if (!currentPasswordInput || !newPasswordInput || !confirmPasswordInput) {
                console.error("Missing password input elements in the form.");
                showFlashMessage("An internal error occurred: Password fields not found.", "error", 'dashboardFlashContainer'); // Pass container ID
                return;
            }

            if (newPasswordInput.value.length < 8) {
                showFlashMessage("New password must be at least 8 characters long for security.", "error", 'dashboardFlashContainer'); // Pass container ID
                return;
            }
            if (newPasswordInput.value !== confirmPasswordInput.value) {
                showFlashMessage("New passwords do not match. Please re-enter them carefully.", "error", 'dashboardFlashContainer'); // Pass container ID
                return;
            }

            const formData = new FormData(this); // Get form data
            try {
                const response = await fetch('/change_password', {
                    method: 'POST',
                    body: formData
                });
                console.log("Change Password Response Status:", response.status); // Debug log
                const html = await response.text(); // Get the HTML response (expected to contain flash messages)
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newFlashMessagesContainer = doc.getElementById('dashboardFlashMessages'); // Target dashboard container
                
                if (newFlashMessagesContainer) {
                    const flaskGeneratedMessages = Array.from(newFlashMessagesContainer.querySelectorAll('ul.flashes li')); // More robust selection
                    flaskGeneratedMessages.forEach(msgElement => {
                        const message = msgElement.textContent.trim();
                        let type = 'info'; 
                        if (msgElement.classList.contains('success')) type = 'success';
                        else if (msgElement.classList.contains('error')) type = 'error';
                        else if (msgElement.classList.contains('warning')) type = 'warning';
                        else if (msgElement.classList.contains('info')) type = 'info';
                        showFlashMessage(message, type, 'dashboardFlashContainer'); // Use the specific dashboard container
                    });
                }
                // Handle Flask's redirect or successful response
                if (response.redirected) {
                    window.location.href = response.url;
                } else if (response.ok) { // If response is OK (e.g., 200) and no redirect happened
                    closeModal('changePasswordModal'); // Close modal on success
                    this.reset(); // Clear form fields
                } else {
                    showFlashMessage("Failed to change password. Please check your current password and try again.", "error", 'dashboardFlashContainer'); // Pass container ID
                }
            } catch (error) {
                console.error("Password change fetch error:", error);
                showFlashMessage("Network error during password change. Please ensure you are connected to the server.", "error", 'dashboardFlashContainer'); // Pass container ID
            }
        }); 

        /**
         * Event listener for the superadmin password reset form submission.
         * Validates new passwords, sends to backend, and handles UI updates.
         */
        document.getElementById('resetPasswordForm').addEventListener('submit', async function(e) {
            e.preventDefault(); // Prevent default form submission
            console.log("Reset Password form submitted by superadmin."); // Debug log
            const resetUsernameInput = document.getElementById('resetUsername');
            const resetNewPasswordInput = document.getElementById('resetNewPassword');
            const resetConfirmPasswordInput = document.getElementById('resetConfirmPassword');

            if (!resetUsernameInput || !resetNewPasswordInput || !resetConfirmPasswordInput) {
                console.error("Missing input elements in the reset password form.");
                showFlashMessage("An internal error occurred: Reset password fields not found.", "error", 'dashboardFlashContainer'); // Pass container ID
                return;
            }

            if (resetNewPasswordInput.value.length < 8) {
                showFlashMessage("New password must be at least 8 characters long for security.", "error", 'dashboardFlashContainer'); // Pass container ID
                return;
            }
            if (resetNewPasswordInput.value !== resetConfirmPasswordInput.value) {
                showFlashMessage("New passwords do not match. Please re-enter them carefully.", "error", 'dashboardFlashContainer'); // Pass container ID
                return;
            }

            const formData = new FormData(this); // Get form data
            try {
                const response = await fetch('/admin/reset_password', {
                    method: 'POST',
                    body: formData
                });
                console.log("Reset Password Response Status:", response.status); // Debug log
                const result = await response.json(); // Expect JSON response

                if (result.status === 'success') {
                    showFlashMessage(result.message, "success", 'dashboardFlashContainer'); // Pass container ID
                    closeModal('resetPasswordModal'); // Close modal on success
                    this.reset(); // Clear form fields
                } else {
                    // Display error message from backend
                    showFlashMessage(result.message, "error", 'dashboardFlashContainer'); // Pass container ID
                }
            } catch (error) {
                console.error("Password reset fetch error:", error);
                showFlashMessage("Network error during password reset. Please ensure you are connected to the server.", "error", 'dashboardFlashContainer'); // Pass container ID
            }
        });

        /**
         * Fetches the list of users from the backend and populates the dropdown
         * in the reset password form.
         */
        async function fetchUsers() {
            const resetUsernameSelect = document.getElementById('resetUsername');
            if (!resetUsernameSelect) {
                console.error("User select dropdown not found.");
                return;
            }
            resetUsernameSelect.innerHTML = '<option value="">Loading users...</option>'; // Show loading state

            try {
                const response = await fetch('/api/users');
                const data = await response.json();

                if (response.ok && data.users) {
                    resetUsernameSelect.innerHTML = '<option value="">Select a user</option>'; // Default option
                    data.users.forEach(user => {
                        const option = document.createElement('option');
                        option.value = user.username;
                        option.textContent = `${user.username} (${user.role})`;
                        resetUsernameSelect.appendChild(option);
                    });
                    console.log("Users fetched and populated:", data.users);
                } else {
                    showFlashMessage(data.message || 'Failed to load users.', 'error', 'dashboardFlashContainer'); // Pass container ID
                    resetUsernameSelect.innerHTML = '<option value="">Failed to load users</option>';
                    console.error("Failed to fetch users:", data.message);
                }
            } catch (error) {
                console.error("Network error fetching users:", error);
                showFlashMessage('An error occurred while fetching users.', "error", 'dashboardFlashContainer'); // Pass container ID
                resetUsernameSelect.innerHTML = '<option value="">Network error</option>';
            }
        }

        /**
         * Manages the tabbed interface within the User Management Modal (Reset Password/Add User).
         * Activates the selected tab and hides others.
         * @param {string} tabId - The ID of the tab content to display ('resetPasswordView' or 'addUserView').
         */
        function showUserManagementTab(tabId) {
            const tabs = document.querySelectorAll('#resetPasswordModal .tab-content');
            const buttons = document.querySelectorAll('#resetPasswordModal .tab-button');

            tabs.forEach(tab => tab.classList.add('hidden')); // Hide all tab contents
            buttons.forEach(button => button.classList.remove('active')); // Deactivate all tab buttons

            const targetTab = document.getElementById(tabId);
            const targetButton = document.getElementById(tabId.replace('View', 'TabBtn')); // Get corresponding button ID

            if (targetTab) targetTab.classList.remove('hidden'); // Show target tab
            if (targetButton) targetButton.classList.add('active'); // Activate target button

            // If switching to reset password, re-fetch users
            if (tabId === 'resetPasswordView') {
                fetchUsers();
            }
        }

        /**
         * Displays the User Management Modal (for superusers), defaulting to the Reset Password view.
         * Fetches the list of users when opened.
         */
        async function showResetPasswordModal() {
            console.log("Showing User Management modal for superuser."); // Debugging
            openModal('resetPasswordModal');
            await fetchUsers(); // Fetch users when the modal is opened
            showUserManagementTab('resetPasswordView'); // Default to Reset Password view
        }

        // --- System Settings Functions ---

        /**
         * Opens the system settings modal and fetches/populates current settings from the backend.
         */
        async function showSettings() {
            try {
                const response = await fetch('/api/system_settings');
                const data = await response.json();
                if (data.status === 'error') {
                    showFlashMessage(data.message, 'error', 'dashboardFlashContainer'); // Pass container ID
                    return;
                }
                systemSettings = data; // Update global systemSettings object
                console.log("Fetched System Settings:", systemSettings);

                // Populate Network Settings fields
                const dynamicIpRadio = document.getElementById('dynamicIp');
                const staticIpRadio = document.getElementById('staticIp');

                if (dynamicIpRadio && staticIpRadio) {
                    if (systemSettings.networkSettings.ipType === 'static') {
                        staticIpRadio.checked = true;
                    } else {
                        dynamicIpRadio.checked = true;
                    }
                }
                // Call toggleStaticIpFields *after* setting the checked state
                toggleStaticIpFields(); // Show/hide static IP fields based on selection

                const ipAddressElem = document.getElementById('ipAddress');
                const subnetMaskElem = document.getElementById('subnetMask');
                const gatewayElem = document.getElementById('gateway');
                const dnsServerElem = document.getElementById('dnsServer');

                if (ipAddressElem) ipAddressElem.value = systemSettings.networkSettings.ipAddress || '';
                if (subnetMaskElem) subnetMaskElem.value = systemSettings.networkSettings.subnetMask || '';
                if (gatewayElem) gatewayElem.value = systemSettings.networkSettings.gateway || '';
                if (dnsServerElem) dnsServerElem.value = systemSettings.networkSettings.dnsServer || '';

                openModal('settingsModal');
            } catch (error) {
                console.error("Error fetching system settings:", error);
                showFlashMessage("Failed to load system settings. " + error.message, "error", 'dashboardFlashContainer'); // Pass container ID
            }
        } 

        /**
         * Event listener for the settings form submission.
         * Gathers data, performs client-side validation, and sends updates to the backend.
         */
        document.getElementById('settingsForm').addEventListener('submit', async function(e) {
            e.preventDefault(); // Prevent default form submission
            console.log("Settings form submitted."); // Debug log

            const updatedSettings = {
                networkSettings: {},
                timeSettings: {},
                API_SERVICE_URL: systemSettings.API_SERVICE_URL // Retain existing API URL
            };

            // Gather Network Settings from the form
            const selectedIpType = document.querySelector('input[name="ipType"]:checked');
            updatedSettings.networkSettings.ipType = selectedIpType ? selectedIpType.value : 'dynamic';
            
            if (updatedSettings.networkSettings.ipType === 'static') {
                const ipAddress = document.getElementById('ipAddress');
                const subnetMask = document.getElementById('subnetMask');
                const gateway = document.getElementById('gateway');
                const dnsServer = document.getElementById('dnsServer');

                const ipAddressValue = ipAddress ? ipAddress.value : '';
                const subnetMaskValue = subnetMask ? subnetMask.value : '';
                const gatewayValue = gateway ? gateway.value : '';
                const dnsServerValue = dnsServer ? dnsServer.value : '';

                // Regular expression for basic IPv4 validation
                const ipRegex = /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
                if (!ipRegex.test(ipAddressValue) || !ipRegex.test(subnetMaskValue) || !ipRegex.test(gatewayValue) || (dnsServerValue && !ipRegex.test(dnsServerValue))) {
                    showFlashMessage("Please enter valid IPv4 addresses for static IP configuration.", "error", 'dashboardFlashContainer'); // Pass container ID
                    return;
                }
                updatedSettings.networkSettings.ipAddress = ipAddressValue;
                updatedSettings.networkSettings.subnetMask = subnetMaskValue;
                updatedSettings.networkSettings.gateway = gatewayValue;
                updatedSettings.networkSettings.dnsServer = dnsServerValue;
            } else {
                // Clear static IP fields if dynamic is selected
                updatedSettings.networkSettings.ipAddress = '';
                updatedSettings.networkSettings.subnetMask = '';
                updatedSettings.networkSettings.gateway = '';
                updatedSettings.networkSettings.dnsServer = '';
            }

            // Gather Time Settings from the form
            const selectedTimeType = document.querySelector('.toggle-option.active');
            updatedSettings.timeSettings.timeType = selectedTimeType ? selectedTimeType.dataset.timeType : 'ntp';
            
            if (updatedSettings.timeSettings.timeType === 'ntp') {
                const ntpServer = document.getElementById('ntpServer');
                updatedSettings.timeSettings.ntpServer = ntpServer ? ntpServer.value : '';
                updatedSettings.timeSettings.manualDate = '';
                updatedSettings.timeSettings.manualTime = '';
            } else { // Manual time setting
                const manualDate = document.getElementById('manualDate');
                const manualTime = document.getElementById('manualTime');
                updatedSettings.timeSettings.ntpServer = '';
                updatedSettings.timeSettings.manualDate = manualDate ? manualDate.value : '';
                updatedSettings.timeSettings.manualTime = manualTime ? manualTime.value : '';
                if (!updatedSettings.timeSettings.manualDate || !updatedSettings.timeSettings.manualTime) {
                    showFlashMessage("Please enter both manual date and time for manual time setting.", "error", 'dashboardFlashContainer'); // Pass container ID
                    return;
                }
            }

            console.log("Sending updated settings:", updatedSettings); // Debug log

            try {
                const response = await fetch('/api/system_settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updatedSettings)
                });
                const result = await response.json();
                console.log("Settings Save Response:", result); // Debug log
                if (result.status === 'success') {
                    showFlashMessage(result.message, "success", 'dashboardFlashContainer'); // Pass container ID
                    closeModal('settingsModal');
                    // Re-fetch all system settings to ensure UI is in sync after saving
                    await fetchSystemSettingsAndUpdateUI();
                } else {
                    showFlashMessage(result.message, "error", 'dashboardFlashContainer'); // Pass container ID
                }
            } catch (error) {
                console.error("Error saving system settings:", error);
                showFlashMessage("Network error saving settings. " + error.message, "error", 'dashboardFlashContainer'); // Pass container ID
            }
        });

        /**
         * Toggles the visibility and required attributes for static IP input fields
         * based on the selected IP configuration type (Dynamic/Static).
         */
        function toggleStaticIpFields() {
            const staticIpRadio = document.getElementById('staticIp');
            const staticIpFields = document.getElementById('staticIpFields');
            const ipAddressInput = document.getElementById('ipAddress');
            const subnetMaskInput = document.getElementById('subnetMask');
            const gatewayInput = document.getElementById('gateway');

            // Ensure all relevant elements exist before attempting to manipulate them.
            if (!staticIpRadio || !staticIpFields || !ipAddressInput || !subnetMaskInput || !gatewayInput) {
                console.warn("Missing elements for toggleStaticIpFields. Skipping execution.");
                return;
            }

            if (staticIpRadio.checked) {
                staticIpFields.classList.remove('hidden');
                ipAddressInput.setAttribute('required', 'required');
                subnetMaskInput.setAttribute('required', 'required');
                gatewayInput.setAttribute('required', 'required');
            } else {
                staticIpFields.classList.add('hidden');
                ipAddressInput.removeAttribute('required');
                subnetMaskInput.removeAttribute('required');
                gatewayInput.removeAttribute('required');
            }
        }

        /**
         * Toggles between NTP server and Manual time setting options in the settings modal.
         * Updates active class for buttons and shows/hides relevant input fields.
         * @param {string} type - The type of time setting to activate ('ntp' or 'manual').
         */
        function selectTimeType(type) {
            const ntpOption = document.getElementById('ntpOption');
            const manualOption = document.getElementById('manualOption');
            const ntpSettingsFields = document.getElementById('ntpSettingsFields');
            const manualTimeFields = document.getElementById('manualTimeFields');
            const manualDateInput = document.getElementById('manualDate');
            const manualTimeInput = document.getElementById('manualTime');

            // Ensure all elements exist for robust operation.
            if (!ntpOption || !manualOption || !ntpSettingsFields || !manualTimeFields || !manualDateInput || !manualTimeInput) {
                console.warn("Missing elements for selectTimeType. Skipping function.");
                return;
            }

            // Remove active class from both options initially
            ntpOption.classList.remove('active');
            manualOption.classList.remove('active');

            if (type === 'ntp') {
                ntpOption.classList.add('active');
                ntpSettingsFields.classList.remove('hidden');
                manualTimeFields.classList.add('hidden');
                manualDateInput.removeAttribute('required'); // Remove required for manual fields
                manualTimeInput.removeAttribute('required');
            } else { // type === 'manual'
                manualOption.classList.add('active');
                ntpSettingsFields.classList.add('hidden');
                manualTimeFields.classList.remove('hidden');
                manualDateInput.setAttribute('required', 'required'); // Add required for manual fields
                manualTimeInput.setAttribute('required', 'required');
            }
        }


        // --- License Management Functions ---

        /**
         * Opens the license management modal.
         * Populates the system license fields and conditionally fetches/renders licensed users for superusers.
         * Also controls the visibility of 'Generate New Key' and 'Licensed Users' tab based on user role.
         */
        async function showLicenseManagement() {
            const licenseKeyElem = document.getElementById('licenseKey');
            const licenseExpiryElem = document.getElementById('licenseExpiry');
            const generateKeyBtn = document.getElementById('generateKeyBtn');
            const validateLicenseBtn = document.getElementById('validateLicenseBtn');
            const licensedUsersTabBtn = document.getElementById('licensedUsersTabBtn');

            // Robust null checks for critical elements.
            if (!licenseKeyElem || !licenseExpiryElem || !generateKeyBtn || !validateLicenseBtn || !licensedUsersTabBtn) {
                console.warn("One or more critical license management elements not found. Cannot show license management modal.");
                return;
            }

            // Populate current system-wide license info
            licenseKeyElem.value = licenseInfo.key || '';
            // datetime-local input needs ISO format YYYY-MM-DDTHH:MM, so substring the ISO string
            licenseExpiryElem.value = licenseInfo.expiry ? licenseInfo.expiry.substring(0, 16) : '';
            
            // Conditional visibility for superuser-only elements
            if (currentUserRole === 'superuser') {
                generateKeyBtn.classList.remove('hidden');
                validateLicenseBtn.classList.remove('hidden');
                licensedUsersTabBtn.classList.remove('hidden'); // Show the "Licensed Users" tab button
                await fetchAndRenderLicensedUsers(); // Fetch and render data for this tab
            } else {
                generateKeyBtn.classList.add('hidden');
                validateLicenseBtn.classList.add('hidden');
                licensedUsersTabBtn.classList.add('hidden'); // Hide the "Licensed Users" tab button for non-superusers
            }

            openModal('licenseModal');
            openLicenseTab('manageLicense'); // Always default to the "Manage System License" tab on opening.
        }

        /**
         * Sends a request to the backend to generate a new system-wide license key (UUID).
         * Updates the license key input field with the newly generated key.
         */
        async function generateLicenseKey() {
            try {
                const response = await fetch('/api/generate_license_key');
                const result = await response.json();
                if (result.status === 'success') {
                    const licenseKeyElem = document.getElementById('licenseKey');
                    if (licenseKeyElem) licenseKeyElem.value = result.licenseKey; // Update input field
                    showFlashMessage("New system license key generated successfully.", "info", 'dashboardFlashContainer'); // Pass container ID
                } else {
                    showFlashMessage(result.message, "error", 'dashboardFlashContainer'); // Pass container ID
                }
            } catch (error) {
                console.error("Error generating license key:", error);
                showFlashMessage("Network error generating license key. " + error.message, "error", 'dashboardFlashContainer'); // Pass container ID
            }
        }

        /**
         * Event listener for the system license validation form submission.
         * Sends the license key and expiry date to the backend for validation and application.
         */
        document.getElementById('licenseForm').addEventListener('submit', async function(e) {
            e.preventDefault(); // Prevent default form submission
            console.log("License form submitted."); // Debug log
            const licenseKeyElem = document.getElementById('licenseKey');
            const licenseExpiryElem = document.getElementById('licenseExpiry');

            const licenseKey = licenseKeyElem ? licenseKeyElem.value : '';
            const fullExpiry = licenseExpiryElem ? `${licenseExpiryElem.value}:00` : ''; // YYYY-MM-DDTHH:MM:SS

            console.log("Sending license data:", { licenseKey: licenseKey, expiryDate: fullExpiry }); // Debug log

            try {
                const response = await fetch('/api/license', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ licenseKey: licenseKey, expiryDate: fullExpiry })
                });
                const result = await response.json();
                console.log("License Validation Response:", result); // Debug log
                if (result.status === 'success') {
                    showFlashMessage(result.message, "success", 'dashboardFlashContainer'); // Pass container ID
                    licenseInfo = result.licenseInfo; // Update global system license info
                    await fetchSystemSettingsAndUpdateUI(); // Re-fetch all settings to update UI based on new license status
                    closeModal('licenseModal'); // Close modal on success
                } else {
                    showFlashMessage(result.message, "error", 'dashboardFlashContainer'); // Pass container ID
                }
            } catch (error) {
                console.error("Error validating license:", error);
                showFlashMessage("Network error validating license. " + error.message, "error", 'dashboardFlashContainer'); // Pass container ID
            }
        });

        /**
         * Updates the UI elements displaying the system-wide license status and expiry date.
         */
        function updateLicenseUI() {
            const statusBadge = document.getElementById('licenseStatusBadge');
            const expiryDateElem = document.getElementById('licenseExpiryDate');

            if (!statusBadge || !expiryDateElem) {
                console.warn("License UI elements not found. Skipping updateLicenseUI.");
                return;
            }

            if (!licenseInfo || !licenseInfo.status) {
                statusBadge.textContent = "Unknown";
                statusBadge.className = `license-status-badge unlicensed`; // Default to unlicensed if no info
                expiryDateElem.textContent = 'N/A';
                return;
            }

            statusBadge.textContent = licenseInfo.status.replace(/_/g, ' '); // Format status for display (e.g., "invalid_format" to "invalid format")
            statusBadge.className = `license-status-badge ${licenseInfo.status}`; // Apply dynamic class for styling

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
        async function checkUserRoleAndFeatureActivation() {
            const resetPasswordBtn = document.getElementById('resetPasswordBtn'); // Get the button element
            const licenseBtn = document.getElementById('licenseManagementBtn'); // Header button for license modal
            const addAlarmBtn = document.getElementById('addAlarmBtn'); // Add new alarm button
            const uploadSoundBtn = document.getElementById('uploadSoundBtn'); // Upload sound button
            const featureActivationCard = document.getElementById('featureActivationCard'); // Admin feature activation card
            const generateKeyBtn = document.getElementById('generateKeyBtn'); // Generate key button in license modal
            const validateLicenseBtn = document.getElementById('validateLicenseBtn'); // Validate license button in license modal
            const licensedUsersTabBtn = document.getElementById('licensedUsersTabBtn'); // "Licensed Users" tab button

            // Perform robust null checks for all critical UI elements.
            const elements = { licenseBtn, addAlarmBtn, uploadSoundBtn, featureActivationCard, generateKeyBtn, validateLicenseBtn, licensedUsersTabBtn };
            for (const key in elements) {
                if (!elements[key]) {
                    console.warn(`UI element '${key}' not found during permission check.`);
                }
            }

            // --- Superuser Permissions ---
            if (currentUserRole === "superuser") {
                if (licenseBtn) licenseBtn.classList.remove('hidden'); // Superusers can access license management
                if (addAlarmBtn) addAlarmBtn.disabled = false; // Superusers can always add alarms
                if (uploadSoundBtn) uploadSoundBtn.disabled = false; // Superusers can always upload sounds
                if (featureActivationCard) featureActivationCard.classList.add('hidden'); // Superuser doesn't need to activate features for themselves
                if (generateKeyBtn) generateKeyBtn.classList.remove('hidden'); // Superuser can generate license keys
                if (validateLicenseBtn) validateLicenseBtn.classList.remove('hidden'); // Superuser can validate system license
                if (licensedUsersTabBtn) licensedUsersTabBtn.classList.remove('hidden'); // Superuser can see licensed users tab
                
            }
            // --- Admin Permissions ---
            else if (currentUserRole === "admin") {
                if (licenseBtn) licenseBtn.classList.add('hidden'); // Admins cannot access system license management
                if (generateKeyBtn) generateKeyBtn.classList.add('hidden'); // Admins cannot generate license keys
                if (validateLicenseBtn) validateLicenseBtn.classList.add('hidden'); // Admins cannot validate system license
                if (licensedUsersTabBtn) licensedUsersTabBtn.classList.add('hidden'); // Admins cannot see licensed users tab

                // Conditional logic for admin features based on system license and individual activation
                if (licenseInfo.status === 'active' && !currentUserFeaturesActivated) {
                    // System license is active, but this admin's features are not yet activated
                    if (featureActivationCard) featureActivationCard.classList.remove('hidden'); // Show the activation card
                    if (addAlarmBtn) addAlarmBtn.disabled = true; // Disable alarm adding
                    if (uploadSoundBtn) uploadSoundBtn.disabled = true; // Disable sound uploading
                }
                else if (licenseInfo.status === 'active' && currentUserFeaturesActivated) {
                    // System license is active AND this admin's features ARE activated
                    if (featureActivationCard) featureActivationCard.classList.add('hidden'); // Hide the activation card
                    if (addAlarmBtn) addAlarmBtn.disabled = false; // Enable alarm adding
                    if (uploadSoundBtn) uploadSoundBtn.disabled = false; // Enable sound uploading
                }
                else {
                    // System license is NOT active (unlicensed, expired, invalid) for admin
                    if (featureActivationCard) featureActivationCard.classList.add('hidden'); // Hide activation card if no active system license
                    if (addAlarmBtn) addAlarmBtn.disabled = true; // Disable alarm adding
                    if (uploadSoundBtn) uploadSoundBtn.disabled = true; // Disable sound uploading
                    
                    // Explicitly show the license message if the system license is not active for an "admin"
                    // This message should only be shown if they are indeed an admin trying to log in
                    if (currentUserRole === 'admin') { // Added check for current user role
                        // ONLY show this message if the user is an "admin" AND the license is NOT active.
                        // This message should NOT persist if the license becomes active.
                        showFlashMessage("System is not yet licensed or license expired, please contact your superadmin for the license.", "error", 'dashboardFlashContainer');
                    }
                }
            }
            // --- Other Roles (e.g., guest) ---
            else {
                // Hide all privileged features for unauthenticated or non-admin/superuser roles
                if (licenseBtn) licenseBtn.classList.add('hidden');
                if (featureActivationCard) featureActivationCard.classList.add('hidden');
                if (addAlarmBtn) addAlarmBtn.disabled = true;
                if (uploadSoundBtn) uploadSoundBtn.disabled = true;
                if (generateKeyBtn) generateKeyBtn.classList.add('hidden');
                if (validateLicenseBtn) validateLicenseBtn.classList.add('hidden');
                if (licensedUsersTabBtn) licensedUsersTabBtn.classList.add('hidden');
            }
                // NEW: Toggle visibility for Reset Password Button for Superusers
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
        async function activateFeatures() {
            try {
                const response = await fetch('/activate_features', { method: 'POST' });
                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newFlashMessagesContainer = doc.getElementById('dashboardFlashMessages'); // Target dashboard container
                
                if (newFlashMessagesContainer) {
                    const flaskGeneratedMessages = Array.from(newFlashMessagesContainer.querySelectorAll('ul.flashes li')); // More robust selection
                    flaskGeneratedMessages.forEach(msgElement => {
                        const message = msgElement.textContent.trim();
                        let type = 'info'; 
                        if (msgElement.classList.contains('success')) type = 'success';
                        else if (msgElement.classList.contains('error')) type = 'error';
                        else if (msgElement.classList.contains('warning')) type = 'warning';
                        else if (msgElement.classList.contains('info')) type = 'info';
                        showFlashMessage(message, type, 'dashboardFlashContainer'); // Use the specific dashboard container
                    });
                }
                if (response.redirected) {
                    window.location.href = response.url; // Follow Flask's redirect
                } else if (response.ok) {
                    // If successful (and no redirect), refresh UI elements to reflect activated features
                    await fetchSystemSettingsAndUpdateUI(); // This will re-fetch data and re-evaluate permissions
                }
            } catch (error) {
                console.error("Error activating features:", error);
                showFlashMessage("Network error during feature activation. " + error.message, "error", 'dashboardFlashContainer'); // Pass container ID
            }
        }

        /**
         * Manages the tabbed interface within the License Management Modal.
         * Activates the selected tab and hides others.
         * @param {string} tabId - The ID of the tab content to display (e.g., 'manageLicense', 'licensedUsers').
         */
        function openLicenseTab(tabId) {
            const tabs = document.querySelectorAll('.tab-content');
            const buttons = document.querySelectorAll('.tab-button');

            // Hide all tab contents and deactivate all tab buttons initially
            tabs.forEach(tab => tab.classList.remove('active'));
            buttons.forEach(button => button.classList.remove('active'));

            const targetTab = document.getElementById(tabId);
            const targetButton = document.querySelector(`.tab-button[onclick="openLicenseTab('${tabId}')"]`);

            // Activate the selected tab and its corresponding button
            if (targetTab) targetTab.classList.add('active');
            if (targetButton) targetButton.classList.add('active');

            // Prevent non-superusers from accessing the 'licensedUsers' tab content directly
            if (tabId === 'licensedUsers' && currentUserRole !== 'superuser') {
                // If an admin somehow tries to access this tab, revert to 'manageLicense' tab
                if (document.getElementById('manageLicense')) {
                    document.getElementById('manageLicense').classList.add('active');
                }
                if (document.querySelector('.tab-button[onclick="openLicenseTab(\'manageLicense\')"]')) {
                    document.querySelector('.tab-button[onclick="openLicenseTab(\'manageLicense\')"]').classList.add('active');
                }
                showFlashMessage("You do not have permission to view licensed users. Only superusers can access this information.", "error", 'dashboardFlashContainer'); // Pass container ID
            }
        }

        /**
         * Fetches the list of individually licensed users from the backend
         * and renders them into the 'Licensed Users' table.
         * Only accessible by superusers.
         */
        async function fetchAndRenderLicensedUsers() {
            const tbody = document.getElementById('licensedUsersTableBody');
            const noUsersDiv = document.getElementById('noLicensedUsers');

            if (!tbody || !noUsersDiv) {
                console.warn("Missing licensed users UI elements (table body or 'no users' div). Skipping fetchAndRenderLicensedUsers.");
                return;
            }

            tbody.innerHTML = ''; // Clear existing table rows
            noUsersDiv.classList.add('hidden'); // Hide the 'no users' message initially

            try {
                const response = await fetch('/api/licensed_users');
                const data = await response.json();

                if (data.status === 'error') {
                    showFlashMessage(data.message, 'error', 'dashboardFlashContainer'); // Pass container ID
                    noUsersDiv.classList.remove('hidden'); // Show 'no users' message or an error message if API failed
                    return;
                }

                const licensedUsers = data.licensedUsers || []; // Get the array of licensed users
                console.log("Fetched licensed users:", licensedUsers); // Debug log

                if (licensedUsers.length === 0) {
                    noUsersDiv.classList.remove('hidden'); // Show message if no users have activated features
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
                showFlashMessage("Failed to load licensed users list. " + error.message, "error", 'dashboardFlashContainer'); // Pass container ID
                noUsersDiv.classList.remove('hidden'); // Show error message on network/fetch failure
            }
        }


        // --- Dashboard Real-time Data Functions ---

        /**
         * Updates the displayed current time and timezone on the dashboard.
         */
        function updateCurrentTime() {
            const currentTimeElement = document.getElementById("currentTime");
            const timezoneElement = document.getElementById("timezone");
            if (currentTimeElement && timezoneElement) {
                const now = new Date();
                currentTimeElement.textContent = now.toLocaleTimeString(); // Display local time
                timezoneElement.textContent = Intl.DateTimeFormat().resolvedOptions().timeZone; // Display local timezone
            }
        }

        /**
         * Fetches system metrics (CPU, memory, uptime) from the backend and updates the dashboard UI.
         */
        async function updateMetrics() {
            try {
                const response = await fetch('/api/metrics');
                const metrics = await response.json();

                if (metrics.error) {
                    console.error("Error fetching metrics:", metrics.error);
                    // Optionally show a flash message here or update UI to show 'N/A'
                    return;
                }

                const cpu = metrics.process.cpu_percent;
                const memory = metrics.process.memory_mb;
                const systemMemory = metrics.system.memory_percent;
                const uptime = metrics.process.uptime;

                // Ensure all elements exist before attempting to update them.
                const cpuBar = document.getElementById("cpuBar");
                const cpuText = document.getElementById("cpuText");
                const memoryText = document.getElementById("memoryText");
                const systemMemoryBar = document.getElementById("systemMemoryBar");
                const systemMemoryText = document.getElementById("systemMemoryText");
                const uptimeText = document.getElementById("uptimeText");

                if (cpuBar) cpuBar.style.width = cpu + "%";
                if (cpuText) cpuText.textContent = cpu.toFixed(1) + "%";
                if (memoryText) memoryText.textContent = memory.toFixed(1) + " MB";
                if (systemMemoryText) systemMemoryText.textContent = systemMemory.toFixed(1) + "%";
                if (systemMemoryBar) systemMemoryBar.style.width = systemMemory + "%";
                if (uptimeText) uptimeText.textContent = uptime;

            } catch (error) {
                console.error("Failed to fetch metrics:", error);
                // Optionally show a flash message about metrics not loading
            }
        }

        /**
         * Fetches the list of available sound files from the backend and populates
         * the sound library list and the sound selection dropdowns in alarm modals.
         */
        async function populateSounds() {
            const soundList = document.getElementById("soundsList");
            const addSoundSelect = document.getElementById("addSound");
            const editSoundSelect = document.getElementById("editSound");
            
            // Robust null checks for sound-related UI elements.
            if (!soundList || !addSoundSelect || !editSoundSelect) {
                console.warn("Missing sound list or sound select elements. Skipping populateSounds.");
                return;
            }

            // Clear existing sound lists and add default option to selects
            soundList.innerHTML = "";
            addSoundSelect.innerHTML = '<option value="">Select a sound</option>';
            editSoundSelect.innerHTML = '<option value="">Select a sound</option>';

            try {
                const response = await fetch('/api/sounds');
                const backendSounds = await response.json();
                sounds = backendSounds.sounds || []; // Update global sounds array
                console.log("Fetched sounds:", sounds); // Debug log

                if (sounds.length === 0) {
                    soundList.innerHTML = '<p class="text-sm text-gray-500 text-center py-4">No sounds uploaded yet. Use the "Upload Sound" button to add some.</p>';
                    // If no sounds, ensure a message is displayed to the user for the dropdowns as well.
                    addSoundSelect.add(new Option("No sounds available - Upload first", "", true, true));
                    editSoundSelect.add(new Option("No sounds available - Upload first", "", true, true));
                    addSoundSelect.disabled = true; // Disable sound selection if no sounds
                    editSoundSelect.disabled = true; // Disable sound selection if no sounds
                } else {
                    addSoundSelect.disabled = false; // Enable sound selection
                    editSoundSelect.disabled = false; // Enable sound selection
                }

                sounds.forEach((sound) => {
                    const div = document.createElement("div");
                    div.className = "flex justify-between items-center bg-gray-50 px-4 py-3 rounded-lg hover:bg-gray-100 transition-colors";
                    div.innerHTML = `
                        <div class="flex items-center gap-3">
                            <i class="fas fa-music text-gray-400"></i>
                            <span class="text-sm font-medium text-gray-700">${sound}</span>
                        </div>
                        <div class="flex gap-2">
                            <button type="button" onclick="testSound('${sound}')" class="text-green-600 hover:text-green-700 text-sm">
                                <i class="fas fa-play mr-1"></i>Test
                            </button>
                            <button type="button" onclick="deleteSound('${sound}')" class="text-red-600 hover:text-red-700 text-sm">
                                <i class="fas fa-trash mr-1"></i>Delete
                            </button>
                        </div>
                    `;
                    soundList.appendChild(div);

                    // Add sound to both add and edit alarm sound dropdowns
                    const optionAdd = document.createElement("option");
                    optionAdd.value = sound;
                    optionAdd.textContent = sound;
                    addSoundSelect.appendChild(optionAdd);

                    const optionEdit = document.createElement("option");
                    optionEdit.value = sound;
                    optionEdit.textContent = sound;
                    editSoundSelect.appendChild(optionEdit);
                });
            } catch (error) {
                console.error("Failed to fetch sounds:", error);
                showFlashMessage("Failed to load sounds for the library. " + error.message, "error", 'dashboardFlashContainer'); // Pass container ID
            }
        }

        /**
         * Plays a specified sound file.
         * @param {string} sound - The filename of the sound to play.
         */
        function testSound(sound) {
            // Use a relative path to the static audio directory
            const audio = new Audio(`./static/audio/${sound}`);
            audio.play().catch(e => {
                console.error("Error playing sound:", e);
                showFlashMessage(`Failed to play sound: ${sound}. Your browser might have blocked autoplay or the file is corrupted.`, "error", 'dashboardFlashContainer'); // Pass container ID
            });
        }

        /**
         * Sends a request to delete a specified sound file.
         * Confirms with the user before proceeding.
         * @param {string} filename - The name of the sound file to delete.
         */
        async function deleteSound(filename) {
            // Using a custom modal/dialog is preferred over `confirm()` for better UX in iframes.
            // For now, retaining confirm as per existing code but noting the preference.
            if (!window.confirm(`Are you sure you want to permanently delete the sound file '${filename}'? This action cannot be undone.`)) {
                return;
            }
            console.log(`Attempting to delete sound: ${filename}`); // Debug log
            try {
                // Flask expects filename as part of the URL path for DELETE, so use POST for browser compatibility.
                const response = await fetch(`/delete_song/${filename}`, {
                    method: 'POST' // Using POST method for delete operation for broad browser compatibility
                });
                console.log("Delete Sound Response Status:", response.status); // Debug log

                if (response.redirected) {
                    window.location.href = response.url; // Follow Flask's redirect
                } else if (response.ok) {
                    // This block should ideally not be hit if Flask redirects for success.
                    // But if it does, it means a 200 OK was returned without a redirect.
                    console.log("Delete Sound: Successful response, refreshing sounds (no redirect)."); // Debug log
                    showFlashMessage("Sound deleted successfully.", "success", 'dashboardFlashContainer'); // Explicitly show message if no redirect
                    populateSounds(); // Refresh the list of sounds after deletion
                }
            } catch (error) {
                console.error("Error deleting sound file:", error);
                showFlashMessage("Network error deleting sound. " + error.message, "error", 'dashboardFlashContainer'); // Pass container ID
            }
        } 

        /**
         * Event listener for the sound file upload form.
         * Handles file selection, validation (size/type), and sends to backend.
         */
        document.getElementById("uploadForm").addEventListener("submit", async function(e) {
            e.preventDefault(); // Prevent default form submission
            console.log("Upload form submitted."); // Debug log
            const fileInput = document.getElementById("fileInput");
            const file = fileInput.files[0]; // Get the selected file

            if (!file) {
                showFlashMessage("Please select an audio file to upload.", "error", 'dashboardFlashContainer'); // Pass container ID
                return;
            }

            // Client-side file size validation
            if (file.size > 2 * 1024 * 1024) { // Max 2MB
                showFlashMessage("The selected file size exceeds the 2MB limit. Please choose a smaller file.", "error", 'dashboardFlashContainer'); // Pass container ID
                return;
            }

            const formData = new FormData();
            formData.append('file', file); // Append file to form data for multipart upload

            console.log("Attempting to upload file:", file.name, "Size:", file.size); // Debug log

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                console.log("Upload Response Status:", response.status); // Debug log
                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newFlashMessagesContainer = doc.getElementById('dashboardFlashMessages'); // Target dashboard container
                
                if (newFlashMessagesContainer) {
                    const flaskGeneratedMessages = Array.from(newFlashMessagesContainer.querySelectorAll('ul.flashes li')); // More robust selection
                    flaskGeneratedMessages.forEach(msgElement => {
                        const message = msgElement.textContent.trim();
                        let type = 'info'; 
                        if (msgElement.classList.contains('success')) type = 'success';
                        else if (msgElement.classList.contains('error')) type = 'error';
                        else if (msgElement.classList.contains('warning')) type = 'warning';
                        else if (msgElement.classList.contains('info')) type = 'info';
                        showFlashMessage(message, type, 'dashboardFlashContainer'); // Use the specific dashboard container
                    });
                }
                
                if (response.redirected) {
                    window.location.href = response.url; // Follow Flask's redirect
                } else if (response.ok) {
                    fileInput.value = ""; // Clear file input field after successful upload
                    populateSounds(); // Refresh the sound library list
                }
            } catch (error) {
                console.error("Error uploading sound file:", error);
                showFlashMessage("Network error during sound upload. " + error.message, "error", 'dashboardFlashContainer'); // Pass container ID
            }
        });

        // --- Alarm Management Functions ---

        /**
         * Event listener for the "Add New Alarm" form submission.
         * Collects alarm data, validates, and sends to the backend via POST request.
         * After successful submission (or redirect), it refreshes the alarm lists.
         */
        document.getElementById("addAlarmForm").addEventListener("submit", async function(e) {
            e.preventDefault(); // Prevent default form submission
            console.log("Add Alarm Form Submitted!"); // Debug log

            const day = document.getElementById("addDay").value;
            const time = document.getElementById("addTime").value;
            const label = document.getElementById("addLabel").value || "No Label"; // Default label
            const sound = document.getElementById("addSound").value;

            // Client-side validation for required alarm fields
            if (!day || !time || !sound) {
                console.warn("Client-side validation failed for Add Alarm: Missing day, time, or sound."); // Debug log
                showFlashMessage("Please fill in all required fields (Day, Time, Sound) for the alarm.", "error", 'dashboardFlashContainer'); // Pass container ID
                return;
            }
            
            const formData = new FormData();
            formData.append('day', day);
            formData.append('time', time);
            formData.append('label', label);
            formData.append('sound', sound);

            // Log the form data being sent for debugging
            console.log("Collected add alarm data:", { day, time, label, sound }); // Debug log

            try {
                const response = await fetch('/set_alarm', {
                    method: 'POST',
                    body: formData
                });
                console.log("Add Alarm Response Status:", response.status); // Debug log

                // For redirects, the new page load will handle flash messages.
                // We just need to trigger a full page reload if the backend redirects.
                if (response.redirected) {
                    console.log("Add Alarm: Redirected to:", response.url); // Debug log
                    window.location.href = response.url; // Follow Flask's redirect
                } else if (response.ok) {
                    // This block should ideally not be hit if Flask redirects for success.
                    // But if it does, it means a 200 OK was returned without a redirect.
                    console.log("Add Alarm: Successful response, resetting form and refreshing alarms (no redirect)."); // Debug log
                    showFlashMessage("Alarm set successfully.", "success", 'dashboardFlashContainer'); // Explicitly show message if no redirect
                    this.reset(); // Clear form fields
                    closeModal("addModal"); // Close the modal
                    await fetchAlarmsAndRender(); // Fetch and re-render alarms to update the UI
                } else {
                    console.error("Add Alarm: Server responded with an error or unexpected status:", response.status); // Debug log
                    showFlashMessage(`Failed to add alarm. Server responded with status: ${response.status}.`, "error", 'dashboardFlashContainer'); // Pass container ID
                }
            } catch (error) {
                console.error("Error adding new alarm (network/fetch error):", error); // Debug log
                showFlashMessage("Network error adding alarm. " + error.message, "error", 'dashboardFlashContainer'); // Pass container ID
            }
        });

        /**
         * Fetches all alarms from the backend API and then triggers rendering functions
         * for both the main alarms table and the weekly alarm overview.
         * This function is crucial for keeping the frontend in sync with backend alarm data.
         */
        async function fetchAlarmsAndRender() {
            console.log("Fetching alarms and rendering..."); // Debug log
            try {
                const response = await fetch('/api/alarms'); // API endpoint to get all alarms
                const data = await response.json();
                console.log("API response data for alarms:", data); // NEW DEBUG LOG: Inspect full data object

                // Ensure data.alarms is an array. If it's not, default to an empty array.
                // This is the crucial fix for "alarms.filter is not a function".
                if (Array.isArray(data.alarms)) {
                    alarms = data.alarms;
                } else {
                    console.warn("Received alarms data is not an array, defaulting to empty array.", data.alarms);
                    alarms = [];
                }

                if (data.status === 'error') { // This check is for an overall error status
                    showFlashMessage(data.message, 'error', 'dashboardFlashContainer'); // Pass container ID
                    // Render empty state or error if API call fails
                    alarms = []; // Ensure alarms array is empty if fetch fails
                    renderAlarms();
                    renderWeeklyAlarms();
                    return; // EXIT early if there's an API error status
                }
                
                renderAlarms(); // Render alarms in the main table
                renderWeeklyAlarms(); // Render alarms in the weekly overview
            } catch (error) {
                console.error("Failed to fetch alarms:", error); // Debug log
                showFlashMessage("Failed to load alarms from the system. " + error.message, "error", 'dashboardFlashContainer'); // Pass container ID
                // Ensure UI reflects empty state or error even on fetch failure
                alarms = [];
                renderAlarms();
                renderWeeklyAlarms();
            }
        }

        /**
         * Renders the alarms into the main alarms table (`alarmsTableBody`).
         * Iterates through the `alarms` array and creates a table row for each alarm,
         * including "Edit" and "Delete" action buttons.
         * Shows "No alarms configured" message if the alarms array is empty.
         */
        function renderAlarms() {
            console.log("Rendering alarms to main table..."); // Debug log
            const tbody = document.getElementById("alarmsTableBody");
            const noAlarms = document.getElementById("noAlarms");
            
            // Null checks for table elements.
            if (!tbody || !noAlarms) {
                console.warn("Missing alarm table elements (tbody or noAlarms div). Skipping renderAlarms.");
                return;
            }

            tbody.innerHTML = ""; // Clear existing table rows

            // IMPORTANT DEBUG LOG: Log type and content of `alarms` right before forEach
            console.log("renderAlarms - Type of alarms:", typeof alarms, "Content:", alarms);

            if (!Array.isArray(alarms) || alarms.length === 0) { // Added Array.isArray check
                noAlarms.classList.remove("hidden"); // Show "No alarms" message
                return;
            }

            noAlarms.classList.add("hidden"); // Hide "No alarms" message if alarms exist

            alarms.forEach((alarm) => { // Removed index, using alarm.id directly
                const row = document.createElement("tr");
                row.className = "table-row bg-white border-b hover:bg-gray-50"; // Apply Tailwind classes

                row.innerHTML = `
                    <td class="py-4 px-4">${alarm.day}</td>
                    <td class="py-4 px-4">${alarm.time}</td>
                    <td class="py-4 px-4">${alarm.label}</td>
                    <td class="py-4 px-4">${alarm.sound}</td>
                    <td class="py-4 px-4 text-center">
                        <button type="button" onclick="editAlarm('${alarm.id}')" class="text-blue-600 hover:text-blue-700 text-sm mr-2 p-1 rounded-md hover:bg-blue-50 transition-colors">
                            <i class="fas fa-edit mr-1"></i>Edit
                        </button>
                        <button type="button" onclick="removeAlarm('${alarm.id}')" class="text-red-600 hover:text-red-700 text-sm p-1 rounded-md hover:bg-red-50 transition-colors">
                            <i class="fas fa-trash mr-1"></i>Delete
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
            });
            console.log("Alarms rendered to main table successfully."); // Debug log
        }

        /**
         * Sends a request to delete an alarm by its unique ID.
         * Confirms with the user before proceeding.
         * After successful deletion (or redirect), it refreshes the alarm lists.
         * @param {string} alarmId - The unique ID of the alarm to delete.
         */
        async function removeAlarm(alarmId) {
            // Using window.confirm for simplicity, but a custom modal is recommended for production.
            if (!window.confirm(`Are you sure you want to permanently delete this alarm? This action cannot be undone.`)) {
                return;
            }
            console.log(`Attempting to delete alarm with ID: ${alarmId}`); // Debug log
            try {
                const response = await fetch(`/delete_alarm/${alarmId}`, {
                    method: 'POST' // Using POST for browser compatibility with redirects
                });
                console.log("Delete Alarm Response Status:", response.status); // Debug log

                if (response.redirected) {
                    window.location.href = response.url; // Follow Flask's redirect
                } else if (response.ok) {
                    // This block should ideally not be hit if Flask redirects for success.
                    // But if it does, it means a 200 OK was returned without a redirect.
                    console.log("Delete Alarm: Successful response, refreshing alarms (no redirect)."); // Debug log
                    showFlashMessage("Alarm deleted successfully.", "success", 'dashboardFlashContainer'); // Explicitly show message if no redirect
                    await fetchAlarmsAndRender(); // Refresh alarms after successful deletion
                } else {
                    console.error("Delete Alarm: Server responded with an error or unexpected status:", response.status); // Debug log
                    showFlashMessage(`Failed to delete alarm. Server responded with status: ${response.status}.`, "error", 'dashboardFlashContainer'); // Pass container ID
                }
            } catch (error) {
                console.error("Error deleting alarm (network/fetch error):", error); // Debug log
                showFlashMessage("Network error deleting alarm. " + error.message, "error", 'dashboardFlashContainer'); // Pass container ID
            }
        }

        /**
         * Populates the "Edit Alarm" modal with data from a specific alarm
         * and then opens the modal.
         * This prepares the form for the user to make changes to an existing alarm.
         * @param {string} alarmId - The unique ID of the alarm to edit.
         */
        function editAlarm(alarmId) {
            console.log(`Preparing to edit alarm with ID: ${alarmId}`); // Debug log
            const alarm = alarms.find(a => a.id === alarmId); // Find the alarm object by its ID
            
            if (!alarm) {
                console.error(`Alarm with ID '${alarmId}' not found for editing.`);
                showFlashMessage("Error: Alarm not found for editing.", "error", 'dashboardFlashContainer'); // Pass container ID
                return;
            }

            // Get all relevant input elements from the edit modal
            const editAlarmIndex = document.getElementById("editAlarmIndex"); // This will now store the alarm.id
            const editDay = document.getElementById("editDay");
            const editTime = document.getElementById("editTime");
            const editLabel = document.getElementById("editLabel");
            const editSound = document.getElementById("editSound");

            // Robust null checks.
            if (!editAlarmIndex || !editDay || !editTime || !editLabel || !editSound) {
                console.warn("Missing edit alarm modal elements. Cannot populate or open edit modal.");
                showFlashMessage("Error: Edit alarm modal elements not found.", "error", 'dashboardFlashContainer'); // Pass container ID
                return;
            }

            // Populate the modal fields with the alarm's current data
            editAlarmIndex.value = alarm.id; // Store the alarm's unique ID
            editDay.value = alarm.day;
            editTime.value = alarm.time;
            editLabel.value = alarm.label === "No Label" ? "" : alarm.label; // Clear "No Label" for editing
            editSound.value = alarm.sound;
            openModal("editModal"); // Open the edit modal
            console.log("Edit alarm modal populated and opened for alarm:", alarm); // Debug log
        }

        /**
         * Event listener for the "Edit Alarm" form submission.
         * Collects updated alarm data, validates, and sends to the backend via POST request.
         * After successful submission (or redirect), it refreshes the alarm lists.
         */
        document.getElementById("editAlarmForm").addEventListener("submit", async function(e) {
            e.preventDefault(); // Prevent default form submission
            console.log("Edit Alarm Form Submitted!"); // Debug log

            const alarmId = document.getElementById("editAlarmIndex").value; // Get the alarm's unique ID
            const day = document.getElementById("editDay").value;
            const time = document.getElementById("editTime").value;
            const label = document.getElementById("editLabel").value || "No Label";
            const sound = document.getElementById("editSound").value;

            // Client-side validation for required fields
            if (!day || !time || !sound) {
                console.warn("Client-side validation failed for Edit Alarm: Missing day, time, or sound."); // Debug log
                showFlashMessage("Please fill in all required fields (Day, Time, Sound) to update the alarm.", "error", 'dashboardFlashContainer'); // Pass container ID
                return;
            }

            const formData = new FormData();
            formData.append('day', day);
            formData.append('time', time);
            formData.append('label', label);
            formData.append('sound', sound);

            // Log the form data being sent for debugging
            console.log("Collected edit alarm data:", { alarmId, day, time, label, sound }); // Debug log

            try {
                const response = await fetch(`/edit_alarm/${alarmId}`, {
                    method: 'POST', // Using POST for browser compatibility
                    body: formData
                });
                console.log("Edit Alarm Response Status:", response.status); // Debug log

                if (response.redirected) {
                    window.location.href = response.url; // Follow Flask's redirect
                } else if (response.ok) {
                    // This block should ideally not be hit if Flask redirects for success.
                    // But if it does, it means a 200 OK was returned without a redirect.
                    console.log("Edit Alarm: Successful response, refreshing alarms (no redirect)."); // Debug log
                    showFlashMessage("Alarm updated successfully.", "success", 'dashboardFlashContainer'); // Explicitly show message if no redirect
                    closeModal("editModal"); // Close the modal
                    await fetchAlarmsAndRender(); // Fetch and re-render alarms to update the UI
                } else {
                    console.error("Edit Alarm: Server responded with an error or unexpected status:", response.status); // Debug log
                    showFlashMessage(`Failed to update alarm. Server responded with status: ${response.status}.`, "error", 'dashboardFlashContainer'); // Pass container ID
                }
            } catch (error) {
                console.error("Error editing alarm (network/fetch error):", error); // Debug log
                showFlashMessage("Network error editing alarm. " + error.message, "error", 'dashboardFlashContainer'); // Pass container ID
            }
        });


        // --- Weekly Alarm Rendering ---
        const daysOfWeek = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

        /**
         * Renders alarms organized by day of the week in the "Weekly Alarm Overview" grid.
         * Creates a card for each day and lists the alarms scheduled for that day, sorted by time.
         * Also displays a message if no alarms are scheduled for the entire week.
         */
        function renderWeeklyAlarms() {
            console.log("Rendering weekly alarms..."); // Debug log
            const weeklyAlarmsGrid = document.getElementById("weeklyAlarmsGrid");
            const noWeeklyAlarms = document.getElementById("noWeeklyAlarms");

            // Robust null checks for critical parent elements.
            if (!weeklyAlarmsGrid || !noWeeklyAlarms) {
                console.warn("Missing weekly alarm grid elements (weeklyAlarmsGrid or noWeeklyAlarms). Skipping renderWeeklyAlarms.");
                return;
            }

            weeklyAlarmsGrid.innerHTML = ""; // Clear existing content
            noWeeklyAlarms.classList.add("hidden"); // Hide the "No alarms" message initially

            console.log("renderWeeklyAlarms - Type of alarms:", typeof alarms, "Content:", alarms);

            // Check if there are any alarms at all.
            const totalAlarmsConfigured = Array.isArray(alarms) && alarms.length > 0;

            if (!totalAlarmsConfigured) {
                // If no alarms, display the "No alarms configured" message and return.
                noWeeklyAlarms.classList.remove("hidden");
                console.log("No alarms configured, displaying no alarms message and returning.");
                return; // Exit the function early if no alarms.
            }

            // If there are alarms, proceed to render day cards.
            daysOfWeek.forEach(day => {
                const dayCard = document.createElement("div"); // This should always create a div
                dayCard.className = "day-card p-6 fade-in";
                
                // Filter and sort alarms for the current day by time
                const alarmsForDay = alarms.filter(alarm => alarm.day === day).sort((a, b) => a.time.localeCompare(b.time));

                let alarmsHtml = '';
                if (alarmsForDay.length > 0) {
                    alarmsForDay.forEach((alarm) => {
                        // Use alarm.id directly for edit and delete actions
                        alarmsHtml += `
                            <div class="alarm-item">
                                <div class="flex items-center gap-2">
                                    <i class="fas fa-bell text-gray-500 text-xs"></i>
                                    <div>
                                        <p class="text-sm font-medium text-gray-800">${alarm.time} - ${alarm.label}</p>
                                        <p class="text-xs text-gray-500">${alarm.sound}</p>
                                    </div>
                                </div>
                                <div class="flex gap-2">
                                    <button type="button" onclick="editAlarm('${alarm.id}')" class="text-blue-500 hover:text-blue-600 text-xs p-1 rounded-md hover:bg-blue-50 transition-colors">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button type="button" onclick="removeAlarm('${alarm.id}')" class="text-red-500 hover:text-red-600 text-xs p-1 rounded-md hover:bg-red-50 transition-colors">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                        `;
                    });
                } else {
                    alarmsHtml = '<p class="text-sm text-gray-500 text-center py-4">No alarms scheduled for this day.</p>';
                }

                dayCard.innerHTML = `
                    <h3 class="text-lg font-semibold text-gray-800 mb-4">${day}</h3>
                    <div class="space-y-3">
                        ${alarmsHtml}
                    </div>
                `;
                weeklyAlarmsGrid.appendChild(dayCard); 
            });
            console.log("Weekly alarms rendered successfully."); // Debug log
        }


        // --- Modal & Flash Message Utilities ---

        /**
         * Opens a specified modal by adding the 'active' class.
         * This makes the modal visible and centered on the screen.
         * @param {string} id - The ID of the modal element to open.
         */
        function openModal(id) {
            const modal = document.getElementById(id);
            if (modal) {
                modal.classList.add("active");
                console.log(`Opened modal: ${id}`); // Debug log
            } else {
                console.error(`Modal with ID '${id}' not found.`);
            }
        }

        /**
         * Closes a specified modal by removing the 'active' class.
         * This hides the modal from view.
         * @param {string} id - The ID of the modal element to close.
         */
        function closeModal(id) {
            const modal = document.getElementById(id);
            if (modal) {
                modal.classList.remove("active");
                console.log(`Closed modal: ${id}`); // Debug log
            } else {
                console.error(`Modal with ID '${id}' not found.`);
            }
        }

        /**
         * Displays a flash message at the top of the dashboard.
         * @param {string} message - The message text to display.
         * @param {string} type - The type of message ('info', 'success', 'error', 'warning'). Affects styling.
         * @param {string} targetContainerId - The ID of the specific flash message container to use (e.g., 'loginFlashContainer', 'dashboardFlashContainer').
         * @param {boolean} [autoHide=true] - Whether the message should automatically hide after a delay. Defaults to true.
         */
        function showFlashMessage(message, type = "info", targetContainerId = 'dashboardFlashContainer', autoHide = true) { 
            const innerFlashMessageDiv = document.getElementById(targetContainerId); // This is the div with id="loginFlashContainer" or "dashboardFlashContainer"
            if (!innerFlashMessageDiv) {
                console.error(`Flash message container with ID '${targetContainerId}' not found.`);
                return;
            }

            const outerFlashContainer = innerFlashMessageDiv.closest('.flash-message-container'); // Find the closest parent with this class
            if (!outerFlashContainer) {
                console.error(`Outer flash message container for ID '${targetContainerId}' not found.`);
                return;
            }

            // Ensure the outer container is visible by adding the 'active' class
            outerFlashContainer.classList.add("active");
            // Also ensure it's not hidden by Tailwind's 'hidden' class or inline style
            outerFlashContainer.classList.remove("hidden");
            outerFlashContainer.style.display = ''; // Clear inline display style

            // Ensure the inner message div is visible (it might have been hidden by a previous close or initial state)
            console.log(`[${targetContainerId}] Before show: classList=${innerFlashMessageDiv.classList}, style.display=${innerFlashMessageDiv.style.display}`);
            innerFlashMessageDiv.classList.remove("hidden"); // Remove Tailwind's hidden class
            innerFlashMessageDiv.style.display = 'flex'; // Explicitly set display to flex for the inner message box

            const msg = innerFlashMessageDiv.querySelector('span[id$="FlashMessage"]');
            const icon = innerFlashMessageDiv.querySelector('i[id$="FlashIcon"]');

            // Ensure all flash message elements exist before attempting to manipulate them.
            if (!msg || !icon) {
                console.error("Flash message UI sub-elements (span or icon) not found within container:", targetContainerId);
                return;
            }

            console.log(`showFlashMessage called: message='${message}', type='${type}', targetContainerId='${targetContainerId}', autoHide=${autoHide}`);
            
            let iconClass = "fa-info-circle";
            let bgColor = "#2563EB"; // Tailwind blue-600
            let textColor = "#FFFFFF"; // White
            let borderColor = "#1E40AF"; // Tailwind blue-800
            let shadow = "shadow-xl";
            
            // Set icon and background color based on message type
            if (type === "success") {
                iconClass = "fa-check-circle";
                bgColor = "#16A34A"; // Tailwind green-600
                textColor = "#FFFFFF"; 
                borderColor = "#15803D"; // Tailwind green-800
                shadow = "shadow-2xl";
            } else if (type === "error") {
                iconClass = "fa-times-circle";
                bgColor = "#DC2626"; // Tailwind red-600
                textColor = "#FFFFFF"; 
                borderColor = "#991B1B"; // Tailwind red-800
                shadow = "shadow-2xl";
            } else if (type === "warning") {
                iconClass = "fa-exclamation-triangle";
                bgColor = "#D97706"; // Tailwind yellow-600
                textColor = "#FFFFFF"; 
                borderColor = "#B45309"; // Tailwind yellow-800
                shadow = "shadow-2xl";
            } else if (type === "info") {
                iconClass = "fa-info-circle";
                bgColor = "#2563EB"; // Tailwind blue-600
                textColor = "#FFFFFF"; 
                borderColor = "#1E40AF"; // Tailwind blue-800
                shadow = "shadow-2xl";
            }

            icon.className = `fas ${iconClass} mr-2`;
            msg.textContent = message;
            msg.style.color = textColor;
            msg.style.whiteSpace = 'normal';
            msg.style.overflow = 'visible';
            msg.style.minWidth = 'unset';

            innerFlashMessageDiv.style.setProperty('--flash-bg-color', bgColor);
            innerFlashMessageDiv.style.setProperty('--flash-text-color', textColor);
            innerFlashMessageDiv.style.setProperty('--flash-border-color', borderColor);

            innerFlashMessageDiv.className = `flash-message px-6 py-4 relative rounded-xl ${shadow} mb-3 flex items-center border`;
            innerFlashMessageDiv.classList.add(type);

            msg.classList.add('flex-grow');

            console.log(`[${targetContainerId}] After show: classList=${innerFlashMessageDiv.classList}, style.display=${innerFlashMessageDiv.style.display}`);

            if (autoHide) {
                setTimeout(() => {
                    console.log(`[${targetContainerId}] Before hide: classList=${innerFlashMessageDiv.classList}, style.display=${innerFlashMessageDiv.style.display}`);
                    innerFlashMessageDiv.classList.add("hidden");
                    innerFlashMessageDiv.style.display = 'none';
                    
                    // Hide the outer container by removing the 'active' class and adding 'hidden'
                    outerFlashContainer.classList.remove("active");
                    outerFlashContainer.classList.add("hidden"); 
                    outerFlashContainer.style.display = 'none';

                    console.log(`[${targetContainerId}] After hide: classList=${innerFlashMessageDiv.classList}, style.display=${innerFlashMessageDiv.style.display}`);
                }, 8000);
            }
        }

        /**
         * Immediately hides the currently displayed flash message.
         * @param {string} targetContainerId - The ID of the specific flash message container to close.
         */
        function closeFlashMessage(targetContainerId) {
            const innerFlashMessageDiv = document.getElementById(targetContainerId);
            if (!innerFlashMessageDiv) {
                console.error(`Flash message container with ID '${targetContainerId}' not found.`);
                return;
            }
            const outerFlashContainer = innerFlashMessageDiv.closest('.flash-message-container');

            console.log(`[${targetContainerId}] Before close (manual): classList=${innerFlashMessageDiv.classList}, style.display=${innerFlashMessageDiv.style.display}`);
            innerFlashMessageDiv.classList.add("hidden");
            innerFlashMessageDiv.style.display = 'none';

            if (outerFlashContainer) {
                outerFlashContainer.classList.remove("active");
                outerFlashContainer.classList.add("hidden");
                outerFlashContainer.style.display = 'none';
            }
            console.log(`[${targetContainerId}] After close (manual): classList=${innerFlashMessageDiv.classList}, style.display=${innerFlashMessageDiv.style.display}`);
            console.log(`Flash message hidden manually for container: ${targetContainerId}`);
        }

        /**
         * Fetches all system settings from the backend, including license info
         * and current user's roles/feature activation, then updates the UI.
         * This function is crucial for synchronizing frontend state with backend.
         */
        async function fetchSystemSettingsAndUpdateUI() {
            console.log("Fetching system settings and updating UI..."); // Debug log
            try {
                const response = await fetch('/api/system_settings');
                const data = await response.json();
                console.log("System Settings fetched:", data); // Debug log
                if (data.status === 'error') {
                    showFlashMessage(data.message, 'error', 'dashboardFlashContainer'); // Pass container ID
                    return;
                }
                systemSettings = data; // Update global systemSettings object
                licenseInfo = systemSettings.license; // Update global licenseInfo based on fetched settings
                console.log("License Info Status (after fetch):", licenseInfo.status); // NEW DEBUG LOG

                // Update currentUserRole and currentUserFeaturesActivated from fetched data
                // This ensures the JS variables reflect the latest state from Flask session
                currentUserRole = data.user_role; 
                currentUserFeaturesActivated = data.current_user_features_activated;
                console.log(`Current User Role: ${currentUserRole}, Features Activated: ${currentUserFeaturesActivated}`); // Debug log

                updateLicenseUI(); // Update the system-wide license badge display
                checkUserRoleAndFeatureActivation(); // Re-evaluate and apply UI permissions based on updated role/activation

                // Update time settings UI in case settings modal is opened again
                selectTimeType(systemSettings.timeSettings.timeType);
                const ntpServerInput = document.getElementById('ntpServer');
                const manualDateInput = document.getElementById('manualDate');
                const manualTimeInput = document.getElementById('manualTime');

                if (ntpServerInput) ntpServerInput.value = systemSettings.timeSettings.ntpServer || '';
                if (manualDateInput) manualDateInput.value = systemSettings.timeSettings.manualDate || '';
                if (manualTimeInput) manualTimeInput.value = systemSettings.timeSettings.manualTime || '';
                
                toggleStaticIpFields(); // Ensure network fields are correctly displayed/hidden
                console.log("System settings UI updated successfully."); // Debug log
            } catch (error) {
                console.error("Error fetching system settings for UI update:", error); // Debug log
                showFlashMessage("Failed to load system settings for dashboard display. " + error.message, "error", 'dashboardFlashContainer'); // Pass container ID
            }
        }


        // --- Initialization Function for Dashboard ---

        /**
         * Initializes all dashboard components: updates current time, fetches system metrics,
         * populates sound library, fetches and renders alarms, and updates system settings related UI.
         * Also sets up recurring intervals for real-time updates.
         */
        async function init() {
            console.log("Initializing dashboard..."); // Debug log
            // Perform initial updates immediately on dashboard load
            updateCurrentTime();
            await updateMetrics(); 
            await populateSounds(); 
            await fetchAlarmsAndRender(); 
            await fetchSystemSettingsAndUpdateUI(); // This is crucial for initial permission checks and UI setup
            
            // Set up intervals to keep data updated in real-time
            setInterval(updateCurrentTime, 1000); // Update current time every second
            setInterval(updateMetrics, 5000); // Update system metrics every 5 seconds
            console.log("Dashboard initialization complete. Real-time updates started."); // Debug log
        }

        /**
         * Event listener for when the DOM content is fully loaded.
         * Determines whether to show the login page or the dashboard based on Flask's initial login status.
         * Also displays any flash messages rendered by Flask on initial page load.
         */
        document.addEventListener('DOMContentLoaded', () => {
            const loginStatusElement = document.getElementById('flaskLoginStatus');
            // Read login status from the hidden input field populated by Flask
            const isLoggedInFromFlask = loginStatusElement ? loginStatusElement.value === 'true' : false;
                        // Add event listener for the dashboard's "Reset Password" button
            const resetPasswordDashboardBtn = document.getElementById('resetPasswordBtn');
            if (resetPasswordDashboardBtn) {
                resetPasswordDashboardBtn.addEventListener('click', showResetPasswordModal);
                console.log("Event listener attached to dashboard's 'resetPasswordBtn'."); // Debugging
            } else {
                console.error("Dashboard button with ID 'resetPasswordBtn' not found."); // Debugging
            }

            if (isLoggedInFromFlask) {
                console.log("User is already logged in (from Flask status). Showing dashboard."); // Debug log
                showDashboard(); // If already logged in, show the dashboard
            } else {
                console.log("User is not logged in (from Flask status). Showing login page."); // Debug log
                showLogin(); // Otherwise, show the login page
            }

            // --- IMPORTANT: Removed general flash message processing from DOMContentLoaded ---
            // Flash messages are now handled specifically within the login form submission
            // or when a backend action explicitly renders the dashboard with messages.

            // Add event listeners for IP type radio buttons to call toggleStaticIpFields
            const dynamicIpRadio = document.getElementById('dynamicIp');
            const staticIpRadio = document.getElementById('staticIp');
            if (dynamicIpRadio) {
                dynamicIpRadio.addEventListener('change', toggleStaticIpFields);
            }
            if (staticIpRadio) {
                staticIpRadio.addEventListener('change', toggleStaticIpFields);
            }
                        // Handle Add New User Form Submission
            const addUserForm = document.getElementById('addUserForm');
            if (addUserForm) {
                addUserForm.addEventListener('submit', async function(e) {
                    e.preventDefault();
                    console.log("Add User form submitted.");

                    const newUsernameInput = document.getElementById('newUsername');
                    const newUserPasswordInput = document.getElementById('newUserPassword');
                    const confirmNewUserPasswordInput = document.getElementById('confirmNewUserPassword');
                    const newUserRoleSelect = document.getElementById('newUserRole');

                    if (!newUsernameInput || !newUserPasswordInput || !confirmNewUserPasswordInput || !newUserRoleSelect) {
                        console.error("Missing input elements in the add user form.");
                        showFlashMessage("An internal error occurred: Add user fields not found.", "error", 'dashboardFlashContainer'); // Pass container ID
                        return;
                    }

                    if (newUserPasswordInput.value.length < 8) {
                        showFlashMessage("Password must be at least 8 characters long for security.", "error", 'dashboardFlashContainer'); // Pass container ID
                        return;
                    }
                    if (newUserPasswordInput.value !== confirmNewUserPasswordInput.value) {
                        showFlashMessage("Passwords do not match. Please re-enter them carefully.", "error", 'dashboardFlashContainer'); // Pass container ID
                        return;
                    }

                    const formData = new FormData(this); // Get form data
                    try {
                        const response = await fetch('/admin/add_user', {
                            method: 'POST',
                            body: formData
                        });
                        const result = await response.json();

                        if (response.ok && result.status === 'success') {
                            showFlashMessage(result.message, "success", 'dashboardFlashContainer'); // Pass container ID
                            this.reset(); // Clear form fields
                            await fetchUsers(); // Refresh user list after adding new user
                            showUserManagementTab('resetPasswordView'); // Switch back to reset password view
                        } else {
                            showFlashMessage(result.message || "Failed to add user.", "error", 'dashboardFlashContainer'); // Pass container ID
                        }
                    } catch (error) {
                        console.error("Add user fetch error:", error);
                        showFlashMessage("Network error during user creation. Please ensure you are connected to the server.", "error", 'dashboardFlashContainer'); // Pass container ID
                    }
                });
                console.log("Event listener attached to 'addUserForm'.");
            } else {
                console.error("Form with ID 'addUserForm' not found.");
            }

        }); 

