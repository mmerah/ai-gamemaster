import { disableInputs } from './inputControls.js';

const diceRequestsEl = document.getElementById('dice-requests');
const submitRollsBtnContainer = document.getElementById('submit-rolls-btn-container');
const submitRollsBtn = document.getElementById('submit-rolls-btn');

// Stores roll request data for submission
let completedPlayerRolls = [];

async function handlePlayerRollButtonClick(button) {
    button.disabled = true;
    button.textContent = `Rolling...`;
    button.classList.add('roll-neutral');

    const rollRequestData = {
        request_id: button.dataset.requestId,
        character_id: button.dataset.characterId,
        roll_type: button.dataset.requestType,
        dice_formula: button.dataset.diceFormula,
        skill: button.dataset.skill || undefined,
        ability: button.dataset.ability || undefined,
        dc: button.dataset.dc ? parseInt(button.dataset.dc, 10) : undefined,
        reason: button.dataset.reason,
    };

    try {
        // Perform the roll immediately via API
        const response = await fetch('/api/perform_roll', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(rollRequestData)
        });

        const rollResult = await response.json();

        if (response.ok && !rollResult.error) {
            // Display the roll result immediately
            displayRollResult(button, rollResult);
            
            // Store the completed roll result for submission
            completedPlayerRolls.push(rollResult);
            console.log("Roll completed and stored:", rollResult);
            
            if (submitRollsBtn) submitRollsBtn.disabled = false;
        } else {
            // Handle error
            button.textContent = rollResult.error || 'Roll failed';
            button.classList.remove('roll-neutral');
            button.classList.add('roll-error');
            console.error("Roll failed:", rollResult.error);
        }
    } catch (error) {
        // Handle network or other errors
        button.textContent = 'Network error';
        button.classList.remove('roll-neutral');
        button.classList.add('roll-error');
        console.error("Network error during roll:", error);
    }
}

function displayRollResult(button, result) {
    button.classList.remove('roll-neutral');
    
    // Use the detailed result_message for the button text
    button.textContent = result.result_message || `${result.character_name} rolled ${result.total_result}`;

    if (result.success === true) {
        button.classList.add('roll-success');
    } else if (result.success === false) {
        button.classList.add('roll-failure');
    } else if (result.error) {
        button.classList.add('roll-error');
        button.textContent = result.error;
    } else { // Neutral outcome (e.g. initiative, damage roll without DC)
        button.classList.add('roll-neutral');
    }
}

export function applyRollResultsToButtons(submittedRollResults) {
    if (!submittedRollResults || submittedRollResults.length === 0) {
        return;
    }
    console.log("Applying submitted roll results to buttons:", submittedRollResults);

    submittedRollResults.forEach(result => {
        // Find the button using both request_id and character_id for precision
        const buttonSelector = `.dice-roll-button[data-request-id="${result.request_id}"][data-character-id="${result.character_id}"]`;
        const button = document.querySelector(buttonSelector);

        if (button) {
            displayRollResult(button, result);
            button.disabled = true; // Ensure it stays disabled after submission
        } else {
            console.warn(`Could not find button for roll result: ReqID=${result.request_id}, CharID=${result.character_id}`);
        }
    });
}

export function displayDiceRequests(requests, partyData) {
    if (!diceRequestsEl || !submitRollsBtnContainer || !submitRollsBtn) return;

    // It's important that completedPlayerRolls is cleared *before* new request buttons are made,
    // as new buttons will add to this list upon click.
    completedPlayerRolls = []; 

    diceRequestsEl.innerHTML = '';
    submitRollsBtnContainer.style.display = 'none';
    submitRollsBtn.disabled = true;

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
