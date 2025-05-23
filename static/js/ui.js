import { triggerNextStep } from './api.js';
import { addMessageToHistory, clearChatHistory, ensureScrollToBottom } from './chatHistoryUI.js';
import { updatePartyList } from './partyUI.js';
import { updateMap } from './mapUI.js';
import { displayDiceRequests, applyRollResultsToButtons } from './diceRequestsUI.js';
import { updateCombatStatus } from './combatStatusUI.js';
import { enableInputs, disableInputs } from './inputControls.js';

// Orchestrates updates to various UI components.
export function updateUI(gameState, sendActionCallback, sendSubmitRollsCallback) {
    if (!gameState || typeof gameState !== 'object') {
        console.error("Invalid game state received for UI update:", gameState);
        // Use addMessageToHistory from chatHistoryUI.js directly
        addMessageToHistory("System", "(Error: Received invalid state from server.)");
        disableInputs(true);
        return;
    }
    console.log("Orchestrating UI update from game state:", gameState);

    // Handle backend error messages displayed in chat
    if (gameState.error) {
        console.warn("Backend returned an error message in game state:", gameState.error);
        addMessageToHistory("System", `(Error: ${gameState.error})`);
        if (gameState.error !== "AI is busy processing previous request." && gameState.error !== "AI is busy") {
            enableInputs();
        } else {
            disableInputs(true);
        }
        return;
    }

    // If there were submitted rolls in this response, update their buttons first
    if (gameState.submitted_roll_results && Array.isArray(gameState.submitted_roll_results)) {
        applyRollResultsToButtons(gameState.submitted_roll_results);
    }

    clearChatHistory();
    (gameState.chat_history || []).forEach(entry => {
        addMessageToHistory(entry.sender, entry.message, entry.gm_thought || null);
    });
    
    // Ensure chat scrolls to bottom after loading all messages
    ensureScrollToBottom();

    updatePartyList(gameState.party || []);
    updateMap(gameState.location, gameState.location_description);
    updateCombatStatus(gameState);
    
    // Display NEW dice requests from the AI (if any)
    // This will clear and rebuild the #dice-requests area
    displayDiceRequests(gameState.dice_requests || [], gameState.party || []);

    const hasPendingPlayerRequests = gameState.dice_requests && gameState.dice_requests.length > 0;
    if (!hasPendingPlayerRequests) {
        enableInputs();
    } else {
        // Free text input is disabled by displayDiceRequests if rolls are shown
        // Dice buttons are managed by diceRequestsUI
    }

    const needsBackendTrigger = gameState.needs_backend_trigger === true;
    console.log(`UI Orchestrator: Backend indicates needs_backend_trigger: ${needsBackendTrigger}`);

    if (needsBackendTrigger && !hasPendingPlayerRequests) {
        console.log("Needs backend trigger and no player requests pending. Scheduling trigger API call...");
        disableInputs(true);
        setTimeout(() => {
            triggerNextStep();
        }, 100);
    } else if (needsBackendTrigger && hasPendingPlayerRequests) {
        console.log("Needs backend trigger, but UI is waiting for player rolls first.");
    }
}
