/**
 * HyperPanel — Domains Page
 */
async function renderDomains() {
    const content = document.getElementById('page-content');
    try {
        const domains = await API.get('/api/domains');
        content.innerHTML = `
            <div class="page-header"><div class="page-header-left"><h1>Domains</h1><p>Manage your registered domains</p></div>
            <div class="page-header-actions"><button class="btn btn-primary" onclick="showAddDomainModal()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg> Add Domain</button></div></div>
            ${domains.length > 0 ? `<div class="table-wrapper"><table class="table"><thead><tr><th>Domain</th><th>Status</th><th>DNS</th><th>Registrar</th><th>Expiry</th><th style="text-align:right">Actions</th></tr></thead><tbody>
                ${domains.map(d => `<tr><td><strong>${d.name}</strong></td><td><span class="badge ${d.status === 'active' ? 'badge-success' : 'badge-warning'}">${d.status}</span></td><td><span class="badge badge-neutral">${d.dns_managed}</span></td><td>${d.registrar || '—'}</td><td>${d.expiry_date || '—'}</td><td><div class="table-actions"><button class="btn btn-ghost btn-sm" onclick="window.location.hash='#/dns?domain=${d.id}'" title="DNS Records">🔧</button><button class="btn btn-ghost btn-sm btn-icon" onclick="deleteDomain(${d.id},'${d.name}')" style="color:var(--danger-400)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg></button></div></td></tr>`).join('')}
            </tbody></table></div>` : `<div class="card"><div class="card-body"><div class="empty-state"><div class="empty-state-icon">🌍</div><h3>No domains</h3><p>Add your first domain to start managing DNS records.</p><button class="btn btn-primary" onclick="showAddDomainModal()">Add Domain</button></div></div></div>`}`;
    } catch (e) { content.innerHTML = `<div class="card"><div class="card-body"><div class="empty-state"><h3>Error</h3><p>${e.message}</p></div></div></div>`; }
}

function showAddDomainModal() {
    openModal('Add Domain', `
        <div class="form-group"><label class="form-label">Domain Name</label><input type="text" class="form-input" id="new-domain-name" placeholder="example.com"></div>
        <div class="form-group"><label class="form-label">Registrar (optional)</label><input type="text" class="form-input" id="new-domain-registrar" placeholder="Namecheap, GoDaddy, etc."></div>
        <div class="form-group"><label class="form-label">DNS Management</label><select class="form-input" id="new-domain-dns"><option value="local">Local (managed by this panel)</option><option value="external">External (managed elsewhere)</option></select></div>
    `, `<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="addDomain()">Add Domain</button>`);
}

async function addDomain() {
    try {
        await API.post('/api/domains', { name: document.getElementById('new-domain-name').value, registrar: document.getElementById('new-domain-registrar').value || null, dns_managed: document.getElementById('new-domain-dns').value });
        closeModal(); showToast('Added', 'Domain added successfully', 'success'); renderDomains();
    } catch (e) { showToast('Error', e.message, 'error'); }
}

async function deleteDomain(id, name) {
    confirmModal('Delete Domain', `Delete "${name}" and all its DNS records?`, async () => {
        try { await API.delete(`/api/domains/${id}`); showToast('Deleted', `${name} removed`, 'success'); renderDomains(); } catch (e) { showToast('Error', e.message, 'error'); }
    });
}
