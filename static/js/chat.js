class ChatHandler {
    constructor() {
        this.userInput = document.getElementById('user-input');
        this.sendButton = document.getElementById('send-button');
        this.isBotResponding = false;
    }

    async sendMessage() {
        if (this.isBotResponding) return;
        
        const message = this.userInput.value.trim();
        const model = document.getElementById("model-selector").value;
        if (!message) return;

        this.isBotResponding = true;
        this.sendButton.disabled = true;
        messageHandler.addMessage(message, true);
        this.userInput.value = '';
        this.userInput.style.height = 'auto';
        
        const loadingMessage = messageHandler.addLoadingMessage();

        try {
            console.log('Sending message to server:', { message, model, sessionId: sessionManager.sessionId });
            
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Session-ID': sessionManager.sessionId,
                },
                body: JSON.stringify({ message, model }),
            });

            // First check if the response is ok
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Server error (${response.status})`);
            }

            // Then try to parse the response
            let responseData;
            try {
                responseData = await response.json();
                console.log('Server response:', responseData);
            } catch (parseError) {
                console.error('Error parsing response:', parseError);
                throw new Error('Invalid response from server');
            }
            
            // Validate the response data
            if (!responseData) {
                throw new Error('Empty response from server');
            }

            if (responseData.error) {
                throw new Error(responseData.error);
            }

            if (!responseData.content) {
                throw new Error('No response content received from server');
            }

            // Remove loading message and show the response
            loadingMessage.remove();
            messageHandler.addMessage(responseData.content, false);

            // Update session if needed
            if(responseData.session_id && !sessionManager.sessionId) {
                sessionManager.sessionId = responseData.session_id;
                sessionStorage.setItem('session_id', sessionManager.sessionId);
                await sessionManager.loadSessions();
            }
        } catch (error) {
            console.error('Error details:', error);
            loadingMessage.remove();
            messageHandler.addMessage(`Error: ${error.message || 'Could not generate response'}`, false);
        } finally {
            this.isBotResponding = false;
            this.sendButton.disabled = false;
        }
    }
}

const chatHandler = new ChatHandler(); 