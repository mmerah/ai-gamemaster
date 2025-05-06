import { disableInputs } from './inputControls.js';

const diceRequestsEl = document.getElementById('dice-requests');
const submitRollsBtnContainer = document.getElementById('submit-rolls-btn-container');
const submitRollsBtn = document.getElementById('submit-rolls-btn');

// Stores roll request data for submission
let completedPlayerRolls = [];

function handlePlayerRollButtonClick(button) {
    button.disabled = true;
    button.textContent = `Queued: ${button.dataset.characterName} - ${button.dataset.requestType}`;
    button.classList.add('roll-neutral');

    const rollRequestData = {
        request_id: button.dataset.requestId,
        character_id: button.dataset.characterId,
        roll_type: button.dataset.requestType,
        dice_formula: button.dataset.diceFormula,
        skill: button.dataset.skill,
        ability: button.dataset.ability,
        dc: button.dataset.dc ? parseInt(button.dataset.dc, 10) : null,
        reason: button.dataset.reason,
    };

    completedPlayerRolls.push(rollRequestData);
    console.log("Stored roll request for submission:", rollRequestData);
    if (submitRollsBtn) submitRollsBtn.disabled = false;
}

export function displayDiceRequests(requests, partyData) {
    if (!diceRequestsEl || !submitRollsBtnContainer || !submitRollsBtn) return;

    diceRequestsEl.innerHTML = '';
    submitRollsBtnContainer.style.display = 'none';
    submitRollsBtn.disabled = true;
    completedPlayerRolls = []; // Clear previous request storage

    if (!requests || requests.length === 0) {
        diceRequestsEl.style.display = 'none';
        return;
    }

    diceRequestsEl.style.display = 'block';
    disableInputs(true); // Disable free text input while rolls are pending

    const requestList = document.createElement('ul');
    let hasPlayerRequests = false;

    requests.forEach(req => {
        let rollLabel = req.reason;
        if (req.type === 'skill_check' && req.skill) rollLabel = req.skill.charAt(0).toUpperCase() + req.skill.slice(1) + " Check";
        else if (req.type === 'saving_throw' && req.ability) rollLabel = req.ability.toUpperCase() + " Save";
        else if (req.type === 'initiative') rollLabel = "Initiative";
        else if (req.type) rollLabel = req.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());

        const reasonLi = document.createElement('li');
        reasonLi.classList.add('dice-request-reason');
        reasonLi.textContent = `Roll Required: ${rollLabel} ${req.dc ? '(DC ' + req.dc + ')' : ''}`;
        reasonLi.title = `Reason: ${req.reason}`;
        requestList.appendChild(reasonLi);

        const charIds = Array.isArray(req.character_ids) ? req.character_ids : [];
        if (charIds.length === 0) return;

        charIds.forEach(charId => {
            const character = (partyData || []).find(c => c.id === charId);
            if (!character) { // Skip buttons for NPCs/unknown IDs
                console.log(`Skipping roll button for non-party ID: ${charId}`);
                return;
            }
            hasPlayerRequests = true;

            const charLi = document.createElement('li');
            charLi.classList.add('dice-request-character');
            const rollButton = document.createElement('button');
            rollButton.classList.add('dice-roll-button');
            rollButton.textContent = `Roll ${req.dice_formula} for ${character.name}`;
            rollButton.title = `Roll ${rollLabel} for ${character.name}. Formula: ${req.dice_formula}. Reason: ${req.reason}`;
            
            Object.assign(rollButton.dataset, {
                requestId: req.request_id, characterId: charId, characterName: character.name,
                diceFormula: req.dice_formula, requestType: req.type, reason: req.reason,
                dc: req.dc || '', skill: req.skill || '', ability: req.ability || ''
            });
            rollButton.addEventListener('click', (event) => handlePlayerRollButtonClick(event.target));
            charLi.appendChild(rollButton);
            requestList.appendChild(charLi);
        });
    });

    diceRequestsEl.appendChild(requestList);

    if (hasPlayerRequests) {
        submitRollsBtnContainer.style.display = 'block';
        // Submit button remains disabled until a roll is clicked
    }
}

export function getCompletedPlayerRolls() {
    return [...completedPlayerRolls]; // Return a copy
}