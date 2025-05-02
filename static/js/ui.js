import { triggerNextStep } from './api.js';

// --- State within UI module ---
let completedPlayerRolls = []; // Store results before submitting
let localPartyData = []; // Keep party data for modifier calculation

// --- DOM Element Access ---
// It's often better to get elements in the functions that use them or pass them as args
const partyListEl = document.getElementById('party-list');
const chatHistoryEl = document.getElementById('chat-history');
const freeChoiceInputEl = document.getElementById('free-choice-input');
const submitActionBtnEl = document.getElementById('submit-action-btn');
const mapLocationNameEl = document.getElementById('map-location-name');
const mapDescriptionEl = document.getElementById('map-description');
const diceRequestsEl = document.getElementById('dice-requests');
const submitRollsBtnContainer = document.getElementById('submit-rolls-btn-container');
const submitRollsBtn = document.getElementById('submit-rolls-btn');

// --- UI Update Functions ---

export function addMessageToHistory(sender, message, thought = null) {
    if (message === null || typeof message === 'undefined') {
        console.warn(`addMessageToHistory called with null/undefined message for sender ${sender}. Displaying placeholder.`);
        message = `(${sender} message content missing)`; // Provide a placeholder
    }

    console.debug(`Adding message to history: Sender=${sender}, Thought=${!!thought}`);
    const messageContainer = document.createElement('div');
    messageContainer.classList.add('message-container', sender.toLowerCase() + '-container');

    const messageEl = document.createElement('p');
    // Basic markdown rendering
    messageEl.innerHTML = message.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>').replace(/\*(.*?)\*/g, '<i>$1</i>');
    messageEl.classList.add(sender.toLowerCase() + '-message');

    // Style system messages differently if needed
    if (sender === 'System') {
        messageEl.classList.add('system-message'); // Add a specific class
    }

    if (sender === 'GM' && thought) {
        const thoughtToggle = document.createElement('button');
        thoughtToggle.textContent = '🤔';
        thoughtToggle.classList.add('thought-toggle');
        thoughtToggle.title = 'Show/Hide GM Thought Process';

        const thoughtContent = document.createElement('div');
        thoughtContent.classList.add('thought-content');
        thoughtContent.textContent = thought;
        thoughtContent.style.display = 'none'; // Start hidden

        thoughtToggle.addEventListener('click', () => {
            const isHidden = thoughtContent.style.display === 'none';
            thoughtContent.style.display = isHidden ? 'block' : 'none';
            thoughtToggle.textContent = isHidden ? '✅' : '🤔';
        });

        messageContainer.appendChild(thoughtToggle);
        messageContainer.appendChild(messageEl);
        messageContainer.appendChild(thoughtContent);
    } else {
        messageContainer.appendChild(messageEl);
    }

    chatHistoryEl.appendChild(messageContainer);
    // Scroll to bottom
    chatHistoryEl.scrollTop = chatHistoryEl.scrollHeight;
}

export function updatePartyList(party) {
    console.debug("Updating party list UI", party);
    localPartyData = party || [];
    partyListEl.innerHTML = ''; // Clear existing
    if (!party || party.length === 0) {
        partyListEl.innerHTML = '<li>No party data</li>';
        return;
    }
    party.forEach(char => {
        const li = document.createElement('li');
        // Display Name, Class, Level, HP, Conditions
        let status = `HP: ${char.hp}/${char.max_hp}`;
        if (char.conditions && char.conditions.length > 0) {
            status += ` | Cond: ${char.conditions.join(', ')}`;
        }
        li.textContent = `${char.name} (${char.race} ${char.char_class} ${char.level}) | ${status}`;
        li.dataset.charId = char.id;

        // Update title attribute for hover info
        const stats = char.stats || {};
        li.title = `AC:${char.ac||'?'} | STR:${stats.STR||'?'} DEX:${stats.DEX||'?'} CON:${stats.CON||'?'} INT:${stats.INT||'?'} WIS:${stats.WIS||'?'} CHA:${stats.CHA||'?'}`;
        // Add click listener for details later if needed
        partyListEl.appendChild(li);
    });
}

