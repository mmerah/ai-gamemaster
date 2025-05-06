const chatHistoryEl = document.getElementById('chat-history');

export function addMessageToHistory(sender, message, thought = null) {
    if (message === null || typeof message === 'undefined') {
        console.warn(`addMessageToHistory called with null/undefined message for sender ${sender}. Displaying placeholder.`);
        message = `(${sender} message content missing)`;
    }

    const messageContainer = document.createElement('div');
    messageContainer.classList.add('message-container', sender.toLowerCase() + '-container');

    const messageEl = document.createElement('p');
    messageEl.innerHTML = message.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>').replace(/\*(.*?)\*/g, '<i>$1</i>');
    messageEl.classList.add(sender.toLowerCase() + '-message');

    if (sender === 'System') {
        messageEl.classList.add('system-message');
    }

    if (sender === 'GM' && thought) {
        const thoughtToggle = document.createElement('button');
        thoughtToggle.textContent = '🤔';
        thoughtToggle.classList.add('thought-toggle');
        thoughtToggle.title = 'Show/Hide GM Thought Process';

        const thoughtContent = document.createElement('div');
        thoughtContent.classList.add('thought-content');
        thoughtContent.textContent = thought;
        thoughtContent.style.display = 'none';

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
    chatHistoryEl.scrollTop = chatHistoryEl.scrollHeight;
}

export function clearChatHistory() {
    if (chatHistoryEl) {
        chatHistoryEl.innerHTML = '';
    }
}