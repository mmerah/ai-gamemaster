const combatStatusEl = document.getElementById('combat-status');

export function updateCombatStatus(gameState) {
    if (!combatStatusEl) {
        console.warn("Combat status display element not found (#combat-status).");
        return;
    }

    combatStatusEl.innerHTML = ''; 
    combatStatusEl.style.display = 'none';
    const combatInfo = gameState.combat_info;

    if (combatInfo && combatInfo.is_active) {
        combatStatusEl.style.display = 'block';

        const roundEl = document.createElement('p');
        roundEl.innerHTML = `<strong>Combat Round: ${combatInfo.round}</strong>`;
        combatStatusEl.appendChild(roundEl);

        const turnEl = document.createElement('p');
        turnEl.innerHTML = `Current Turn: <strong style="color: #c62828;">${combatInfo.current_turn || 'N/A'}</strong>`;
        combatStatusEl.appendChild(turnEl);

        const turnOrderTitle = document.createElement('p');
        turnOrderTitle.innerHTML = '<em>Turn Order:</em>';
        combatStatusEl.appendChild(turnOrderTitle);

        const turnOrderList = document.createElement('ol');
        (combatInfo.turn_order || []).forEach((c) => {
            const li = document.createElement('li');
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
                li.style.color = '#c62828'; // Highlight color
                li.style.listStyle = '"➠ "'; // Custom marker for current turn
            } else {
                 li.style.listStyle = '"◦ "'; // Custom marker for other turns
            }
            turnOrderList.appendChild(li);
        });
        combatStatusEl.appendChild(turnOrderList);
    }
}