/**
 * HyperPanel — SSL Certificates Page
 */
async function renderSSL() {
    const content = document.getElementById('page-content');
    try {
        const certs = await API.get('/api/ssl');
        content.innerHTML = `
            <div class="page-header"><div class="page-header-left"><h1>SSL / TLS</h1><p>Manage SSL certificates for your domains</p></div>
            <div class="page-header-actions"><button class="btn btn-primary" onclick="showIssueSSLModal()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg> Issue Certificate</button></div></div>
            ${certs.length > 0 ? `<div class="table-wrapper"><table class="table"><thead><tr><th>Domain</th><th>Type</th><th>Status</th><th>Issuer</th><th>Expires</th><th>Auto-Renew</th><th style="text-align:right">Actions</th></tr></thead><tbody>
                ${certs.map(c => `<tr><td><strong>🔒 ${c.domain_name}</strong></td><td><span class="badge badge-neutral">${c.cert_type}</span></td><td><span class="badge ${c.status === 'active' ? 'badge-success' : 'badge-danger'}">${c.status}</span></td><td>${c.issuer || '—'}</td><td>${c.expires_at ? new Date(c.expires_at).toLocaleDateString() : '—'}</td><td>${c.auto_renew ? '✅' : '—'}</td><td><div class="table-actions"><button class="btn btn-ghost btn-sm btn-icon" onclick="deleteSSL(${c.id},'${c.domain_name}')" style="color:var(--danger-400)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg></button></div></td></tr>`).join('')}
            </tbody></table></div>` : `<div class="card"><div class="card-body"><div class="empty-state"><div class="empty-state-icon">🔒</div><h3>No certificates</h3><p>Issue a free Let's Encrypt certificate for your domains.</p><button class="btn btn-primary" onclick="showIssueSSLModal()">Issue Certificate</button></div></div></div>`}`;
    } catch (e) { content.innerHTML = `<div class="empty-state"><h3>Error</h3><p>${e.message}</p></div>`; }
}

function showIssueSSLModal() {
    openModal('Issue SSL Certificate', `
        <div class="form-group"><label class="form-label">Domain Name</label><input type="text" class="form-input" id="ssl-domain" placeholder="example.com"></div>
        <div class="form-group"><label class="form-label" style="display:flex;align-items:center;gap:var(--space-2)"><label class="toggle"><input type="checkbox" id="ssl-auto-renew" checked><span class="toggle-slider"></span></label> Auto-renew certificate</label></div>
        <p style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:var(--space-2)">A free Let's Encrypt certificate will be issued. Your domain must point to this server.</p>
    `, `<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="issueSSL()">Issue Certificate</button>`);
}

async function issueSSL() {
    try {
        await API.post('/api/ssl/issue', { domain_name: document.getElementById('ssl-domain').value, auto_renew: document.getElementById('ssl-auto-renew').checked });
        closeModal(); showToast('Issued', 'SSL certificate issued successfully', 'success'); renderSSL();
    } catch (e) { showToast('Error', e.message, 'error'); }
}

async function deleteSSL(id, domain) {
    confirmModal('Delete Certificate', `Revoke and remove the certificate for "${domain}"?`, async () => {
        try { await API.delete(`/api/ssl/${id}`); showToast('Deleted', 'Certificate removed', 'success'); renderSSL(); } catch (e) { showToast('Error', e.message, 'error'); }
    });
}
