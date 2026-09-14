/**
 * HyperPanel — Fail2Ban Page
 */
async function renderFail2Ban() {
    const content = document.getElementById('page-content');
    try {
        const status = await API.get('/api/fail2ban/status');

        if (!status.installed) {
            content.innerHTML = `
                <div class="page-header"><div class="page-header-left"><h1>Fail2Ban</h1><p>Intrusion prevention</p></div></div>
                <div class="card"><div class="card-body" style="text-align:center;padding:var(--space-8)">
                    <div style="font-size:48px;margin-bottom:var(--space-4)">🛡️</div>
                    <h2 style="margin-bottom:var(--space-2)">Fail2Ban Not Installed</h2>
                    <p style="color:var(--text-tertiary);margin-bottom:var(--space-5);max-width:400px;margin-left:auto;margin-right:auto">Fail2Ban protects your server from brute-force attacks by monitoring log files and banning suspicious IPs.</p>
                    <button class="btn btn-primary" onclick="installFail2Ban()">Install Fail2Ban</button>
                </div></div>`;
            return;
        }

        const jails = await API.get('/api/fail2ban/jails');

        content.innerHTML = `
            <div class="page-header"><div class="page-header-left"><h1>Fail2Ban</h1><p>${status.version || 'Intrusion prevention'}</p></div>
            <div class="page-header-actions"><button class="btn btn-primary" onclick="showManualBanModal()">Ban IP</button></div></div>

            <div class="grid grid-3" style="margin-bottom:var(--space-5)">
                <div class="stat-card"><div class="stat-card-value"><span class="status-dot ${status.running ? 'online' : 'offline'}" style="width:10px;height:10px;display:inline-block;margin-right:8px"></span>${status.running ? 'Active' : 'Inactive'}</div><div class="stat-card-label">Status</div></div>
                <div class="stat-card"><div class="stat-card-value">${status.jails}</div><div class="stat-card-label">Active Jails</div></div>
                <div class="stat-card"><div class="stat-card-value">${jails.reduce((sum, j) => sum + j.currently_banned, 0)}</div><div class="stat-card-label">Currently Banned</div></div>
            </div>

            ${jails.length > 0 ? `<div class="table-wrapper"><table class="table"><thead><tr><th>Jail</th><th>Currently Failed</th><th>Total Failed</th><th>Currently Banned</th><th>Total Banned</th><th style="text-align:right">Actions</th></tr></thead><tbody>
                ${jails.map(j => `<tr>
                    <td style="font-weight:var(--font-semibold)">${j.name}</td>
                    <td>${j.currently_failed}</td>
                    <td>${j.total_failed}</td>
                    <td><span class="badge ${j.currently_banned > 0 ? 'badge-danger' : 'badge-success'}">${j.currently_banned}</span></td>
                    <td>${j.total_banned}</td>
                    <td><div class="table-actions"><button class="btn btn-ghost btn-sm" onclick="showJailDetail('${j.name}')">View Bans</button></div></td>
                </tr>`).join('')}
            </tbody></table></div>` : `<div class="card"><div class="card-body"><div class="empty-state"><div class="empty-state-icon">🛡️</div><h3>No jails active</h3><p>Fail2Ban is installed but no jails are configured.</p></div></div></div>`}`;
    } catch (e) { content.innerHTML = `<div class="empty-state"><h3>Error</h3><p>${e.message}</p></div>`; }
}

async function installFail2Ban() {
    if (!confirm('Install Fail2Ban?')) return;
    showToast('Installing', 'Installing Fail2Ban...', 'info');
    try { await API.post('/api/fail2ban/install'); showToast('Installed', 'Fail2Ban installed', 'success'); renderFail2Ban(); } catch (e) { showToast('Error', e.message, 'error'); }
}

async function showJailDetail(name) {
    try {
        const jail = await API.get(`/api/fail2ban/jails/${name}`);
        const bannedList = jail.banned_ips.length > 0
            ? jail.banned_ips.map(ip => `<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border-primary)"><code>${ip}</code><button class="btn btn-ghost btn-sm" onclick="unbanIP('${name}','${ip}')" style="color:var(--success-400)">Unban</button></div>`).join('')
            : '<div style="text-align:center;color:var(--text-tertiary);padding:var(--space-4)">No IPs currently banned</div>';
        openModal(`Jail: ${name}`, `
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-3);margin-bottom:var(--space-4)">
                <div style="text-align:center;padding:var(--space-3);background:var(--bg-tertiary);border-radius:var(--radius-md)"><div style="font-size:var(--text-xl);font-weight:var(--font-bold)">${jail.currently_banned}</div><div style="font-size:var(--text-xs);color:var(--text-tertiary)">Currently Banned</div></div>
                <div style="text-align:center;padding:var(--space-3);background:var(--bg-tertiary);border-radius:var(--radius-md)"><div style="font-size:var(--text-xl);font-weight:var(--font-bold)">${jail.total_banned}</div><div style="font-size:var(--text-xs);color:var(--text-tertiary)">Total Banned</div></div>
            </div>
            <h4 style="margin-bottom:var(--space-2)">Banned IPs</h4>
            ${bannedList}
        `, `<button class="btn btn-secondary" onclick="closeModal()">Close</button>`);
    } catch (e) { showToast('Error', e.message, 'error'); }
}

function showManualBanModal() {
    openModal('Ban IP Address', `
        <div class="form-group"><label class="form-label">Jail</label><input type="text" class="form-input" id="f2b-jail" value="sshd" placeholder="sshd"></div>
        <div class="form-group"><label class="form-label">IP Address</label><input type="text" class="form-input" id="f2b-ip" placeholder="192.168.1.100"></div>
    `, `<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-danger" onclick="manualBan()">Ban</button>`);
}

async function manualBan() {
    try {
        await API.post(`/api/fail2ban/jails/${document.getElementById('f2b-jail').value}/ban`, { ip: document.getElementById('f2b-ip').value });
        closeModal(); showToast('Banned', 'IP banned successfully', 'success'); renderFail2Ban();
    } catch (e) { showToast('Error', e.message, 'error'); }
}

async function unbanIP(jail, ip) {
    try { await API.post(`/api/fail2ban/jails/${jail}/unban`, { ip }); showToast('Unbanned', `${ip} unbanned`, 'success'); closeModal(); renderFail2Ban(); } catch (e) { showToast('Error', e.message, 'error'); }
}
