// ui.js
// Contains general UI utility functions like openModal, closeModal, showFlashMessage, and closeFlashMessage.

console.log("ui.js loaded!"); // Added for debugging

/**
 * Opens a specified modal by adding the 'active' class.
 * This makes the modal visible and centered on the screen.
 * @param {string} id - The ID of the modal element to open.
 */
export function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add("active");
        console.log(`Opened modal: ${id}`); // Debug log
    } else {
        console.error(`Modal with ID '${id}' not found.`);
    }
}

/**
 * Closes a specified modal or flash message by removing the 'active' class
 * and setting display to 'none'.
 * @param {string} id - The ID of the modal or inner flash message element to close.
 */
export function closeModal(id) {
    const elementToClose = document.getElementById(id);
    if (!elementToClose) {
        console.error(`Element with ID '${id}' not found for closing.`);
        return;
    }

    console.log(`closeModal called for ID: ${id}`);
    console.log(`elementToClose:`, elementToClose);
    console.log(`elementToClose.classList:`, Array.from(elementToClose.classList)); // Convert to array for better logging
    console.log(`Does elementToClose have 'flash-message' class?`, elementToClose.classList.contains('flash-message'));


    // Check if it's a flash message container (inner div)
    if (elementToClose.classList.contains('flash-message')) {
        const outerFlashContainer = elementToClose.closest('.flash-message-container');
        if (outerFlashContainer) {
            outerFlashContainer.classList.remove("active");
            outerFlashContainer.classList.add("hidden");
            outerFlashContainer.style.display = 'none';
            console.log(`Outer flash container for ${id} hidden.`);
        } else {
            console.warn(`No outer flash-message-container found for ${id}.`);
        }
        elementToClose.classList.add("hidden");
        elementToClose.style.display = 'none';
        console.log(`Inner flash message with ID '${id}' hidden.`);
    } else {
        // Assume it's a regular modal
        elementToClose.classList.remove("active");
        elementToClose.style.display = 'none'; // Ensure display is set to none
        console.log(`Closed regular modal: ${id}`); // Debug log
    }
}


/**
 * Displays a flash message at the top of the dashboard.
 * @param {string} message - The message text to display.
 * @param {string} type - The type of message ('info', 'success', 'error', 'warning'). Affects styling.
 * @param {string} targetContainerId - The ID of the specific flash message container to use (e.g., 'loginFlashContainer', 'dashboardFlashContainer').
 * @param {boolean} [autoHide=true] - Whether the message should automatically hide after a delay. Defaults to true.
 */
export function showFlashMessage(message, type = "info", targetContainerId = 'dashboardFlashContainer', autoHide = true) {
    const innerFlashMessageDiv = document.getElementById(targetContainerId);
    if (!innerFlashMessageDiv) {
        console.error(`Flash message container with ID '${targetContainerId}' not found.`);
        return;
    }

    const outerFlashContainer = innerFlashMessageDiv.closest('.flash-message-container');
    if (!outerFlashContainer) {
        console.error(`Outer flash message container for ID '${targetContainerId}' not found.`);
        return;
    }

    outerFlashContainer.classList.add("active");
    outerFlashContainer.classList.remove("hidden");
    outerFlashContainer.style.display = '';

    innerFlashMessageDiv.classList.remove("hidden");
    innerFlashMessageDiv.style.display = 'flex';

    const msg = innerFlashMessageDiv.querySelector('span[id$="FlashMessage"]');
    const icon = innerFlashMessageDiv.querySelector('i[id$="FlashIcon"]');

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
            // Call closeModal to ensure consistent hiding logic
            closeModal(targetContainerId);
            console.log(`[${targetContainerId}] After hide (via setTimeout): classList=${innerFlashMessageDiv.classList}, style.display=${innerFlashMessageDiv.style.display}`);
        }, 8000);
    }
}

/**
 * Immediately hides the currently displayed flash message.
 * This function now just calls closeModal with the appropriate ID.
 * @param {string} targetContainerId - The ID of the specific flash message container to close.
 */
export function closeFlashMessage(targetContainerId) {
    closeModal(targetContainerId);
    console.log(`Flash message hidden manually for container: ${targetContainerId}`);
}
