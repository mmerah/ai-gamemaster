import { addMessageToHistory, updateUI } from './ui.js';

const API_PLAYER_ACTION_URL = '/api/player_action';
const API_SUBMIT_ROLLS_URL = '/api/submit_rolls';
const API_GAME_STATE_URL = '/api/game_state';
const API_TRIGGER_NEXT_STEP_URL = '/api/trigger_next_step';

// Store callbacks to update UI after API calls
let uiUpdateCallback = null;
let sendActionCallbackForUI = null;
let sendSubmitRollsCallbackForUI = null;

// Flag to prevent multiple triggers
let isTriggeringNextStep = false;

// --- Helper Function: Convert camelCase keys to snake_case ---
function camelToSnake(key) {
    return key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
}

function convertKeysToSnakeCase(obj) {
    if (typeof obj !== 'object' || obj === null) {
        return obj;
    }
    if (Array.isArray(obj)) {
        return obj.map(convertKeysToSnakeCase);
    }
    const newObj = {};
    for (const key in obj) {
        if (Object.prototype.hasOwnProperty.call(obj, key)) {
            newObj[camelToSnake(key)] = convertKeysToSnakeCase(obj[key]);
        }
    }
    return newObj;
}

export function registerUICallbacks(updateCallback, actionCallback, submitRollsCallback) {
    uiUpdateCallback = updateCallback;
    sendActionCallbackForUI = actionCallback;
    sendSubmitRollsCallbackForUI = submitRollsCallback;
}


// Function to send player action (choice or free text)
export async function sendAction(actionType, value) {
    console.log(`Sending action: Type=${actionType}, Value=${JSON.stringify(value)}`);
    if (actionType !== 'free_text') {
        console.warn(`sendAction called with unexpected type: ${actionType}. Sending as free_text.`);
        actionType = 'free_text'; // Force it
    }

    // Add player message immediately to UI (handled by caller in main.js now)
    // disableInputs(); // Handled by caller
    // clearFreeTextInput(); // Handled by caller

    try {
        console.debug(`Sending POST request to ${API_PLAYER_ACTION_URL}`);
        const response = await fetch(API_PLAYER_ACTION_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action_type: actionType, value: value }),
        });
        console.debug(`Received response status: ${response.status}`);

        const responseData = await response.json();

        if (!response.ok) {
            const errorMsg = responseData.error || responseData.message || `HTTP error! status: ${response.status}`;
            console.warn("Parsed error data from backend:", responseData);
            // Throw error to be caught below
            throw new Error(errorMsg);
        }

        console.log("Received AI Response Object after action:", responseData);

        // Process Successful Response - Update the entire UI
        if (uiUpdateCallback) {
            uiUpdateCallback(responseData, sendActionCallbackForUI, sendSubmitRollsCallbackForUI);
        } else {
            console.error("UI Update callback not registered in api.js");
        }

    } catch (error) {
        console.error('Error sending action:', error);
        const errorText = `Error: ${error.message || 'Communication failed.'}`;
        addMessageToHistory('System', `(System Error: ${errorText})`);
    }
    console.log("sendAction finished.");
}

