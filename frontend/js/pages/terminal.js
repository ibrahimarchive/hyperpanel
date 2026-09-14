/**
 * HyperPanel — Web Terminal Page (xterm.js)
 */
async function renderTerminal() {
    const content = document.getElementById('page-content');

    content.innerHTML = `
        <div class="page-header" style="margin-bottom:var(--space-3)"><div class="page-header-left"><h1>Terminal</h1><p>Secure shell access</p></div>
        <div class="page-header-actions">
            <button class="btn btn-ghost btn-sm" onclick="reconnectTerminal()"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15"/></svg> Reconnect</button>
        </div></div>
        <div id="terminal-container" style="background:#1a1b26;border-radius:var(--radius-lg);padding:var(--space-2);height:calc(100vh - 200px);min-height:400px"></div>
        <div style="display:flex;justify-content:space-between;margin-top:var(--space-2);font-size:var(--text-xs);color:var(--text-tertiary)">
            <span id="terminal-status">Connecting...</span>
            <span>Tip: Use Ctrl+Shift+V to paste</span>
        </div>`;

    initTerminalSession();
}

let _term = null;
let _termWs = null;
let _fitAddon = null;

function initTerminalSession() {
    // Check if xterm.js is loaded
    if (typeof Terminal === 'undefined') {
        document.getElementById('terminal-status').textContent = 'Error: xterm.js not loaded';
        document.getElementById('terminal-container').innerHTML = `
            <div style="display:flex;align-items:center;justify-content:center;height:100%;color:#888;flex-direction:column;gap:16px">
                <div style="font-size:24px">💻</div>
                <div>Terminal requires a Linux server with PTY support.</div>
                <div style="font-size:12px;opacity:0.6">xterm.js library could not be loaded.</div>
            </div>`;
        return;
    }

    const container = document.getElementById('terminal-container');

    // Create terminal
    _term = new Terminal({
        cursorBlink: true,
        fontSize: 14,
        fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
        theme: {
            background: '#1a1b26',
            foreground: '#c0caf5',
            cursor: '#c0caf5',
            selectionBackground: '#33467c',
            black: '#15161e',
            red: '#f7768e',
            green: '#9ece6a',
            yellow: '#e0af68',
            blue: '#7aa2f7',
            magenta: '#bb9af7',
            cyan: '#7dcfff',
            white: '#a9b1d6',
        },
        allowTransparency: false,
        scrollback: 5000,
    });

    // Fit addon
    if (typeof FitAddon !== 'undefined') {
        _fitAddon = new FitAddon.FitAddon();
        _term.loadAddon(_fitAddon);
    }

    // Web links addon
    if (typeof WebLinksAddon !== 'undefined') {
        _term.loadAddon(new WebLinksAddon.WebLinksAddon());
    }

    _term.open(container);

    if (_fitAddon) {
        _fitAddon.fit();
        window.addEventListener('resize', () => { if (_fitAddon) _fitAddon.fit(); });
    }

    connectTerminalWs();
}

function connectTerminalWs() {
    const token = localStorage.getItem('hyperpanel-token');
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/terminal?token=${token}`;

    _termWs = new WebSocket(wsUrl);

    _termWs.onopen = () => {
        document.getElementById('terminal-status').textContent = 'Connected';
        // Send initial resize
        if (_fitAddon && _term) {
            const dims = _fitAddon.proposeDimensions();
            if (dims) {
                _termWs.send(JSON.stringify({ type: 'resize', cols: dims.cols, rows: dims.rows }));
            }
        }
    };

    _termWs.onmessage = (event) => {
        if (_term) _term.write(event.data);
    };

    _termWs.onclose = () => {
        document.getElementById('terminal-status').textContent = 'Disconnected';
        if (_term) _term.write('\r\n\x1b[31m[Connection closed]\x1b[0m\r\n');
    };

    _termWs.onerror = () => {
        document.getElementById('terminal-status').textContent = 'Connection error';
    };

    // Send input to server
    if (_term) {
        _term.onData((data) => {
            if (_termWs && _termWs.readyState === WebSocket.OPEN) {
                _termWs.send(JSON.stringify({ type: 'input', data: data }));
            }
        });

        _term.onResize(({ cols, rows }) => {
            if (_termWs && _termWs.readyState === WebSocket.OPEN) {
                _termWs.send(JSON.stringify({ type: 'resize', cols, rows }));
            }
        });
    }
}

function reconnectTerminal() {
    if (_termWs) _termWs.close();
    if (_term) _term.clear();
    connectTerminalWs();
}