// Needs access to the partyData for names, but not for calculations
export function displayDiceRequests(requests, partyData) {
    console.debug("Displaying dice requests", requests);
    diceRequestsEl.innerHTML = '';
    submitRollsBtnContainer.style.display = 'none';
    submitRollsBtn.disabled = true;
    completedPlayerRolls = []; // Clear previous request storage

    if (!requests || requests.length === 0) {
        diceRequestsEl.style.display = 'none';
        return;
    }

    diceRequestsEl.style.display = 'block';
    disableInputs(true);

    const requestList = document.createElement('ul');
    let hasPlayerRequests = false;

    requests.forEach(req => {
        // Determine label (Skill/Save/etc.)
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
        if (charIds.length === 0) { /* ... error handling ... */ return; }

        charIds.forEach(charId => {
            // Find character name from partyData
            const character = partyData.find(c => c.id === charId);
            // IMPORTANT: Only display buttons for known party members
            if (!character) {
                console.log(`Skipping button display for unknown/NPC ID: ${charId}`);
                return; // Don't show button for NPCs
            }

            hasPlayerRequests = true; // We have at least one player button

            const charLi = document.createElement('li');
            charLi.classList.add('dice-request-character');

            const rollButton = document.createElement('button');
            rollButton.classList.add('dice-roll-button');
            rollButton.textContent = `Roll ${req.dice_formula} for ${character.name}`;
            rollButton.title = `Roll ${rollLabel} for ${character.name}. Formula: ${req.dice_formula}. Reason: ${req.reason}`;

            // Store data needed for local roll AND backend submission
            rollButton.dataset.requestId = req.request_id;
            rollButton.dataset.characterId = charId;
            rollButton.dataset.characterName = character.name;
            rollButton.dataset.diceFormula = req.dice_formula;
            rollButton.dataset.requestType = req.type;
            rollButton.dataset.reason = req.reason;
            rollButton.dataset.dc = req.dc || '';
            if (req.skill) rollButton.dataset.skill = req.skill;
            if (req.ability) rollButton.dataset.ability = req.ability;

            rollButton.addEventListener('click', (event) => {
                handlePlayerRollButtonClick(event.target);
            });

            charLi.appendChild(rollButton);
            requestList.appendChild(charLi);
        });
    });

    diceRequestsEl.appendChild(requestList);

    // Show "Submit Rolls" button only if there were player requests displayed
    if (hasPlayerRequests) {
        submitRollsBtnContainer.style.display = 'block';
        // Keep submit button disabled until a roll is made
        submitRollsBtn.disabled = true;
        // Attach listener here or in main.js
        // Let's assume main.js attaches it based on ID 'submit-rolls-btn'
    }
}

// --- Handler for Player Roll Button Click ---
function handlePlayerRollButtonClick(button) {
    // 1. Disable the clicked button immediately
    button.disabled = true;
    button.textContent = `Queued: ${button.dataset.characterName} - ${button.dataset.requestType}`;
    button.classList.add('roll-neutral'); // Style as queued/pending

    // 2. Get data from button dataset and store it
    const rollRequestData = {
        // Extract data needed by backend perform_roll
        request_id: button.dataset.requestId,
        character_id: button.dataset.characterId,
        roll_type: button.dataset.requestType,
        dice_formula: button.dataset.diceFormula,
        skill: button.dataset.skill,
        ability: button.dataset.ability,
        dc: button.dataset.dc ? parseInt(button.dataset.dc, 10) : null,
        reason: button.dataset.reason,
        // We don't include results here anymore
    };

    completedPlayerRolls.push(rollRequestData);
    console.log("Stored roll request:", rollRequestData);

    // 3. Enable the "Submit Rolls" button now that at least one roll is queued
    submitRollsBtn.disabled = false;

    // Optional: Disable other buttons for the same request_id? Maybe not needed.
}

