document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const tabChat = document.getElementById('tab-chat');
    const tabDashboard = document.getElementById('tab-dashboard');
    const viewChat = document.getElementById('view-chat');
    const viewDashboard = document.getElementById('view-dashboard');
    const promptInput = document.getElementById('prompt-input');
    const sendBtn = document.getElementById('send-btn');
    const historyDeepseek = document.getElementById('history-deepseek');
    const historyOss = document.getElementById('history-oss');
    const historyOssSecure = document.getElementById('history-oss-secure');
    const refreshLogsBtn = document.getElementById('refresh-logs-btn');
    const logsBody = document.getElementById('logs-body');

    // Tab Switching
    tabChat.addEventListener('click', () => switchTab(tabChat, viewChat));
    tabDashboard.addEventListener('click', () => {
        switchTab(tabDashboard, viewDashboard);
        fetchLogs();
    });

    function switchTab(activeTab, activeView) {
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.view').forEach(view => view.classList.remove('active'));
        activeTab.classList.add('active');
        activeView.classList.add('active');
    }

    // Auto-resize textarea
    promptInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Send Message Handlers
    promptInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);

    async function sendMessage() {
        const text = promptInput.value.trim();
        if (!text) return;

        // Reset input
        promptInput.value = '';
        promptInput.style.height = 'auto';

        // Add user messages
        appendMessage(historyDeepseek, text, 'user');
        appendMessage(historyOss, text, 'user');
        appendMessage(historyOssSecure, text, 'user');

        // Add loading placeholders
        const loadingDs = appendMessage(historyDeepseek, '...', 'ai', true);
        const loadingOss = appendMessage(historyOss, '...', 'ai', true);
        const loadingOssSecure = appendMessage(historyOssSecure, '...', 'ai', true);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            
            const data = await response.json();

            // Populate with real data using marked.js to render Markdown
            loadingDs.innerHTML = marked.parse(data.deepseek);
            loadingDs.style.opacity = '1';
            
            loadingOss.innerHTML = marked.parse(data.oss);
            loadingOss.style.opacity = '1';
            
            loadingOssSecure.innerHTML = marked.parse(data.oss_secure);
            loadingOssSecure.style.opacity = '1';
            
        } catch (err) {
            loadingDs.textContent = 'Network Error.';
            loadingOss.textContent = 'Network Error.';
            loadingOssSecure.textContent = 'Network Error.';
        }
        
        historyDeepseek.scrollTop = historyDeepseek.scrollHeight;
        historyOss.scrollTop = historyOss.scrollHeight;
        historyOssSecure.scrollTop = historyOssSecure.scrollHeight;
    }

    function appendMessage(container, text, sender, isLoading = false) {
        const div = document.createElement('div');
        div.className = `message msg-${sender}`;
        if (isLoading) div.style.opacity = '0.5';
        
        if (sender === 'user') {
            div.textContent = text;
        } else {
            div.innerHTML = marked.parse(text);
        }
        
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
        return div;
    }

    // Dashboard Data Fetching
    refreshLogsBtn.addEventListener('click', fetchLogs);

    async function fetchLogs() {
        try {
            const response = await fetch('/api/logs');
            const data = await response.json();
            
            logsBody.innerHTML = '';
            data.logs.forEach(log => {
                const tr = document.createElement('tr');
                const date = new Date(log[0]).toLocaleString();
                
                tr.innerHTML = `
                    <td>${date}</td>
                    <td><span class="badge">${log[1]}</span></td>
                    <td>${Math.round(log[2])} ms</td>
                    <td>${log[3]}</td>
                    <td>$${log[4].toFixed(6)}</td>
                    <td style="max-width:300px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${log[5]}">${log[5]}</td>
                `;
                logsBody.appendChild(tr);
            });
        } catch (err) {
            console.error('Failed to load logs', err);
        }
    }
});
