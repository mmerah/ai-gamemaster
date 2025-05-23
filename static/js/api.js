import { updateUI } from './ui.js';
import { addMessageToHistory } from './chatHistoryUI.js';

const API_PLAYER_ACTION_URL = '/api/player_action';
const API_SUBMIT_ROLLS_URL = '/api/submit_rolls';
const API_GAME_STATE_URL = '/api/game_state';
const API_TRIGGER_NEXT_STEP_URL = '/api/trigger_next_step';
const API_RETRY_LAST_AI_REQUEST_URL = '/api/retry_last_ai_request';

let uiUpdateCallback = null;
let sendActionCallbackForUI = null;
let sendSubmitRollsCallbackForUI = null;

let isTriggeringNextStep = false;
let isRetryingLastRequest = false;

export function registerUICallbacks(updateCallback, actionCallback, submitRollsCallback) {
    uiUpdateCallback = updateCallback;
    sendActionCallbackForUI = actionCallback;
    sendSubmitRollsCallbackForUI = submitRollsCallback;
}

export async function sendAction(actionType, value) {
    console.log(`Sending action: Type=${actionType}, Value=${JSON.stringify(value)}`);
    // ... (rest of sendAction, uses addMessageToHistory in catch)
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
            throw new Error(errorMsg);
        }
        console.log("Received AI Response Object after action:", responseData);
        if (uiUpdateCallback) {
            uiUpdateCallback(responseData, sendActionCallbackForUI, sendSubmitRollsCallbackForUI);
        }
    } catch (error) {
        console.error('Error sending action:', error);
        addMessageToHistory('System', `(System Error sending action: ${error.message || 'Communication failed.'})`);
        // Potentially call uiUpdateCallback with an error state or re-enable inputs if appropriate
        if (uiUpdateCallback) {
            // Create a minimal error state to pass to UI update
            const errorState = { error: `Action failed: ${error.message}` };
            uiUpdateCallback(errorState, sendActionCallbackForUI, sendSubmitRollsCallbackForUI);
        }
    }
    console.log("sendAction finished.");
}

export async function sendCompletedRolls(completedRollRequests) {
    if (!completedRollRequests || completedRollRequests.length === 0) {
        console.warn("sendCompletedRolls called with no queued roll requests.");
        return;
    }
    console.log(`Submitting ${completedRollRequests.length} completed roll result(s):`, completedRollRequests);
    // ... (rest of sendCompletedRolls, uses addMessageToHistory in catch)
    try {
        console.debug(`Sending POST request to ${API_SUBMIT_ROLLS_URL}`);
        const response = await fetch(API_SUBMIT_ROLLS_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                roll_results: completedRollRequests
            }),
        });
        console.debug(`Received response status after submit rolls: ${response.status}`);
        const responseData = await response.json();
        if (!response.ok) {
            const errorMsg = responseData.error || responseData.message || `HTTP error! status: ${response.status}`;
            addMessageToHistory('System', `(Error submitting rolls: ${errorMsg})`); // Add message before throwing
            throw new Error(errorMsg);
        }
        console.log("Received AI Response Object after submitting rolls:", responseData);
        if (uiUpdateCallback) {
            uiUpdateCallback(responseData, sendActionCallbackForUI, sendSubmitRollsCallbackForUI);
        }
    } catch (error) {
        console.error('Error submitting rolls:', error);
        // Error message already added if !response.ok
        if (error.message && !error.message.startsWith("HTTP error!")) { // Avoid double message for HTTP errors
             addMessageToHistory('System', `(System Error submitting rolls: ${error.message || 'Communication failed.'})`);
        }
        if (uiUpdateCallback) {
            const errorState = { error: `Submit rolls failed: ${error.message}` };
            uiUpdateCallback(errorState, sendActionCallbackForUI, sendSubmitRollsCallbackForUI);
        }
    }
    console.log("sendCompletedRolls finished.");
}

