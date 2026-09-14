/**
 * HyperPanel — Log Viewer Page
 */
let _logSource = 'nginx_access';
let _logLines = 100;

async function renderLogs() {
    const content = document.getElementById('page-content');
    try {
        const sources = await API.get('/api/logs');
        const available = sources.filter(s => s.exists);
        const logData = await API.get(`/api/logs/${_logSource}?lines=${_logLines}`);

        content.innerHTML = `
            <div class="page-header"><div class="page-header-left"><h1>Log Viewer</h1><p>View system and service logs</p></div>
            <div class="page-header-actions">
                <button class="btn btn-ghost btn-sm" onclick="downloadLog('${_logSource}')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg> Download</button>
                <button class="btn btn-ghost btn-sm" onclick="renderLogs()"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15"/></svg> Refresh</button>
            </div></div>

            <div style="display:flex;gap:var(--space-3);margin-bottom:var(--space-4);flex-wrap:wrap;align-items:center">
                <div class="form-group" style="margin:0;flex:0 0 auto">
                    <select class="form-input" id="log-source-select" onchange="changeLogSource(this.value)" style="min-width:200px">
                        ${available.map(s => `<option value="${s.id}" ${s.id === _logSource ? 'selected' : ''}>${s.label}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group" style="margin:0;flex:0 0 auto">
                    <select class="form-input" onchange="changeLogLines(this.value)" style="min-width:100px">
                        ${[100, 500, 1000, 5000].map(n => `<option value="${n}" ${_logLines === n ? 'selected' : ''}>${n} lines</option>`).join('')}
                    </select>
                </div>
                <div class="form-group" style="margin:0;flex:1">
                    <input type="text" class="form-input" id="log-search" placeholder="Search logs..." onkeydown="if(event.key==='Enter')searchLogs()">
                </div>
                <button class="btn btn-ghost btn-sm" onclick="searchLogs()">Search</button>
            </div>

            <div style="display:flex;gap:var(--space-3);margin-bottom:var(--space-3);font-size:var(--text-xs);color:var(--text-tertiary)">
                <span>${logData.total_lines?.toLocaleString() || 0} total lines</span>
                <span>·</span>
                <span>${logData.file_size ? (logData.file_size / 1024 / 1024).toFixed(2) + ' MB' : '—'}</span>
                <span>·</span>
                <span>Showing last ${logData.lines?.length || 0} lines</span>
            </div>

            <div class="card" style="padding:0;overflow:hidden">
                <pre id="log-output" style="margin:0;padding:var(--space-4);background:var(--bg-primary);color:var(--text-secondary);font-family:'JetBrains Mono',monospace;font-size:12px;line-height:1.6;max-height:600px;overflow:auto;white-space:pre-wrap;word-break:break-all">${logData.lines?.length > 0 ? logData.lines.map(l => escapeHtml(l)).join('\n') : 'No log entries found.'}</pre>
            </div>`;

        // Auto-scroll to bottom
        const output = document.getElementById('log-output');
        if (output) output.scrollTop = output.scrollHeight;
    } catch (e) { content.innerHTML = `<div class="empty-state"><h3>Error</h3><p>${e.message}</p></div>`; }
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function changeLogSource(source) { _logSource = source; renderLogs(); }
function changeLogLines(lines) { _logLines = parseInt(lines); renderLogs(); }

async function searchLogs() {
    const search = document.getElementById('log-search')?.value;
    try {
        const logData = await API.get(`/api/logs/${_logSource}?lines=${_logLines}${search ? '&search=' + encodeURIComponent(search) : ''}`);
        const output = document.getElementById('log-output');
        if (output) {
            output.textContent = logData.lines?.length > 0 ? logData.lines.join('\n') : 'No matching entries found.';
            output.scrollTop = output.scrollHeight;
        }
    } catch (e) { showToast('Error', e.message, 'error'); }
}

function downloadLog(logId) { window.open(`/api/logs/${logId}/download`, '_blank'); }
