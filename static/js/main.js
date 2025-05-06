import { fetchInitialState, sendAction, sendCompletedRolls, registerUICallbacks } from './api.js';
import { updateUI } from './ui.js';
import { addMessageToHistory } from './chatHistoryUI.js';
import { getCompletedPlayerRolls } from './diceRequestsUI.js';
import { disableInputs, clearFreeTextInput } from './inputControls.js';

document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM fully loaded - main.js executing");

    const freeChoiceInputEl = document.getElementById('free-choice-input');
    const submitActionBtnEl = document.getElementById('submit-action-btn');
    const submitRollsBtn = document.getElementById('submit-rolls-btn');

    // Register the main UI update callback with api.js
    // sendAction and sendCompletedRolls are passed for api.js to call them,
    // though updateUI itself doesn't use these specific callbacks.
    registerUICallbacks(updateUI, sendAction, sendCompletedRolls);

    function handleSendAction() {
        const value = freeChoiceInputEl.value.trim();
        if (!value) {
            addMessageToHistory("System", "Please enter an action."); // Uses chatHistoryUI.js
            return;
        }
        addMessageToHistory('Player', `"${value}"`); // Uses chatHistoryUI.js
        disableInputs(true); // Uses inputControls.js
        clearFreeTextInput(); // Uses inputControls.js
        sendAction('free_text', value); // Uses api.js
    }

    submitActionBtnEl.addEventListener('click', handleSendAction);
    freeChoiceInputEl.addEventListener('keypress', (event) => {
        if (event.key === 'Enter' && !freeChoiceInputEl.disabled) {
            event.preventDefault();
            handleSendAction();
        }
    });

    submitRollsBtn.addEventListener('click', () => {
        console.log("Submit Rolls button clicked.");
        submitRollsBtn.disabled = true;
        document.querySelectorAll('#dice-requests .dice-roll-button:not(:disabled)').forEach(btn => {
            btn.disabled = true;
            btn.classList.add('disabled-secondary');
        });
        const rollsToSubmit = getCompletedPlayerRolls(); // Uses diceRequestsUI.js
        sendCompletedRolls(rollsToSubmit); // Uses api.js
    });

    fetchInitialState(); // Uses api.js
});