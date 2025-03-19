class MessageHandler {
    constructor() {
        this.chatMessages = document.getElementById('chat-messages');
        this.isBotResponding = false;
    }

    addMessage(message, isUser) {
        const container = document.createElement('div');
        container.className = `message-container ${isUser ? 'user-container' : 'bot-container'}`;

        const avatar = document.createElement('div');
        avatar.className = `message-avatar ${isUser ? 'user-avatar' : 'bot-avatar'}`;
        if (isUser) {
            avatar.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
            </svg>`;
        } else {
            avatar.innerHTML = `<img src="static/images/nokia-logo.svg" alt="Nokia" width="20" height="20">`;
        }
        container.appendChild(avatar);

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.innerHTML = isUser ? message : marked.parse(message);
        messageDiv.appendChild(textDiv);

        if (!isUser) {
            const footer = document.createElement('div');
            footer.className = 'message-footer';
            
            const timestamp = document.createElement('div');
            timestamp.className = 'message-timestamp';
            const now = new Date();
            timestamp.textContent = now.toLocaleString();
            
            const buttonContainer = document.createElement('div');
            buttonContainer.className = 'message-actions';
            buttonContainer.innerHTML = this.getActionButtons();
            
            footer.appendChild(timestamp);
            footer.appendChild(buttonContainer);
            messageDiv.appendChild(footer);
        }

        container.appendChild(messageDiv);
        this.chatMessages.appendChild(container);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    getActionButtons() {
        return `
            <button class="action-btn" data-tooltip="Copy message" onclick="messageHandler.copyMessage(this)" onmouseenter="tooltipHandler.show(event, 'Copy message')" onmouseleave="tooltipHandler.hide()">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M8 4v12h12V4H8zM6 2h16v16H6V2zM4 6H2v18h18v-2"/>
                </svg>
            </button>
            <button class="action-btn" data-tooltip="Execute code" onclick="messageHandler.handleExecute(this)" onmouseenter="tooltipHandler.show(event, 'Execute code')" onmouseleave="tooltipHandler.hide()">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M5 12l5 5 10-10M5 12l5-5 10 10"/>
                </svg>
            </button>
        `;
    }

    copyMessage(button) {
        const messageContainer = button.closest('.message');
        const textElement = messageContainer.querySelector('.message-text');
        navigator.clipboard.writeText(textElement.textContent.trim());
        
        const originalTitle = button.title;
        button.title = 'Copied!';
        setTimeout(() => {
            button.title = originalTitle;
        }, 2000);
    }

    handleExecute(button) {
        //TODO: Implement logic here
        console.log('Execute button clicked - implement logic here');
        const message = button.closest('.message').textContent;
    }

    addLoadingMessage() {
        const container = document.createElement('div');
        container.className = 'message-container bot-container';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar bot-avatar';
        avatar.innerHTML = `<img src="static/images/nokia-logo.svg" alt="Nokia" width="20" height="20">`;
        container.appendChild(avatar);
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'loading-message';
        
        const dotsContainer = document.createElement('div');
        dotsContainer.className = 'loading-dots';
        dotsContainer.innerHTML = '<div></div><div></div><div></div>';
        
        messageDiv.appendChild(dotsContainer);
        container.appendChild(messageDiv);
        this.chatMessages.appendChild(container);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        
        return container;
    }
}

const messageHandler = new MessageHandler(); 