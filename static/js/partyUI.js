const partyListEl = document.getElementById('party-list');

function getCharacterInitials(name) {
    if (!name) return '?';
    const words = name.trim().split(' ');
    if (words.length === 1) {
        return words[0].substring(0, 2).toUpperCase();
    }
    return words.map(word => word.charAt(0).toUpperCase()).join('').substring(0, 2);
}

function getPortraitImage(characterId, characterName) {
    // Try to load a character portrait image
    // For now, we'll use a placeholder system with initials
    // In the future, this could check for actual image files
    const portraitPath = `/static/images/portraits/${characterId}.jpg`;
    
    // Create a placeholder div with initials
    const portraitDiv = document.createElement('div');
    portraitDiv.className = 'character-portrait';
    portraitDiv.textContent = getCharacterInitials(characterName);
    portraitDiv.title = `${characterName}'s Portrait`;
    
    // You could add logic here to check if an actual image exists
    // and replace the initials with an img element if it does
    
    return portraitDiv;
}

function getHealthBarColor(currentHp, maxHp) {
    const percentage = (currentHp / maxHp) * 100;
    if (percentage > 75) return 'var(--forest-green)';
    if (percentage > 50) return 'var(--gold)';
    if (percentage > 25) return '#ff9800'; // Orange
    return 'var(--crimson)';
}

function createHealthBar(currentHp, maxHp) {
    const percentage = Math.max(0, Math.min(100, (currentHp / maxHp) * 100));
    
    const healthBarContainer = document.createElement('div');
    healthBarContainer.style.cssText = `
        width: 100%;
        height: 4px;
        background-color: #e0e0e0;
        border-radius: 2px;
        margin-top: 4px;
        overflow: hidden;
    `;
    
    const healthBarFill = document.createElement('div');
    healthBarFill.style.cssText = `
        width: ${percentage}%;
        height: 100%;
        background-color: ${getHealthBarColor(currentHp, maxHp)};
        transition: width 0.3s ease;
        border-radius: 2px;
    `;
    
    healthBarContainer.appendChild(healthBarFill);
    return healthBarContainer;
}

export function updatePartyList(party) {
    if (!partyListEl) return;
    partyListEl.innerHTML = ''; 
    
    if (!party || party.length === 0) {
        const li = document.createElement('li');
        li.innerHTML = `
            <div class="character-portrait">?</div>
            <div class="character-info">
                <div class="character-name">No party data</div>
            </div>
        `;
        partyListEl.appendChild(li);
        return;
    }
    
    party.forEach(char => {
        const li = document.createElement('li');
        li.dataset.charId = char.id;
        
        // Create portrait
        const portrait = getPortraitImage(char.id, char.name);
        
        // Create character info container
        const infoDiv = document.createElement('div');
        infoDiv.className = 'character-info';
        
        // Character name
        const nameDiv = document.createElement('div');
        nameDiv.className = 'character-name';
        nameDiv.textContent = char.name;
        
        // Character details
        const detailsDiv = document.createElement('div');
        detailsDiv.className = 'character-details';
        
        // Basic character info
        const basicInfo = `${char.race} ${char.char_class} ${char.level}`;
        const hpInfo = `${char.hp}/${char.max_hp} HP`;
        
        // Conditions
        let conditionInfo = '';
        if (char.conditions && char.conditions.length > 0) {
            conditionInfo = ` • ${char.conditions.join(', ')}`;
        }
        
        detailsDiv.innerHTML = `
            ${basicInfo}<br>
            ${hpInfo}${conditionInfo}
        `;
        
        // Add health bar
        const healthBar = createHealthBar(char.hp, char.max_hp);
        
        // Assemble the structure
        infoDiv.appendChild(nameDiv);
        infoDiv.appendChild(detailsDiv);
        infoDiv.appendChild(healthBar);
        
        li.appendChild(portrait);
        li.appendChild(infoDiv);
        
        // Tooltip with detailed stats
        const stats = char.stats || {};
        li.title = `${char.name}\nAC: ${char.ac || '?'}\nSTR: ${stats.STR || '?'} DEX: ${stats.DEX || '?'} CON: ${stats.CON || '?'}\nINT: ${stats.INT || '?'} WIS: ${stats.WIS || '?'} CHA: ${stats.CHA || '?'}`;
        
        partyListEl.appendChild(li);
    });
}

// Function to update portrait if a real image becomes available
export function updateCharacterPortrait(characterId, imageUrl) {
    const characterElement = document.querySelector(`[data-char-id="${characterId}"] .character-portrait`);
    if (characterElement && imageUrl) {
        // Replace the initials with an actual image
        characterElement.innerHTML = '';
        characterElement.style.backgroundImage = `url(${imageUrl})`;
        characterElement.style.backgroundSize = 'cover';
        characterElement.style.backgroundPosition = 'center';
        characterElement.style.color = 'transparent'; // Hide any text
    }
}
