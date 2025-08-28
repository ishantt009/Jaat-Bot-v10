class DiscordBotDevEnvironment {
    constructor() {
        this.socket = null;
        this.editor = null;
        this.currentFile = null;
        this.files = [];
        this.envVars = {};
        this.isConnected = false;
        
        this.init();
    }
    
    async init() {
        this.initSocketConnection();
        this.initMonacoEditor();
        this.initEventListeners();
        this.loadFiles();
        
        // Initialize tabs
        this.initTabs();
    }
    
    initSocketConnection() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            this.isConnected = true;
            this.updateConnectionStatus('Connected');
            console.log('Connected to server');
        });
        
        this.socket.on('disconnect', () => {
            this.isConnected = false;
            this.updateConnectionStatus('Disconnected');
            console.log('Disconnected from server');
        });
        
        this.socket.on('bot_status', (status) => {
            this.updateBotStatus(status);
        });
        
        this.socket.on('bot_log', (logEntry) => {
            this.addLogEntry(logEntry);
        });
    }
    
    async initMonacoEditor() {
        require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.30.1/min/vs' }});
        
        require(['vs/editor/editor.main'], () => {
            this.editor = monaco.editor.create(document.getElementById('editor'), {
                value: '# Welcome to Discord Bot Development Environment\n# Upload or create a Python file to get started\n\nimport discord\nfrom discord.ext import commands\n\n# Example bot setup\nbot = commands.Bot(command_prefix=\'!\')\n\n@bot.event\nasync def on_ready():\n    print(f\'{bot.user} has connected to Discord!\')\n\n@bot.command(name=\'hello\')\nasync def hello(ctx):\n    await ctx.send(\'Hello! I am your Discord bot.\')\n\n# Run the bot\n# bot.run(\'YOUR_BOT_TOKEN\')',
                language: 'python',
                theme: 'vs-dark',
                automaticLayout: true,
                fontSize: 14,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                wordWrap: 'on'
            });
            
            // Add save shortcut
            this.editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
                this.saveCurrentFile();
            });
            
            // Add change listener
            this.editor.onDidChangeModelContent(() => {
                this.markFileAsModified();
            });
        });
    }
    
    initEventListeners() {
        // File upload
        const fileInput = document.getElementById('fileInput');
        const uploadArea = document.querySelector('.upload-area');
        
        fileInput.addEventListener('change', (e) => {
            this.uploadFiles(e.target.files);
        });
        
        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            this.uploadFiles(e.dataTransfer.files);
        });
        
        // Bot controls
        document.getElementById('startBot').addEventListener('click', () => {
            this.showConfigModal();
        });
        
        document.getElementById('stopBot').addEventListener('click', () => {
            this.stopBot();
        });
        
        document.getElementById('configBot').addEventListener('click', () => {
            this.showConfigModal();
        });
        
        // File operations
        document.getElementById('saveFile').addEventListener('click', () => {
            this.saveCurrentFile();
        });
        
        document.getElementById('newFileBtn').addEventListener('click', () => {
            this.showNewFileModal();
        });
        
        // Console controls
        document.getElementById('clearConsole').addEventListener('click', () => {
            this.clearConsole();
        });
        
        // Environment variables
        document.getElementById('addEnvVar').addEventListener('click', () => {
            this.addEnvironmentVariable();
        });
        
        document.getElementById('saveEnvVars').addEventListener('click', () => {
            this.saveEnvironmentVariables();
        });
        
        // Modal controls
        document.querySelectorAll('.close').forEach(closeBtn => {
            closeBtn.addEventListener('click', () => {
                this.closeModal();
            });
        });
        
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal();
            }
        });
        
        // Forms
        document.getElementById('configForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.startBot();
        });
        
        document.getElementById('newFileForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createNewFile();
        });
    }
    
    initTabs() {
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const tabName = tab.dataset.tab;
                this.switchTab(tabName);
            });
        });
    }
    
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Update tab content
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.style.display = 'none';
        });
        document.getElementById(tabName).style.display = 'block';
    }
    
    async uploadFiles(files) {
        const formData = new FormData();
        
        for (let file of files) {
            formData.append('files', file);
        }
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification(result.message, 'success');
                this.loadFiles();
            } else {
                this.showNotification(result.error, 'error');
            }
        } catch (error) {
            this.showNotification('Failed to upload files: ' + error.message, 'error');
        }
    }
    
    async loadFiles() {
        try {
            const response = await fetch('/api/files');
            const result = await response.json();
            
            if (response.ok) {
                this.files = result.files;
                this.renderFileList();
                this.updateMainFileOptions();
            } else {
                this.showNotification(result.error, 'error');
            }
        } catch (error) {
            this.showNotification('Failed to load files: ' + error.message, 'error');
        }
    }
    
    renderFileList() {
        const fileList = document.getElementById('fileList');
        
        if (this.files.length === 0) {
            fileList.innerHTML = '<div style="text-align: center; color: #888; padding: 20px;">No files uploaded yet</div>';
            return;
        }
        
        fileList.innerHTML = this.files.map(file => `
            <div class="file-item" data-filename="${file.name}">
                <i class="file-icon ${this.getFileIcon(file.type)}"></i>
                <span class="file-name">${file.name}</span>
                <div class="file-actions">
                    <button class="file-action" onclick="app.openFile('${file.name}')" title="Open">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="file-action" onclick="app.deleteFile('${file.name}')" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    getFileIcon(type) {
        const icons = {
            'python': 'fab fa-python',
            'json': 'fas fa-code',
            'yaml': 'fas fa-file-code',
            'text': 'fas fa-file-alt',
            'markdown': 'fab fa-markdown'
        };
        return icons[type] || 'fas fa-file';
    }
    
    async openFile(filename) {
        try {
            const response = await fetch(`/api/files/${filename}`);
            const result = await response.json();
            
            if (response.ok) {
                this.currentFile = filename;
                this.editor.setValue(result.content);
                
                // Update language based on file extension
                const extension = filename.split('.').pop().toLowerCase();
                const language = this.getLanguageFromExtension(extension);
                monaco.editor.setModelLanguage(this.editor.getModel(), language);
                
                // Update UI
                document.getElementById('currentFileName').innerHTML = 
                    `<i class="fas fa-code"></i> ${filename}`;
                document.getElementById('saveFile').disabled = false;
                
                // Update active file in list
                document.querySelectorAll('.file-item').forEach(item => {
                    item.classList.remove('active');
                });
                document.querySelector(`[data-filename="${filename}"]`).classList.add('active');
                
            } else {
                this.showNotification(result.error, 'error');
            }
        } catch (error) {
            this.showNotification('Failed to open file: ' + error.message, 'error');
        }
    }
    
    getLanguageFromExtension(extension) {
        const languages = {
            'py': 'python',
            'json': 'json',
            'yaml': 'yaml',
            'yml': 'yaml',
            'md': 'markdown',
            'txt': 'plaintext'
        };
        return languages[extension] || 'plaintext';
    }
    
    async saveCurrentFile() {
        if (!this.currentFile) {
            this.showNotification('No file is currently open', 'warning');
            return;
        }
        
        try {
            const content = this.editor.getValue();
            const response = await fetch(`/api/files/${this.currentFile}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification(result.message, 'success');
                this.unmarkFileAsModified();
            } else {
                this.showNotification(result.error, 'error');
            }
        } catch (error) {
            this.showNotification('Failed to save file: ' + error.message, 'error');
        }
    }
    
    async deleteFile(filename) {
        if (!confirm(`Are you sure you want to delete ${filename}?`)) {
            return;
        }
        
        try {
            const response = await fetch(`/api/files/${filename}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification(result.message, 'success');
                this.loadFiles();
                
                // Close file if it's currently open
                if (this.currentFile === filename) {
                    this.currentFile = null;
                    this.editor.setValue('');
                    document.getElementById('currentFileName').innerHTML = 
                        '<i class="fas fa-code"></i> No file selected';
                    document.getElementById('saveFile').disabled = true;
                }
            } else {
                this.showNotification(result.error, 'error');
            }
        } catch (error) {
            this.showNotification('Failed to delete file: ' + error.message, 'error');
        }
    }
    
    showNewFileModal() {
        document.getElementById('newFileModal').style.display = 'block';
        document.getElementById('newFileName').focus();
    }
    
    async createNewFile() {
        const filename = document.getElementById('newFileName').value.trim();
        
        if (!filename) {
            this.showNotification('Please enter a filename', 'warning');
            return;
        }
        
        try {
            const response = await fetch(`/api/files/${filename}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content: '' })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification(`File ${filename} created successfully`, 'success');
                this.closeModal();
                this.loadFiles();
                
                // Open the new file
                setTimeout(() => {
                    this.openFile(filename);
                }, 500);
            } else {
                this.showNotification(result.error, 'error');
            }
        } catch (error) {
            this.showNotification('Failed to create file: ' + error.message, 'error');
        }
    }
    
    showConfigModal() {
        this.updateMainFileOptions();
        document.getElementById('configModal').style.display = 'block';
    }
    
    updateMainFileOptions() {
        const select = document.getElementById('mainFile');
        const pythonFiles = this.files.filter(file => file.name.endsWith('.py'));
        
        select.innerHTML = '<option value="">Select main file...</option>' +
            pythonFiles.map(file => 
                `<option value="${file.name}">${file.name}</option>`
            ).join('');
    }
    
    async startBot() {
        const token = document.getElementById('botToken').value.trim();
        const mainFile = document.getElementById('mainFile').value;
        
        if (!mainFile) {
            this.showNotification('Please select a main bot file', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/bot/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    main_file: mainFile,
                    token: token 
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification(result.message, 'success');
                this.closeModal();
                this.clearForm('configForm');
            } else {
                this.showNotification(result.error, 'error');
            }
        } catch (error) {
            this.showNotification('Failed to start bot: ' + error.message, 'error');
        }
    }
    
    async stopBot() {
        try {
            const response = await fetch('/api/bot/stop', {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification(result.message, 'success');
            } else {
                this.showNotification(result.error, 'error');
            }
        } catch (error) {
            this.showNotification('Failed to stop bot: ' + error.message, 'error');
        }
    }
    
    updateBotStatus(status) {
        const statusElement = document.getElementById('botStatus');
        const startBtn = document.getElementById('startBot');
        const stopBtn = document.getElementById('stopBot');
        
        if (status.running) {
            statusElement.className = 'bot-status running';
            statusElement.innerHTML = '<i class="fas fa-circle"></i> Bot Running';
            startBtn.disabled = true;
            stopBtn.disabled = false;
        } else {
            statusElement.className = 'bot-status stopped';
            statusElement.innerHTML = '<i class="fas fa-circle"></i> Bot Stopped';
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
        
        // Update bot info
        document.getElementById('uptime').textContent = 
            status.uptime ? this.formatUptime(status.uptime) : '--';
        document.getElementById('memory').textContent = 
            status.memory_usage ? `${Math.round(status.memory_usage)}MB` : '--';
        document.getElementById('pid').textContent = 
            status.pid || '--';
    }
    
    formatUptime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }
    
    addLogEntry(logEntry) {
        const consoleOutput = document.getElementById('consoleOutput');
        const timestamp = new Date(logEntry.timestamp).toLocaleTimeString();
        
        const logElement = document.createElement('div');
        logElement.className = 'log-entry';
        logElement.innerHTML = `
            <span class="log-timestamp">${timestamp}</span>
            <span class="log-level ${logEntry.level}">${logEntry.level}</span>
            <span class="log-message">${this.escapeHtml(logEntry.message)}</span>
        `;
        
        consoleOutput.appendChild(logElement);
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
        
        // Limit console history
        const maxEntries = 1000;
        while (consoleOutput.children.length > maxEntries) {
            consoleOutput.removeChild(consoleOutput.firstChild);
        }
    }
    
    clearConsole() {
        document.getElementById('consoleOutput').innerHTML = '';
    }
    
    addEnvironmentVariable() {
        const nameInput = document.getElementById('envName');
        const valueInput = document.getElementById('envValue');
        
        const name = nameInput.value.trim();
        const value = valueInput.value.trim();
        
        if (!name) {
            this.showNotification('Please enter a variable name', 'warning');
            return;
        }
        
        this.envVars[name] = value;
        
        // Clear inputs
        nameInput.value = '';
        valueInput.value = '';
        
        this.renderEnvironmentVariables();
    }
    
    renderEnvironmentVariables() {
        const list = document.getElementById('envVarsList');
        
        list.innerHTML = Object.entries(this.envVars).map(([name, value]) => `
            <div class="env-var">
                <input type="text" class="env-input" value="${name}" readonly>
                <input type="text" class="env-input" value="${value}" 
                       onchange="app.updateEnvVar('${name}', this.value)">
                <button class="btn btn-danger" onclick="app.removeEnvVar('${name}')">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `).join('');
    }
    
    updateEnvVar(name, value) {
        this.envVars[name] = value;
    }
    
    removeEnvVar(name) {
        delete this.envVars[name];
        this.renderEnvironmentVariables();
    }
    
    async saveEnvironmentVariables() {
        try {
            const response = await fetch('/api/environment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ variables: this.envVars })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification(result.message, 'success');
            } else {
                this.showNotification(result.error, 'error');
            }
        } catch (error) {
            this.showNotification('Failed to save environment variables: ' + error.message, 'error');
        }
    }
    
    closeModal() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });
    }
    
    clearForm(formId) {
        const form = document.getElementById(formId);
        form.reset();
    }
    
    markFileAsModified() {
        const filename = document.getElementById('currentFileName');
        if (filename && !filename.textContent.includes('●')) {
            filename.innerHTML = filename.innerHTML.replace('</i>', '</i> ●');
        }
    }
    
    unmarkFileAsModified() {
        const filename = document.getElementById('currentFileName');
        if (filename) {
            filename.innerHTML = filename.innerHTML.replace(' ●', '');
        }
    }
    
    updateConnectionStatus(status) {
        document.getElementById('connectionStatus').textContent = status;
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Trigger animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Remove after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }
    
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }
}

// Initialize the application
const app = new DiscordBotDevEnvironment();

// Make app globally available for onclick handlers
window.app = app;
window.closeModal = () => app.closeModal();