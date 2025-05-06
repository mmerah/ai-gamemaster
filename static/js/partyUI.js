const partyListEl = document.getElementById('party-list');

export function updatePartyList(party) {
    if (!partyListEl) return;
    partyListEl.innerHTML = ''; 
    if (!party || party.length === 0) {
        partyListEl.innerHTML = '<li>No party data</li>';
        return;
    }
    party.forEach(char => {
        const li = document.createElement('li');
        let status = `HP: ${char.hp}/${char.max_hp}`;
        if (char.conditions && char.conditions.length > 0) {
            status += ` | Cond: ${char.conditions.join(', ')}`;
        }
        li.textContent = `${char.name} (${char.race} ${char.char_class} ${char.level}) | ${status}`;
        li.dataset.charId = char.id;

        const stats = char.stats || {};
        li.title = `AC:${char.ac||'?'} | STR:${stats.STR||'?'} DEX:${stats.DEX||'?'} CON:${stats.CON||'?'} INT:${stats.INT||'?'} WIS:${stats.WIS||'?'} CHA:${stats.CHA||'?'}`;
        partyListEl.appendChild(li);
    });
}