export async function sendCompletedRolls(completedRollRequests) {
    // completedRollRequests is the array of *request data objects* stored in ui.js
    if (!completedRollRequests || completedRollRequests.length === 0) {
        console.warn("sendCompletedRolls called with no queued roll requests.");
        // Maybe re-enable submit button? Or backend handles empty list gracefully.
        return;
    }

    console.log(`Submitting ${completedRollRequests.length} roll request(s):`, completedRollRequests);

    try {
        console.debug(`Sending POST request to ${API_SUBMIT_ROLLS_URL}`);
        const response = await fetch(API_SUBMIT_ROLLS_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(completedRollRequests),
        });
        console.debug(`Received response status after submit rolls: ${response.status}`);

        const responseData = await response.json();

        if (!response.ok) {
            const errorMsg = responseData.error || responseData.message || `HTTP error! status: ${response.status}`;
            console.warn("Parsed error data from backend:", responseData);
            addMessageToHistory('System', `(Error submitting rolls: ${errorMsg})`);
            throw new Error(errorMsg);
        }

        console.log("Received AI Response Object after submitting rolls:", responseData);

        // Process Successful Response - Update the entire UI
        if (uiUpdateCallback) {
            // Pass the correct callbacks for the *next* UI state
            uiUpdateCallback(responseData, sendActionCallbackForUI, sendSubmitRollsCallbackForUI);
        } else {
            console.error("UI Update callback not registered in api.js");
        }

    } catch (error) {
        console.error('Error submitting rolls:', error);
        // Error message added above if !response.ok
        if (typeof response === 'undefined' || response?.ok) {
            const errorText = `Error: ${error.message || 'Communication failed.'}`;
            addMessageToHistory('System', `(System Error submitting rolls: ${errorText})`);
        }
        // Let the UI update function handle enabling/disabling inputs based on the response
    }
    console.log("sendCompletedRolls finished.");
}

// Function to fetch the initial game state
export async function fetchInitialState() {
    console.log("Fetching initial game state...");
    try {
        const response = await fetch(API_GAME_STATE_URL);
        console.debug(`Initial state response status: ${response.status}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const initialState = await response.json();
        console.log("Received initial state:", initialState);

        // Update UI using the initial state
        if (uiUpdateCallback) {
            uiUpdateCallback(initialState, sendActionCallbackForUI, sendSubmitRollsCallbackForUI);
        } else {
            console.error("UI Update callback not registered in api.js");
        }

        console.log("Initial state processed successfully.");

    } catch (error) {
        console.error('Error fetching initial state:', error);
        addMessageToHistory('System', `(System Error: Failed to load game state. Please refresh.)`);
        // Clear critical UI elements on load failure
        // updateUI({}, sendActionCallbackForUI, sendRollRequestCallbackForUI); // Send empty state?
        document.getElementById('dice-requests').innerHTML = '';
        document.getElementById('party-list').innerHTML = '<li>Error loading</li>';
    }
}

// Function called by UI when backend indicates next step needed
export async function triggerNextStep() {
    if (isTriggeringNextStep) {
        console.warn("Already triggering next step. Ignoring duplicate request.");
        return;
    }
    console.log("Attempting to trigger next backend step (e.g., NPC turn)...");
    isTriggeringNextStep = true;
    // Optionally disable inputs here or rely on UI update from response
    // disableInputs(); // Maybe too aggressive? Let UI handle based on response.

    try {
        console.debug(`Sending POST request to ${API_TRIGGER_NEXT_STEP_URL}`);
        const response = await fetch(API_TRIGGER_NEXT_STEP_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            // No body needed for this trigger, backend checks current state
        });
        console.debug(`Received response status from trigger: ${response.status}`);

        const responseData = await response.json();

        if (!response.ok) {
            const errorMsg = responseData.error || responseData.message || `HTTP error! status: ${response.status}`;
            console.warn("Parsed error data from backend trigger:", responseData);
            addMessageToHistory('System', `(Error triggering next step: ${errorMsg})`);
            // Throw error to be caught below
            throw new Error(errorMsg);
        }

        console.log("Received AI Response Object after triggering next step:", responseData);

        // Process Successful Response - Update the entire UI
        // This response might *also* contain needs_backend_trigger=true if another NPC follows
        if (uiUpdateCallback) {
            uiUpdateCallback(responseData, sendActionCallbackForUI, sendSubmitRollsCallbackForUI);
        } else {
            console.error("UI Update callback not registered in api.js");
        }

    } catch (error) {
        console.error('Error triggering next step:', error);
        // Error message added above if !response.ok
        if (typeof response === 'undefined' || response?.ok) {
            const errorText = `Error: ${error.message || 'Communication failed.'}`;
            addMessageToHistory('System', `(System Error triggering next step: ${errorText})`);
        }
        // Let the UI update function handle enabling/disabling inputs based on the response
    } finally {
        isTriggeringNextStep = false; // Release lock
        console.log("triggerNextStep finished.");
    }
}