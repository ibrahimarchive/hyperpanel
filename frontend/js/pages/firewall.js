/**
 * HyperPanel — Firewall Page
 */
async function renderFirewall() {
    const content = document.getElementById('page-content');
    try {
        const status = await API.get('/api/firewall/status');
        const rules = await API.get('/api/firewall/rules');
        content.innerHTML = `
            <div class="page-header"><div class="page-header-left"><h1>Firewall</h1><p>Manage UFW firewall rules</p></div>
            <div class="page-header-actions"><button class="btn btn-primary" onclick="showAddRuleModal()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg> Add Rule</button></div></div>

            <div class="card" style="margin-bottom:var(--space-5)"><div class="card-body" style="display:flex;align-items:center;justify-content:space-between">
                <div style="display:flex;align-items:center;gap:var(--space-4)">
                    <span class="status-dot ${status.enabled ? 'online' : 'offline'}" style="width:12px;height:12px"></span>
                    <div><div style="font-weight:var(--font-semibold)">${status.enabled ? 'Firewall Active' : 'Firewall Inactive'}</div><div style="font-size:var(--text-xs);color:var(--text-tertiary)">Default: incoming ${status.default_incoming || 'deny'}, outgoing ${status.default_outgoing || 'allow'}</div></div>
                </div>
                <label class="toggle"><input type="checkbox" ${status.enabled ? 'checked' : ''} onchange="toggleFirewall(this.checked)"><span class="toggle-slider"></span></label>
            </div></div>

            ${rules.managed_rules.length > 0 ? `<div class="table-wrapper"><table class="table"><thead><tr><th>Action</th><th>Port</th><th>Protocol</th><th>Source</th><th>Description</th><th style="text-align:right">Actions</th></tr></thead><tbody>
                ${rules.managed_rules.map(r => `<tr><td><span class="badge ${r.action === 'allow' ? 'badge-success' : r.action === 'deny' ? 'badge-danger' : 'badge-warning'}">${r.action.toUpperCase()}</span></td><td><strong>${r.port}</strong></td><td>${r.protocol}</td><td>${r.source_ip || 'Any'}</td><td style="color:var(--text-tertiary);font-size:var(--text-xs)">${r.description || '—'}</td><td><div class="table-actions"><button class="btn btn-ghost btn-sm btn-icon" onclick="deleteRule(${r.id})" style="color:var(--danger-400)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg></button></div></td></tr>`).join('')}
            </tbody></table></div>` : `<div class="card"><div class="card-body"><div class="empty-state"><div class="empty-state-icon">🛡️</div><h3>No rules</h3><p>Add firewall rules to secure your server.</p></div></div></div>`}`;
    } catch (e) { content.innerHTML = `<div class="empty-state"><h3>Error</h3><p>${e.message}</p></div>`; }
}

function showAddRuleModal() {
    openModal('Add Firewall Rule', `
        <div class="form-group"><label class="form-label">Action</label><select class="form-input" id="fw-action"><option value="allow">Allow</option><option value="deny">Deny</option><option value="limit">Limit</option></select></div>
        <div class="form-group"><label class="form-label">Port</label><input type="text" class="form-input" id="fw-port" placeholder="80 or 8000:8100"></div>
        <div class="form-group"><label class="form-label">Protocol</label><select class="form-input" id="fw-proto"><option value="tcp">TCP</option><option value="udp">UDP</option><option value="both">Both</option></select></div>
        <div class="form-group"><label class="form-label">Source IP (optional)</label><input type="text" class="form-input" id="fw-source" placeholder="Any"></div>
        <div class="form-group"><label class="form-label">Description</label><input type="text" class="form-input" id="fw-desc" placeholder="HTTP traffic"></div>
    `, `<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="addRule()">Add Rule</button>`);
}

async function addRule() {
    try {
        await API.post('/api/firewall/rules', { action: document.getElementById('fw-action').value, port: document.getElementById('fw-port').value, protocol: document.getElementById('fw-proto').value, source_ip: document.getElementById('fw-source').value || null, description: document.getElementById('fw-desc').value || null });
        closeModal(); showToast('Added', 'Firewall rule added', 'success'); renderFirewall();
    } catch (e) { showToast('Error', e.message, 'error'); }
}

async function deleteRule(id) { confirmModal('Delete Rule', 'Remove this firewall rule?', async () => { try { await API.delete(`/api/firewall/rules/${id}`); showToast('Deleted', 'Rule removed', 'success'); renderFirewall(); } catch (e) { showToast('Error', e.message, 'error'); } }); }

async function toggleFirewall(enable) { try { await API.post(`/api/firewall/toggle?enable=${enable}`); showToast('Success', `Firewall ${enable ? 'enabled' : 'disabled'}`, 'success'); renderFirewall(); } catch (e) { showToast('Error', e.message, 'error'); } }
