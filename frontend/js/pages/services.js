/**
 * HyperPanel — Services Page
 */
async function renderServices() {
    const content = document.getElementById('page-content');
    try {
        const services = await API.get('/api/services');

        // Group by category
        const groups = {};
        services.forEach(s => {
            if (!groups[s.category]) groups[s.category] = [];
            groups[s.category].push(s);
        });

        const categoryLabels = { web: 'Web Server', database: 'Database', php: 'PHP', cache: 'Cache', security: 'Security', mail: 'Mail', container: 'Containers', panel: 'Panel' };
        const categoryIcons = { web: '🌐', database: '🗄️', php: '🐘', cache: '⚡', security: '🛡️', mail: '📧', container: '🐳', panel: '⚙️' };

        content.innerHTML = `
            <div class="page-header"><div class="page-header-left"><h1>Services</h1><p>Manage system services</p></div></div>

            ${Object.entries(groups).map(([cat, svcs]) => `
                <div style="margin-bottom:var(--space-5)">
                    <h3 style="font-size:var(--text-sm);color:var(--text-tertiary);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:var(--space-3)">${categoryIcons[cat] || '📦'} ${categoryLabels[cat] || cat}</h3>
                    <div class="grid grid-2">
                        ${svcs.map(s => `
                            <div class="card">
                                <div class="card-body" style="display:flex;align-items:center;justify-content:space-between">
                                    <div style="display:flex;align-items:center;gap:var(--space-3)">
                                        <span class="status-dot ${s.active ? 'online' : 'offline'}" style="width:10px;height:10px"></span>
                                        <div>
                                            <div style="font-weight:var(--font-semibold)">${s.label}</div>
                                            <div style="font-size:var(--text-xs);color:var(--text-tertiary)">${s.description}${s.memory_bytes > 0 ? ` · ${(s.memory_bytes / 1024 / 1024).toFixed(1)} MB` : ''}${s.main_pid > 0 ? ` · PID ${s.main_pid}` : ''}</div>
                                        </div>
                                    </div>
                                    <div style="display:flex;gap:var(--space-2)">
                                        ${!s.active ? `<button class="btn btn-ghost btn-sm" onclick="serviceAction('${s.name}','start')" style="color:var(--success-400)">Start</button>` : ''}
                                        ${s.active ? `<button class="btn btn-ghost btn-sm" onclick="serviceAction('${s.name}','stop')" style="color:var(--danger-400)">Stop</button>` : ''}
                                        ${s.active ? `<button class="btn btn-ghost btn-sm" onclick="serviceAction('${s.name}','restart')" style="color:var(--warning-400)">Restart</button>` : ''}
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('')}

            ${services.length === 0 ? `<div class="card"><div class="card-body"><div class="empty-state"><div class="empty-state-icon">⚙️</div><h3>No services detected</h3><p>Services will appear here when running on a Linux server.</p></div></div></div>` : ''}`;
    } catch (e) { content.innerHTML = `<div class="empty-state"><h3>Error</h3><p>${e.message}</p></div>`; }
}

async function serviceAction(name, action) {
    try {
        await API.post(`/api/services/${name}/${action}`);
        showToast('Success', `Service ${name} ${action}ed`, 'success');
        renderServices();
    } catch (e) { showToast('Error', e.message, 'error'); }
}
