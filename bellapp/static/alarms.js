// alarms.js
// Manages alarm functionalities (add, edit, delete, render).
import { showFlashMessage, closeModal, openModal } from './ui.js'; // Ensure openModal is imported
import { alarms, setAlarms } from './globals.js';

/**
 * Event listener for the "Add New Alarm" form submission.
 * Collects alarm data, validates, and sends to the backend via POST request.
 * After successful submission (or redirect), it refreshes the alarm lists.
 */
export async function handleAddAlarm(e) {
    e.preventDefault();
    console.log("Add Alarm Form Submitted!");

    const day = document.getElementById("addDay").value;
    const time = document.getElementById("addTime").value;
    const label = document.getElementById("addLabel").value || "No Label";
    const sound = document.getElementById("addSound").value;

    if (!day || !time || !sound) {
        console.warn("Client-side validation failed for Add Alarm: Missing day, time, or sound.");
        showFlashMessage("Please fill in all required fields (Day, Time, Sound) for the alarm.", "error", 'dashboardFlashContainer');
        return;
    }

    const formData = new FormData();
    formData.append('day', day);
    formData.append('time', time);
    formData.append('label', label);
    formData.append('sound', sound);

    console.log("Collected add alarm data:", { day, time, label, sound });

    try {
        const response = await fetch('/set_alarm', {
            method: 'POST',
            body: formData
        });
        console.log("Add Alarm Response Status:", response.status);

        if (response.redirected) {
            console.log("Add Alarm: Redirected to:", response.url);
            window.location.href = response.url;
        } else if (response.ok) {
            console.log("Add Alarm: Successful response, resetting form and refreshing alarms (no redirect).");
            showFlashMessage("Alarm set successfully.", "success", 'dashboardFlashContainer');
            closeModal("addModal");
            this.reset();
            await fetchAlarmsAndRender();
        } else {
            console.error("Add Alarm: Server responded with an error or unexpected status:", response.status);
            showFlashMessage(`Failed to add alarm. Server responded with status: ${response.status}.`, "error", 'dashboardFlashContainer');
        }
    } catch (error) {
        console.error("Error adding new alarm (network/fetch error):", error);
        showFlashMessage("Network error adding alarm. " + error.message, "error", 'dashboardFlashContainer');
    }
}

/**
 * Fetches all alarms from the backend API and then triggers rendering functions
 * for both the main alarms table and the weekly alarm overview.
 * This function is crucial for keeping the frontend in sync with backend alarm data.
 */
