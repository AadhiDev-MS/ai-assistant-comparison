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

    // Generate a unique session ID for this browser tab
    const sessionId = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);

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
            const reqDs = fetch('/api/chat/deepseek', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: text, session_id: sessionId }) });
            const reqOss = fetch('/api/chat/oss', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: text, session_id: sessionId }) });
            const reqOssSecure = fetch('/api/chat/oss_secure', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: text, session_id: sessionId }) });
            
            // Process the streams in parallel
            readStream(reqDs, loadingDs, historyDeepseek);
            readStream(reqOss, loadingOss, historyOss);
            readStream(reqOssSecure, loadingOssSecure, historyOssSecure);
            
        } catch (err) {
            loadingDs.textContent = 'Network Error.';
            loadingOss.textContent = 'Network Error.';
            loadingOssSecure.textContent = 'Network Error.';
        }
    }

    async function readStream(fetchPromise, uiElement, container) {
        try {
            const response = await fetchPromise;
            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let fullText = "";
            uiElement.style.opacity = '1';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                const chunkStr = decoder.decode(value, { stream: true });
                const lines = chunkStr.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.substring(6));
                            fullText += data.chunk;
                            // Re-render markdown on every chunk
                            uiElement.innerHTML = marked.parse(fullText);
                            container.scrollTop = container.scrollHeight;
                        } catch(e) {
                            // ignore partial json parsing errors during stream splits
                        }
                    }
                }
            }
        } catch (err) {
            uiElement.textContent = 'Stream Error';
        }
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
                    <td>${log[3].toFixed(1)}</td>
                    <td>${log[4]}</td>
                    <td>$${log[5].toFixed(6)}</td>
                    <td style="max-width:300px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${log[6]}">${log[6]}</td>
                `;
                logsBody.appendChild(tr);
            });
        } catch (err) {
            console.error('Failed to load logs', err);
        }
    }
});