export function updateMap(locationName, description) {
    console.debug("Updating map display", { locationName, description });
    mapLocationNameEl.textContent = locationName || "Unknown Location";
    mapDescriptionEl.textContent = description || "";
    // Later, could add map generation call here
}

export function disableInputs(disableFreeText = true) {
    console.debug("Disabling inputs...");
    if (disableFreeText) {
        freeChoiceInputEl.disabled = true;
    }
    submitActionBtnEl.disabled = true;
    // Keep disabling dice buttons if needed (though usually done when clicked)
    diceRequestsEl.querySelectorAll('.dice-roll-button').forEach(button => button.disabled = true);
    submitRollsBtn.disabled = true; 
}

export function enableInputs() {
    console.debug("Enabling inputs...");
    freeChoiceInputEl.disabled = false;
    submitActionBtnEl.disabled = false;
    // Re-enable pending dice roll buttons if any exist and weren't clicked
    diceRequestsEl.querySelectorAll('.dice-roll-button:not(.roll-success):not(.roll-failure):not(.roll-neutral):not(.roll-error)').forEach(button => button.disabled = false);
    // Enable submit rolls button *only* if there are queued rolls
    submitRollsBtn.disabled = completedPlayerRolls.length === 0;
}

export function clearFreeTextInput() {
    freeChoiceInputEl.value = '';
}

// --- Add element for Combat Status ---
const combatStatusEl = document.getElementById('combat-status');

// Function to update the entire UI based on game state object from backend
export function updateUI(gameState, sendActionCallback, sendSubmitRollsCallback) {
    if (!gameState || typeof gameState !== 'object') {
        console.error("Invalid game state received for UI update:", gameState);
        addMessageToHistory("System", "(Error: Received invalid state from server.)");
        // Potentially disable everything on critical error
        disableInputs(true);
        return;
    }

    console.log("Updating UI from game state:", gameState);

    // Check for backend error messages first
    if (gameState.error) {
        console.warn("Backend returned an error message:", gameState.error);
        addMessageToHistory("System", `(Error: ${gameState.error})`);
        // Decide if inputs should be enabled despite the error
        // If it was a 429 (busy), keep inputs disabled. Otherwise, maybe enable?
        // Let's enable unless it's specifically a busy error.
        if (gameState.error !== "AI is busy processing previous request.") {
            // Enable input if it wasn't a busy error, allowing user to try again
            enableInputs();
        } else {
            // Keep inputs disabled if AI is busy
            disableInputs(true);
        }
        // Don't proceed with trigger check if there was an error
        return;
    }

    // Update chat history first
    chatHistoryEl.innerHTML = ''; // Clear current display
    (gameState.chat_history || []).forEach(entry => {
        addMessageToHistory(entry.sender, entry.message, entry.gm_thought || null);
    });

    // Update party list
    updatePartyList(gameState.party || []);

    // Update map
    updateMap(gameState.location, gameState.location_description);

    // Update Combat Status Display
    updateCombatStatus(gameState);

    // Display dice requests
    // Pass party data for name lookups in displayDiceRequests
    displayDiceRequests(gameState.dice_requests || [], gameState.party || []);

    // Enable/disable inputs based on pending requests
    const hasPendingPlayerRequests = gameState.dice_requests && gameState.dice_requests.length > 0;
    if (!gameState.dice_requests || gameState.dice_requests.length === 0) {
        enableInputs(); // Enable free text
        diceRequestsEl.style.display = 'none'; // Ensure hidden
        submitRollsBtnContainer.style.display = 'none';
        submitRollsBtn.disabled = true;
    } else {
        // Inputs (free text) disabled by displayDiceRequests if needed
        // Dice buttons are enabled/disabled individually
        // Submit button enabled by handlePlayerRollButtonClick
        // submitRollsBtnContainer visibility handled by displayDiceRequests
    }

    // Check and Trigger Next Step
    const needsTrigger = gameState.needs_backend_trigger === true;
    console.log(`Backend indicates needs_backend_trigger: ${needsTrigger}`);
    if (needsTrigger && !hasPendingPlayerRequests) {
        // IMPORTANT: Only trigger if there are no pending player requests
        console.log("Needs backend trigger and no player requests pending. Scheduling trigger...");
        // Disable inputs while waiting for the trigger response
        disableInputs(true);
        // Add a small delay to allow the current UI update to render
        setTimeout(() => {
            triggerNextStep(); // Call the API function
        }, 100); // 100ms delay, adjust as needed
    } else if (needsTrigger && hasPendingPlayerRequests) {
        console.log("Needs backend trigger, but waiting for player rolls first.");
        // UI is already set up for player rolls, do nothing extra here.
    }
}