export async function fetchInitialState() {
    console.log("Fetching initial game state..."); // THIS LOG IS KEY
    try {
        const response = await fetch(API_GAME_STATE_URL);
        console.debug(`Initial state response status: ${response.status}`); // THIS LOG IS KEY
        if (!response.ok) {
            // Try to get error message from response body if possible
            let errorData = { message: `HTTP error! status: ${response.status}` };
            try {
                errorData = await response.json();
            } catch (e) { /* ignore if body isn't json */ }
            throw new Error(errorData.error || errorData.message || `HTTP error! status: ${response.status}`);
        }
        const initialState = await response.json();
        console.log("Received initial state:", initialState);

        if (uiUpdateCallback) {
            uiUpdateCallback(initialState, sendActionCallbackForUI, sendSubmitRollsCallbackForUI);
        } else {
            console.error("UI Update callback not registered in api.js");
        }
        console.log("Initial state processed successfully by api.js.");
    } catch (error) {
        console.error('Error fetching initial state:', error);
        addMessageToHistory('System', `(System Error: Failed to load game state. ${error.message}. Please refresh.)`);
        // Clear critical UI elements on load failure by passing an empty/error state to updateUI
        if (uiUpdateCallback) {
            const errorState = {
                party: [],
                location: "Error",
                location_description: "Could not load game data.",
                chat_history: [{ sender: "System", message: "Failed to load game state." }],
                dice_requests: [],
                combat_info: null,
                error: "Failed to load initial game state." // Explicit error for ui.js
            };
            uiUpdateCallback(errorState, sendActionCallbackForUI, sendSubmitRollsCallbackForUI);
        }
    }
}

export async function triggerNextStep() {
    if (isTriggeringNextStep) {
        console.warn("Already triggering next step. Ignoring duplicate request.");
        return;
    }
    console.log("Attempting to trigger next backend step (e.g., NPC turn)...");
    isTriggeringNextStep = true;
    // ... (rest of triggerNextStep, uses addMessageToHistory in catch)
    try {
        console.debug(`Sending POST request to ${API_TRIGGER_NEXT_STEP_URL}`);
        const response = await fetch(API_TRIGGER_NEXT_STEP_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });
        console.debug(`Received response status from trigger: ${response.status}`);
        const responseData = await response.json();
        if (!response.ok) {
            const errorMsg = responseData.error || responseData.message || `HTTP error! status: ${response.status}`;
            addMessageToHistory('System', `(Error triggering next step: ${errorMsg})`);
            throw new Error(errorMsg);
        }
        console.log("Received AI Response Object after triggering next step:", responseData);
        if (uiUpdateCallback) {
            uiUpdateCallback(responseData, sendActionCallbackForUI, sendSubmitRollsCallbackForUI);
        }
    } catch (error) {
        console.error('Error triggering next step:', error);
        if (error.message && !error.message.startsWith("HTTP error!")) {
            addMessageToHistory('System', `(System Error triggering next step: ${error.message || 'Communication failed.'})`);
        }
        if (uiUpdateCallback) {
            const errorState = { error: `Trigger next step failed: ${error.message}` };
            uiUpdateCallback(errorState, sendActionCallbackForUI, sendSubmitRollsCallbackForUI);
        }
    } finally {
        isTriggeringNextStep = false;
        console.log("triggerNextStep finished.");
    }
}

export async function retryLastAIRequest() {
    if (isRetryingLastRequest) {
        console.warn("Already retrying last request. Ignoring duplicate request.");
        return;
    }
    console.log("Attempting to retry last AI request...");
    isRetryingLastRequest = true;
    
    try {
        console.debug(`Sending POST request to ${API_RETRY_LAST_AI_REQUEST_URL}`);
        const response = await fetch(API_RETRY_LAST_AI_REQUEST_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });
        console.debug(`Received response status from retry: ${response.status}`);
        const responseData = await response.json();
        if (!response.ok) {
            const errorMsg = responseData.error || responseData.message || `HTTP error! status: ${response.status}`;
            addMessageToHistory('System', `(Error retrying last request: ${errorMsg})`);
            throw new Error(errorMsg);
        }
        console.log("Received AI Response Object after retrying last request:", responseData);
        if (uiUpdateCallback) {
            uiUpdateCallback(responseData, sendActionCallbackForUI, sendSubmitRollsCallbackForUI);
        }
    } catch (error) {
        console.error('Error retrying last request:', error);
        if (error.message && !error.message.startsWith("HTTP error!")) {
            addMessageToHistory('System', `(System Error retrying last request: ${error.message || 'Communication failed.'})`);
        }
        if (uiUpdateCallback) {
            const errorState = { error: `Retry last request failed: ${error.message}` };
            uiUpdateCallback(errorState, sendActionCallbackForUI, sendSubmitRollsCallbackForUI);
        }
    } finally {
        isRetryingLastRequest = false;
        console.log("retryLastAIRequest finished.");
    }
}
