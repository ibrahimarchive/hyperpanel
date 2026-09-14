/**
 * HyperPanel — Processes Page
 */
let _procSort = 'cpu';
let _procRefreshInterval = null;

async function renderProcesses() {
    const content = document.getElementById('page-content');
    try {
        const processes = await API.get(`/api/processes?sort=${_procSort}&limit=50`);
        const summary = await API.get('/api/processes/summary');

        content.innerHTML = `
            <div class="page-header"><div class="page-header-left"><h1>Processes</h1><p>Running system processes</p></div>
            <div class="page-header-actions">
                <button class="btn ${_procSort === 'cpu' ? 'btn-primary' : 'btn-ghost'} btn-sm" onclick="sortProcesses('cpu')">Sort by CPU</button>
                <button class="btn ${_procSort === 'memory' ? 'btn-primary' : 'btn-ghost'} btn-sm" onclick="sortProcesses('memory')">Sort by Memory</button>
            </div></div>

            <div class="grid grid-4" style="margin-bottom:var(--space-5)">
                <div class="stat-card"><div class="stat-card-value">${summary.total}</div><div class="stat-card-label">Total Processes</div></div>
                <div class="stat-card"><div class="stat-card-value">${summary.running}</div><div class="stat-card-label">Running</div></div>
                <div class="stat-card"><div class="stat-card-value">${summary.zombie}</div><div class="stat-card-label">Zombie</div></div>
                <div class="stat-card"><div class="stat-card-value">${summary.load_avg_1} / ${summary.load_avg_5} / ${summary.load_avg_15}</div><div class="stat-card-label">Load Average (1/5/15 min)</div></div>
            </div>

            <div class="table-wrapper"><table class="table"><thead><tr>
                <th>PID</th><th>Name</th><th>User</th><th>CPU %</th><th>Memory %</th><th>Memory</th><th>Status</th><th style="text-align:right">Action</th>
            </tr></thead><tbody>
                ${processes.map(p => `<tr>
                    <td><code>${p.pid}</code></td>
                    <td style="font-weight:var(--font-medium)">${p.name}</td>
                    <td style="font-size:var(--text-xs)">${p.username}</td>
                    <td><div style="display:flex;align-items:center;gap:var(--space-2)"><div style="width:60px;height:4px;background:var(--bg-tertiary);border-radius:2px;overflow:hidden"><div style="width:${Math.min(p.cpu_percent, 100)}%;height:100%;background:${p.cpu_percent > 80 ? 'var(--danger-400)' : p.cpu_percent > 50 ? 'var(--warning-400)' : 'var(--success-400)'}"></div></div><span style="font-size:var(--text-xs)">${p.cpu_percent}%</span></div></td>
                    <td><div style="display:flex;align-items:center;gap:var(--space-2)"><div style="width:60px;height:4px;background:var(--bg-tertiary);border-radius:2px;overflow:hidden"><div style="width:${Math.min(p.memory_percent, 100)}%;height:100%;background:${p.memory_percent > 80 ? 'var(--danger-400)' : p.memory_percent > 50 ? 'var(--warning-400)' : 'var(--primary-400)'}"></div></div><span style="font-size:var(--text-xs)">${p.memory_percent}%</span></div></td>
                    <td style="font-size:var(--text-xs)">${p.memory_rss > 0 ? (p.memory_rss / 1024 / 1024).toFixed(1) + ' MB' : '—'}</td>
                    <td><span class="badge ${p.status === 'running' ? 'badge-success' : p.status === 'sleeping' ? 'badge-secondary' : p.status === 'zombie' ? 'badge-danger' : 'badge-warning'}">${p.status}</span></td>
                    <td><div class="table-actions"><button class="btn btn-ghost btn-sm btn-icon" onclick="killProcess(${p.pid}, '${p.name}')" style="color:var(--danger-400)" title="Kill Process"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg></button></div></td>
                </tr>`).join('')}
            </tbody></table></div>

            <div style="text-align:center;margin-top:var(--space-3);font-size:var(--text-xs);color:var(--text-tertiary)">Auto-refreshes every 5 seconds</div>`;

        // Auto-refresh
        clearInterval(_procRefreshInterval);
        _procRefreshInterval = setInterval(() => {
            if (window.location.hash === '#/processes') renderProcesses();
            else clearInterval(_procRefreshInterval);
        }, 5000);
    } catch (e) { content.innerHTML = `<div class="empty-state"><h3>Error</h3><p>${e.message}</p></div>`; }
}

function sortProcesses(by) { _procSort = by; renderProcesses(); }

async function killProcess(pid, name) {
    confirmModal('Kill Process', `Terminate process <strong>${name}</strong> (PID ${pid})?`, async () => {
        try {
            await API.post(`/api/processes/${pid}/kill`);
            showToast('Killed', `Process ${name} (${pid}) terminated`, 'success');
            renderProcesses();
        } catch (e) { showToast('Error', e.message, 'error'); }
    });
}
