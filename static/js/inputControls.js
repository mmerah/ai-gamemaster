const freeChoiceInputEl = document.getElementById('free-choice-input');
const submitActionBtnEl = document.getElementById('submit-action-btn');
const diceRequestsEl = document.getElementById('dice-requests');
const submitRollsBtn = document.getElementById('submit-rolls-btn');

export function disableInputs(disableFreeText = true) {
    if (freeChoiceInputEl && disableFreeText) {
        freeChoiceInputEl.disabled = true;
    }
    if (submitActionBtnEl) {
        submitActionBtnEl.disabled = true;
    }
    if (diceRequestsEl) {
        diceRequestsEl.querySelectorAll('.dice-roll-button').forEach(button => button.disabled = true);
    }
    if (submitRollsBtn) {
        submitRollsBtn.disabled = true;
    }
}

export function enableInputs(enableFreeText = true) {
    if (freeChoiceInputEl && enableFreeText) {
        freeChoiceInputEl.disabled = false;
    }
    if (submitActionBtnEl) {
        submitActionBtnEl.disabled = false;
    }
    // Re-enable only non-clicked dice roll buttons
    if (diceRequestsEl) {
        diceRequestsEl.querySelectorAll('.dice-roll-button:not(.roll-success):not(.roll-failure):not(.roll-neutral):not(.roll-error)')
            .forEach(button => button.disabled = false);
    }
    // Submit rolls button is enabled by diceRequestsUI when a roll is queued
    // if (submitRollsBtn) {
    //     // Enable only if there are completedPlayerRolls (state managed in diceRequestsUI)
    // }
}

export function clearFreeTextInput() {
    if (freeChoiceInputEl) {
        freeChoiceInputEl.value = '';
    }
}