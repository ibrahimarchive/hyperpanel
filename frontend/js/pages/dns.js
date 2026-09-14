/**
 * HyperPanel — DNS Records Page
 */
async function renderDNS() {
    const content = document.getElementById('page-content');
    try {
        const domains = await API.get('/api/domains');
        const urlParams = new URLSearchParams(window.location.hash.split('?')[1]);
        let selectedDomain = urlParams.get('domain') ? parseInt(urlParams.get('domain')) : (domains[0]?.id || null);

        let records = [];
        if (selectedDomain) { records = await API.get(`/api/dns/${selectedDomain}/records`); }

        content.innerHTML = `
            <div class="page-header"><div class="page-header-left"><h1>DNS Records</h1><p>Manage DNS zones for your domains</p></div>
            <div class="page-header-actions"><button class="btn btn-primary" onclick="showAddRecordModal(${selectedDomain})"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg> Add Record</button></div></div>
            ${domains.length > 0 ? `
            <div class="form-group" style="max-width:300px;margin-bottom:var(--space-5)"><label class="form-label">Select Domain</label><select class="form-input" id="dns-domain-select" onchange="window.location.hash='#/dns?domain='+this.value">
                ${domains.map(d => `<option value="${d.id}" ${d.id === selectedDomain ? 'selected' : ''}>${d.name}</option>`).join('')}
            </select></div>
            ${records.length > 0 ? `<div class="table-wrapper"><table class="table"><thead><tr><th>Type</th><th>Name</th><th>Value</th><th>TTL</th><th>Priority</th><th style="text-align:right">Actions</th></tr></thead><tbody>
                ${records.map(r => `<tr><td><span class="badge badge-info">${r.record_type}</span></td><td><strong>${r.name}</strong></td><td style="max-width:250px;overflow:hidden;text-overflow:ellipsis">${r.value}</td><td>${r.ttl}</td><td>${r.priority || '—'}</td><td><div class="table-actions"><button class="btn btn-ghost btn-sm btn-icon" onclick="deleteDnsRecord(${r.id},${selectedDomain})" style="color:var(--danger-400)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg></button></div></td></tr>`).join('')}
            </tbody></table></div>` : `<div class="card"><div class="card-body"><div class="empty-state"><div class="empty-state-icon">📋</div><h3>No DNS records</h3><p>Add records for this domain.</p></div></div></div>`}
            ` : `<div class="card"><div class="card-body"><div class="empty-state"><h3>No domains</h3><p>Add a domain first to manage DNS records.</p></div></div></div>`}`;
    } catch (e) { content.innerHTML = `<div class="empty-state"><h3>Error</h3><p>${e.message}</p></div>`; }
}

function showAddRecordModal(domainId) {
    if (!domainId) { showToast('Error', 'Select a domain first', 'warning'); return; }
    openModal('Add DNS Record', `
        <div class="form-group"><label class="form-label">Record Type</label><select class="form-input" id="dns-type"><option>A</option><option>AAAA</option><option>CNAME</option><option>MX</option><option>TXT</option><option>NS</option><option>SRV</option></select></div>
        <div class="form-group"><label class="form-label">Name</label><input type="text" class="form-input" id="dns-name" placeholder="@ or subdomain"></div>
        <div class="form-group"><label class="form-label">Value</label><input type="text" class="form-input" id="dns-value" placeholder="IP address or hostname"></div>
        <div class="form-group"><label class="form-label">TTL</label><input type="number" class="form-input" id="dns-ttl" value="3600"></div>
        <div class="form-group"><label class="form-label">Priority (MX/SRV)</label><input type="number" class="form-input" id="dns-priority" placeholder="10"></div>
    `, `<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="addDnsRecord(${domainId})">Add Record</button>`);
}

async function addDnsRecord(domainId) {
    try {
        await API.post('/api/dns/records', { domain_id: domainId, record_type: document.getElementById('dns-type').value, name: document.getElementById('dns-name').value, value: document.getElementById('dns-value').value, ttl: parseInt(document.getElementById('dns-ttl').value), priority: document.getElementById('dns-priority').value ? parseInt(document.getElementById('dns-priority').value) : null });
        closeModal(); showToast('Added', 'DNS record created', 'success'); renderDNS();
    } catch (e) { showToast('Error', e.message, 'error'); }
}

async function deleteDnsRecord(id, domainId) {
    confirmModal('Delete Record', 'Delete this DNS record?', async () => {
        try { await API.delete(`/api/dns/records/${id}`); showToast('Deleted', 'Record removed', 'success'); renderDNS(); } catch (e) { showToast('Error', e.message, 'error'); }
    });
}