// Combat status update
function updateCombatStatus(gameState) {
    const combatStatusEl = document.getElementById('combat-status');
    if (!combatStatusEl) {
        console.warn("Combat status display element not found (#combat-status).");
        return;
    }

    combatStatusEl.innerHTML = ''; // Clear previous status
    combatStatusEl.style.display = 'none'; // Hide by default
    const combatInfo = gameState.combat_info;
    if (combatInfo && combatInfo.is_active) {
        combatStatusEl.style.display = 'block';

        const roundEl = document.createElement('p');
        roundEl.style.margin = '0 0 5px 0';
        roundEl.innerHTML = `<strong>Combat Round: ${combatInfo.round}</strong>`;
        combatStatusEl.appendChild(roundEl);

        const turnEl = document.createElement('p');
        turnEl.style.margin = '0 0 10px 0';
        turnEl.innerHTML = `Current Turn: <strong style="color: #c62828;">${combatInfo.current_turn || 'N/A'}</strong>`;
        combatStatusEl.appendChild(turnEl);

        const turnOrderTitle = document.createElement('p');
        turnOrderTitle.style.margin = '5px 0 2px 0';
        turnOrderTitle.innerHTML = '<em>Turn Order:</em>';
        combatStatusEl.appendChild(turnOrderTitle);

        const turnOrderList = document.createElement('ol');
        turnOrderList.style.margin = '0';
        turnOrderList.style.paddingLeft = '20px';
        (combatInfo.turn_order || []).forEach((c) => {
            const li = document.createElement('li');
            li.style.marginBottom = '3px';
            let statusText = "";
            const player = (gameState.party || []).find(p => p.id === c.id);
            if (player) {
                statusText = `(HP: ${player.hp}/${player.max_hp}${player.conditions.length > 0 ? ', Cond: ' + player.conditions.join(', ') : ''})`;
            } else if (combatInfo.monster_status && combatInfo.monster_status[c.id]) {
                const mStat = combatInfo.monster_status[c.id];
                statusText = `(HP: ${mStat.hp ?? '?'}/${mStat.initial_hp ?? '?'}${mStat.conditions && mStat.conditions.length > 0 ? ', Cond: ' + mStat.conditions.join(', ') : ''})`;
            }

            li.innerHTML = `${c.name} (${c.initiative}) ${statusText}`;
            if (c.id === combatInfo.current_turn_id) {
                li.style.fontWeight = 'bold';
                li.style.color = '#c62828';
                li.style.borderLeft = '3px solid #ff9800';
                li.style.paddingLeft = '5px';
                li.style.listStyle = '"➠ "';
            } else {
                li.style.listStyle = '"◦ "';
            }
            turnOrderList.appendChild(li);
        });
        combatStatusEl.appendChild(turnOrderList);
    }
}

export function getCompletedPlayerRolls() {
    // Return a copy to prevent external modification if desired,
    // or the array itself if direct modification isn't a concern here.
    // Let's return a copy for safety.
    return [...completedPlayerRolls];
}
