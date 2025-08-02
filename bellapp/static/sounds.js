// Manages sound-related functionalities (populate, test, delete, upload).
import { showFlashMessage } from './ui.js';
import { sounds, setSounds } from './globals.js';

/**
 * Fetches the list of available sound files from the backend and populates
 * the sound library list and the sound selection dropdowns in alarm modals.
 */
export async function populateSounds() {
    const soundList = document.getElementById("soundsList");
    const addSoundSelect = document.getElementById("addSound");
    const editSoundSelect = document.getElementById("editSound");

    if (!soundList || !addSoundSelect || !editSoundSelect) {
        console.warn("Missing sound list or sound select elements. Skipping populateSounds.");
        return;
    }

    soundList.innerHTML = "";
    addSoundSelect.innerHTML = '<option value="">Select a sound</option>';
    editSoundSelect.innerHTML = '<option value="">Select a sound</option>';

    try {
        const response = await fetch('/api/sounds');
        const backendSounds = await response.json();
        setSounds(backendSounds.sounds || []);
        console.log("Fetched sounds:", sounds);

        if (sounds.length === 0) {
            soundList.innerHTML = '<p class="text-sm text-gray-500 text-center py-4">No sounds uploaded yet. Use the "Upload Sound" button to add some.</p>';
            addSoundSelect.add(new Option("No sounds available - Upload first", "", true, true));
            editSoundSelect.add(new Option("No sounds available - Upload first", "", true, true));
            addSoundSelect.disabled = true;
            editSoundSelect.disabled = true;
        } else {
            addSoundSelect.disabled = false;
            editSoundSelect.disabled = false;
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
                    <button type="button" onclick="window.testSound('${sound}')" class="text-green-600 hover:text-green-700 text-sm">
                        <i class="fas fa-play mr-1"></i>Test
                    </button>
                    <button type="button" onclick="window.deleteSound('${sound}')" class="text-red-600 hover:text-red-700 text-sm">
                        <i class="fas fa-trash mr-1"></i>Delete
                    </button>
                </div>
            `;
            soundList.appendChild(div);

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
        showFlashMessage("Failed to load sounds for the library. " + error.message, "error", 'dashboardFlashContainer');
    }
}

/**
 * Plays a specified sound file.
 * @param {string} sound - The filename of the sound to play.
 */
export function testSound(sound) {
    const audio = new Audio(`./static/audio/${sound}`);
    audio.play().catch(e => {
        console.error("Error playing sound:", e);
        showFlashMessage(`Failed to play sound: ${sound}. Your browser might have blocked autoplay or the file is corrupted.`, "error", 'dashboardFlashContainer');
    });
}

/**
 * Sends a request to delete a specified sound file.
 * Confirms with the user before proceeding.
 * @param {string} filename - The name of the sound file to delete.
 */
export async function deleteSound(filename) {
    if (!window.confirm(`Are you sure you want to permanently delete the sound file '${filename}'? This action cannot be undone.`)) {
        return;
    }
    console.log(`Attempting to delete sound: ${filename}`);
    try {
        const response = await fetch(`/delete_song/${filename}`, {
            method: 'POST'
        });
        console.log("Delete Sound Response Status:", response.status);

        if (response.redirected) {
            window.location.href = response.url;
        } else if (response.ok) {
            console.log("Delete Sound: Successful response, refreshing sounds (no redirect).");
            showFlashMessage("Sound deleted successfully.", "success", 'dashboardFlashContainer');
            populateSounds();
        }
    } catch (error) {
        console.error("Error deleting sound file:", error);
        showFlashMessage("Network error deleting sound. " + error.message, "error", 'dashboardFlashContainer');
    }
}

/**
 * Event listener for the sound file upload form.
 * Handles file selection, validation (size/type), and sends to backend.
 */
export async function handleSoundUpload(e) {
    e.preventDefault();
    console.log("Upload form submitted.");
    const fileInput = document.getElementById("fileInput");
    const file = fileInput.files[0];

    if (!file) {
        showFlashMessage("Please select an audio file to upload.", "error", 'dashboardFlashContainer');
        return;
    }

    if (file.size > 2 * 1024 * 1024) { // Max 2MB
        showFlashMessage("The selected file size exceeds the 2MB limit. Please choose a smaller file.", "error", 'dashboardFlashContainer');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    console.log("Attempting to upload file:", file.name, "Size:", file.size);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        console.log("Upload Response Status:", response.status);
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
            fileInput.value = "";
            populateSounds();
        }
    } catch (error) {
        console.error("Error uploading sound file:", error);
        showFlashMessage("Network error during sound upload. " + error.message, "error", 'dashboardFlashContainer');
    }
}
