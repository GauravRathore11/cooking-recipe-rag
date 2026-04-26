

let isStreaming = false;



function switchTab(tab) {
    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`nav-${tab}`).classList.add('active');

    // Update views
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(`view-${tab}`).classList.add('active');
}



function sendMessage() {
    const input = document.getElementById('chat-input');
    const query = input.value.trim();

    if (!query || isStreaming) return;

    // Add user message
    appendMessage('user', query);
    input.value = '';

    // Show typing indicator
    const typingEl = showTypingIndicator();

    // Stream response from backend
    isStreaming = true;
    toggleInput(false);

    fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query }),
    })
    .then(response => {
        // Remove typing indicator
        typingEl.remove();

        if (!response.ok) {
            return response.json().then(data => {
                appendMessage('bot', data.error || 'Something went wrong.', true);
                throw new Error('handled');
            });
        }

        // Create bot message bubble for streaming tokens into
        const { bubbleContent } = appendMessage('bot', '');

        // Read the SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        function readStream() {
            reader.read().then(({ done, value }) => {
                if (done) {
                    isStreaming = false;
                    toggleInput(true);
                    return;
                }

                const text = decoder.decode(value, { stream: true });
                // Parse SSE format: "data: {...}\n\n"
                const lines = text.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.substring(6));

                            if (data.done) {
                                isStreaming = false;
                                toggleInput(true);
                                return;
                            }

                            if (data.token) {
                                bubbleContent.textContent += data.token;
                                scrollToBottom();
                            }
                        } catch (e) {
                            // Skip malformed lines
                        }
                    }
                }

                readStream();
            });
        }

        readStream();
    })
    .catch(err => {
        if (err.message !== 'handled') {
            typingEl.remove();
            appendMessage('bot', 'Could not connect to the server. Make sure the backend is running.', true);
        }
        isStreaming = false;
        toggleInput(true);
    });
}



function appendMessage(role, text, isError = false) {
    const container = document.getElementById('chat-container');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message fade-in`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? 'U' : 'AI';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    const bubbleContent = document.createElement('span');
    if (isError) {
        bubbleContent.className = 'error-text';
    }
    bubbleContent.textContent = text;
    bubble.appendChild(bubbleContent);

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    container.appendChild(messageDiv);

    scrollToBottom();

    return { bubbleContent };
}



function showTypingIndicator() {
    const container = document.getElementById('chat-container');

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message fade-in';
    messageDiv.id = 'typing-indicator';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = 'AI';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble typing-indicator';
    bubble.innerHTML = '<span></span><span></span><span></span>';

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    container.appendChild(messageDiv);

    scrollToBottom();

    return messageDiv;
}



function scrollToBottom() {
    const container = document.getElementById('chat-container');
    container.scrollTop = container.scrollHeight;
}

function toggleInput(enabled) {
    document.getElementById('chat-input').disabled = !enabled;
    document.getElementById('send-btn').disabled = !enabled;

    if (enabled) {
        document.getElementById('chat-input').focus();
    }
}



function addRecipe(event) {
    event.preventDefault();

    const title = document.getElementById('recipe-title').value.trim();
    const ingredients = document.getElementById('recipe-ingredients').value.trim();
    const instructions = document.getElementById('recipe-instructions').value.trim();

    const submitBtn = document.getElementById('submit-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Adding...';

    fetch('/api/recipe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, ingredients, instructions }),
    })
    .then(response => response.json().then(data => ({ ok: response.ok, data })))
    .then(({ ok, data }) => {
        if (ok) {
            showToast(data.message, 'success');
            document.getElementById('recipe-form').reset();
        } else {
            showToast(data.error || 'Failed to add recipe.', 'error');
        }
    })
    .catch(() => {
        showToast('Could not connect to server.', 'error');
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Add Recipe';
    });
}

function showToast(message, type) {
    const toast = document.getElementById('form-toast');
    toast.textContent = message;
    toast.className = `form-toast show ${type}`;

    setTimeout(() => {
        toast.className = 'form-toast';
    }, 4000);
}



document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('chat-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});
