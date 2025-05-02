      
import { fetchInitialState, sendAction, sendCompletedRolls, registerUICallbacks } from './api.js';
import { updateUI, addMessageToHistory, disableInputs, clearFreeTextInput, getCompletedPlayerRolls } from './ui.js';

document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM fully loaded and parsed - main.js executing");

    // --- Get DOM Elements needed for listeners ---
    const freeChoiceInputEl = document.getElementById('free-choice-input');
    const submitActionBtnEl = document.getElementById('submit-action-btn');
    const submitRollsBtn = document.getElementById('submit-rolls-btn');

    // --- Register Callbacks ---
    // Pass the UI update function and the action functions to api.js
    // so it can trigger UI updates after API calls complete.
    registerUICallbacks(updateUI, sendAction, sendCompletedRolls);

    // --- Event Listeners ---
    submitActionBtnEl.addEventListener('click', () => {
        console.debug("Submit button clicked.");
        const value = freeChoiceInputEl.value.trim();
        if (!value) {
             console.warn("Empty free text input.");
             addMessageToHistory("System", "Please enter an action.");
             return;
        }
        // Add player message to UI immediately
        addMessageToHistory('Player', `"${value}"`);
        disableInputs(); // Disable inputs before sending
        clearFreeTextInput();
        // Call API function
        sendAction('free_text', value);
    });

    freeChoiceInputEl.addEventListener('keypress', (event) => {
        if (event.key === 'Enter' && !freeChoiceInputEl.disabled) {
            console.debug("Enter key pressed in input.");
            event.preventDefault(); // Prevent default form submission
            const value = freeChoiceInputEl.value.trim();
             if (!value) {
                 console.warn("Empty free text input on Enter.");
                 addMessageToHistory("System", "Please enter an action.");
                 return;
             }
            // Add player message to UI immediately
            addMessageToHistory('Player', `"${value}"`);
            disableInputs(); // Disable inputs before sending
            clearFreeTextInput();
            // Call API function
            sendAction('free_text', value);
        }
    });

    // Add listener for the "Submit Rolls" button
    submitRollsBtn.addEventListener('click', () => {
        console.log("Submit Rolls button clicked.");
        // Disable button immediately
        submitRollsBtn.disabled = true;
        // Disable any remaining active roll buttons (optional, good practice)
        document.querySelectorAll('#dice-requests .dice-roll-button:not(:disabled)').forEach(btn => {
            btn.disabled = true;
            btn.classList.add('disabled-secondary');
        });

        // Get the rolls using the exported getter function
        const rollsToSubmit = getCompletedPlayerRolls();
        sendCompletedRolls(rollsToSubmit);
    });

    // --- Initial Load ---
    fetchInitialState();

}); // End DOMContentLoaded

    