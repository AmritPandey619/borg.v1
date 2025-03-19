class SessionManager {
    constructor() {
        this.sessionsList = document.getElementById('sessions-list');
        this.sessionId = sessionStorage.getItem('session_id') || null;
        this.chatMessages = document.getElementById('chat-messages');
    }

    async loadSessions() {
        try {
            const response = await fetch('/sessions');
            if (!response.ok) throw new Error('Failed to load sessions');

            const sessions = await response.json();
            this.sessionsList.innerHTML = '';
            sessions.forEach(session => {
                const sessionItem = document.createElement('div');
                sessionItem.className = 'session-item';
                if (session.session_id === this.sessionId) {
                    sessionItem.classList.add('active');
                }
                sessionItem.textContent = session.title || 'New Chat';
                sessionItem.addEventListener('click', () => {
                    document.querySelectorAll('.session-item').forEach(item => {
                        item.classList.remove('active');
                    });
                    sessionItem.classList.add('active');
                    this.sessionId = session.session_id;
                    sessionStorage.setItem('session_id', this.sessionId);
                    this.loadChatHistory(this.sessionId);
                });
                this.sessionsList.appendChild(sessionItem);
            });
        } catch (error) {
            console.error('Error loading sessions:', error);
        }
    }

    async loadChatHistory(sessionid) {
        this.sessionId = sessionid || sessionStorage.getItem('session_id') || null;
        try {
            const response = await fetch('/history', {
                headers: {
                    'Session-ID': this.sessionId
                }
            });
            if (!response.ok) throw new Error('Failed to load chat history');

            const history = await response.json();
            this.chatMessages.innerHTML = '';
            history.forEach(message => {
                messageHandler.addMessage(message.content, message.role === 'user');
            });
        } catch (error) {
            console.error("Error loading chat history:", error);
        }
    }

    async createNewChat() {
        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Session-ID': 'null',
                },
                body: JSON.stringify({ message: '', model: 'gemini-pro' }),
            });

            if (!response.ok) throw new Error('Failed to start new chat');
            const data = await response.json();

            if (data.session_id) {
                this.sessionId = data.session_id;
                sessionStorage.setItem('session_id', this.sessionId);
                this.chatMessages.innerHTML = '';
                this.loadSessions();
            }
        } catch (error) {
            console.error('Error starting new chat:', error);
        }
    }
}

const sessionManager = new SessionManager(); 