export async function fetchAlarmsAndRender() {
    console.log("Fetching alarms and rendering...");
    try {
        const response = await fetch('/api/alarms');
        const data = await response.json();
        console.log("API response data for alarms:", data);

        if (Array.isArray(data.alarms)) {
            setAlarms(data.alarms);
        } else {
            console.warn("Received alarms data is not an array, defaulting to empty array.", data.alarms);
            setAlarms([]);
        }

        if (data.status === 'error') {
            showFlashMessage(data.message, 'error', 'dashboardFlashContainer');
            setAlarms([]);
            renderAlarms();
            renderWeeklyAlarms();
            return;
        }

        renderAlarms();
        renderWeeklyAlarms();
    } catch (error) {
        console.error("Failed to fetch alarms:", error);
        showFlashMessage("Failed to load alarms from the system. " + error.message, "error", 'dashboardFlashContainer');
        setAlarms([]);
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
export function renderAlarms() {
    console.log("Rendering alarms to main table...");
    const tbody = document.getElementById("alarmsTableBody");
    const noAlarms = document.getElementById("noAlarms");

    if (!tbody || !noAlarms) {
        console.warn("Missing alarm table elements (tbody or noAlarms div). Skipping renderAlarms.");
        return;
    }

    tbody.innerHTML = "";

    console.log("renderAlarms - Type of alarms:", typeof alarms, "Content:", alarms);

    if (!Array.isArray(alarms) || alarms.length === 0) {
        noAlarms.classList.remove("hidden");
        return;
    }

    noAlarms.classList.add("hidden");

    alarms.forEach((alarm) => {
        const row = document.createElement("tr");
        row.className = "table-row bg-white border-b hover:bg-gray-50";

        row.innerHTML = `
            <td class="py-4 px-4">${alarm.day}</td>
            <td class="py-4 px-4">${alarm.time}</td>
            <td class="py-4 px-4">${alarm.label}</td>
            <td class="py-4 px-4">${alarm.sound}</td>
            <td class="py-4 px-4 text-center">
                <button type="button" onclick="window.editAlarm('${alarm.id}')" class="text-blue-600 hover:text-blue-700 text-sm mr-2 p-1 rounded-md hover:bg-blue-50 transition-colors">
                    <i class="fas fa-edit mr-1"></i>Edit
                </button>
                <button type="button" onclick="window.removeAlarm('${alarm.id}')" class="text-red-600 hover:text-red-700 text-sm p-1 rounded-md hover:bg-red-50 transition-colors">
                    <i class="fas fa-trash mr-1"></i>Delete
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
    console.log("Alarms rendered to main table successfully.");
}

/**
 * Sends a request to delete an alarm by its unique ID.
 * Confirms with the user before proceeding.
 * After successful deletion (or redirect), it refreshes the alarm lists.
 * @param {string} alarmId - The unique ID of the alarm to delete.
 */
export async function removeAlarm(alarmId) {
    if (!window.confirm(`Are you sure you want to permanently delete this alarm? This action cannot be undone.`)) {
        return;
    }
    console.log(`Attempting to delete alarm with ID: ${alarmId}`);
    try {
        const response = await fetch(`/delete_alarm/${alarmId}`, {
            method: 'POST'
        });
        console.log("Delete Alarm Response Status:", response.status);

        if (response.redirected) {
            window.location.href = response.url;
        } else if (response.ok) {
            console.log("Delete Alarm: Successful response, refreshing alarms (no redirect).");
            showFlashMessage("Alarm deleted successfully.", "success", 'dashboardFlashContainer');
            await fetchAlarmsAndRender();
        } else {
            console.error("Delete Alarm: Server responded with an error or unexpected status:", response.status);
            showFlashMessage(`Failed to delete alarm. Server responded with status: ${response.status}.`, "error", 'dashboardFlashContainer');
        }
    } catch (error) {
        console.error("Error deleting alarm (network/fetch error):", error);
        showFlashMessage("Network error deleting alarm. " + error.message, "error", 'dashboardFlashContainer');
    }
}

/**
 * Populates the "Edit Alarm" modal with data from a specific alarm
 * and then opens the modal.
 * This prepares the form for the user to make changes to an existing alarm.
 * @param {string} alarmId - The unique ID of the alarm to edit.
 */
export function editAlarm(alarmId) {
    console.log(`Preparing to edit alarm with ID: ${alarmId}`);
    const alarm = alarms.find(a => a.id === alarmId);

    if (!alarm) {
        console.error(`Alarm with ID '${alarmId}' not found for editing.`);
        showFlashMessage("Error: Alarm not found for editing.", "error", 'dashboardFlashContainer');
        return;
    }

    const editAlarmIndex = document.getElementById("editAlarmIndex");
    const editDay = document.getElementById("editDay");
    const editTime = document.getElementById("editTime");
    const editLabel = document.getElementById("editLabel");
    const editSound = document.getElementById("editSound");

    if (!editAlarmIndex || !editDay || !editTime || !editLabel || !editSound) {
        console.warn("Missing edit alarm modal elements. Cannot populate or open edit modal.");
        showFlashMessage("Error: Edit alarm modal elements not found.", "error", 'dashboardFlashContainer');
        return;
    }

    editAlarmIndex.value = alarm.id;
    editDay.value = alarm.day;
    editTime.value = alarm.time;
    editLabel.value = alarm.label === "No Label" ? "" : alarm.label;
    editSound.value = alarm.sound;
    openModal("editModal"); // Uncommented this line to open the modal
    console.log("Edit alarm modal populated and opened for alarm:", alarm);
}

/**
 * Event listener for the "Edit Alarm" form submission.
 * Collects updated alarm data, validates, and sends to the backend via POST request.
 * After successful submission (or redirect), it refreshes the alarm lists.
 */
export async function handleEditAlarm(e) {
    e.preventDefault();
    console.log("Edit Alarm Form Submitted!");

    const alarmId = document.getElementById("editAlarmIndex").value;
    const day = document.getElementById("editDay").value;
    const time = document.getElementById("editTime").value;
    const label = document.getElementById("editLabel").value || "No Label";
    const sound = document.getElementById("editSound").value;

    if (!day || !time || !sound) {
        console.warn("Client-side validation failed for Edit Alarm: Missing day, time, or sound.");
        showFlashMessage("Please fill in all required fields (Day, Time, Sound) to update the alarm.", "error", 'dashboardFlashContainer');
        return;
    }

    const formData = new FormData();
    formData.append('day', day);
    formData.append('time', time);
    formData.append('label', label);
    formData.append('sound', sound);

    console.log("Collected edit alarm data:", { alarmId, day, time, label, sound });

    try {
        const response = await fetch(`/edit_alarm/${alarmId}`, {
            method: 'POST',
            body: formData
        });
        console.log("Edit Alarm Response Status:", response.status);

        if (response.redirected) {
            window.location.href = response.url;
        } else if (response.ok) {
            console.log("Edit Alarm: Successful response, refreshing alarms (no redirect).");
            showFlashMessage("Alarm updated successfully.", "success", 'dashboardFlashContainer');
            closeModal("editModal");
            await fetchAlarmsAndRender();
        } else {
            console.error("Edit Alarm: Server responded with an error or unexpected status:", response.status);
            showFlashMessage(`Failed to update alarm. Server responded with status: ${response.status}.`, "error", 'dashboardFlashContainer');
        }
    } catch (error) {
        console.error("Error editing alarm (network/fetch error):", error);
        showFlashMessage("Network error editing alarm. " + error.message, "error", 'dashboardFlashContainer');
    }
}

const daysOfWeek = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

/**
 * Renders alarms organized by day of the week in the "Weekly Alarm Overview" grid.
 * Creates a card for each day and lists the alarms scheduled for that day, sorted by time.
 * Also displays a message if no alarms are scheduled for the entire week.
 */
export function renderWeeklyAlarms() {
    console.log("Rendering weekly alarms...");
    const weeklyAlarmsGrid = document.getElementById("weeklyAlarmsGrid");
    const noWeeklyAlarms = document.getElementById("noWeeklyAlarms");

    if (!weeklyAlarmsGrid || !noWeeklyAlarms) {
        console.warn("Missing weekly alarm grid elements (weeklyAlarmsGrid or noWeeklyAlarms). Skipping renderWeeklyAlarms.");
        return;
    }

    weeklyAlarmsGrid.innerHTML = "";
    noWeeklyAlarms.classList.add("hidden");

    console.log("renderWeeklyAlarms - Type of alarms:", typeof alarms, "Content:", alarms);

    const totalAlarmsConfigured = Array.isArray(alarms) && alarms.length > 0;

    if (!totalAlarmsConfigured) {
        noWeeklyAlarms.classList.remove("hidden");
        console.log("No alarms configured, displaying no alarms message and returning.");
        return;
    }

    daysOfWeek.forEach(day => {
        const dayCard = document.createElement("div");
        dayCard.className = "day-card p-6 fade-in";

        const alarmsForDay = alarms.filter(alarm => alarm.day === day).sort((a, b) => a.time.localeCompare(b.time));

        let alarmsHtml = '';
        if (alarmsForDay.length > 0) {
            alarmsForDay.forEach((alarm) => {
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
                            <button type="button" onclick="window.editAlarm('${alarm.id}')" class="text-blue-500 hover:text-blue-600 text-xs p-1 rounded-md hover:bg-blue-50 transition-colors">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button type="button" onclick="window.removeAlarm('${alarm.id}')" class="text-red-500 hover:text-red-600 text-xs p-1 rounded-md hover:bg-red-50 transition-colors">
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
    console.log("Weekly alarms rendered successfully.");
}
