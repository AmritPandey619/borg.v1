class UIHandler {
    constructor() {
        this.userInput = document.getElementById('user-input');
        this.sendButton = document.getElementById('send-button');
        this.toggleSidebarBtn = document.getElementById('toggle-sidebar-btn');
        this.themeToggle = document.getElementById('theme-toggle');
        this.newChatBtn = document.querySelector('#new-chat-btn');
        this.newChat = document.querySelector('#new-chat');
        this.root = document.documentElement;
        
        this.initializeEventListeners();
        this.initializeTheme();
    }

    initializeEventListeners() {
        // Auto-resize textarea
        this.userInput.addEventListener('input', () => {
            this.userInput.style.height = 'auto';
            this.userInput.style.height = Math.min(this.userInput.scrollHeight, 200) + 'px';
        });

        // Toggle sidebar
        this.toggleSidebarBtn.addEventListener('click', () => {
            const sidebar = document.getElementById('sidebar');
            const toggleButtonContainer = document.querySelector('.toggle-button-container');
            sidebar.classList.toggle('collapsed');
            this.newChat.classList.toggle('show');
            toggleButtonContainer.classList.toggle('show');
            
            // Update chat container margin
            const chatContainer = document.querySelector('.chat-container');
            if (sidebar.classList.contains('collapsed')) {
                chatContainer.style.marginLeft = '0';
                chatContainer.style.maxWidth = '100%';
            } else {
                chatContainer.style.marginLeft = '260px';
                chatContainer.style.maxWidth = 'calc(100% - 260px)';
            }
        });

        // Theme toggle
        this.themeToggle.addEventListener('click', () => {
            this.root.classList.toggle('dark-mode');
            const isDark = this.root.classList.contains('dark-mode');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
        });

        // New chat buttons
        [this.newChatBtn, this.newChat].forEach(btn => {
            if (btn) {
                btn.addEventListener('click', () => sessionManager.createNewChat());
            }
        });

        // Send message handlers
        this.sendButton.addEventListener('click', () => chatHandler.sendMessage());
        this.userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatHandler.sendMessage();
            }
        });
    }

    initializeTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        if (savedTheme === 'dark') {
            this.root.classList.add('dark-mode');
        }
    }
}

class TooltipHandler {
    show(event, text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = text;
        document.body.appendChild(tooltip);

        const rect = event.target.getBoundingClientRect();
        tooltip.style.top = rect.bottom + 5 + 'px';
        tooltip.style.left = rect.left + (rect.width - tooltip.offsetWidth) / 2 + 'px';
        
        setTimeout(() => tooltip.style.opacity = '1', 0);
    }

    hide() {
        const tooltips = document.querySelectorAll('.tooltip');
        tooltips.forEach(tooltip => {
            tooltip.style.opacity = '0';
            setTimeout(() => tooltip.remove(), 200);
        });
    }
}

const uiHandler = new UIHandler();
const tooltipHandler = new TooltipHandler();

// Add tooltip listeners to buttons
document.querySelectorAll('[data-tooltip]').forEach(element => {
    element.addEventListener('mouseenter', (e) => tooltipHandler.show(e, e.target.dataset.tooltip));
    element.addEventListener('mouseleave', () => tooltipHandler.hide());
}); 