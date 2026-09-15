/**
 * HyperPanel — SSL / TLS Certificates Page
 * Shows all websites with SSL status and allows installing Let's Encrypt or viewing existing certs.
 */

let _sslWebsites = [];
let _sslCerts = [];

async function renderSSL() {
    const content = document.getElementById('page-content');

    try {
        const [websites, certs] = await Promise.all([
            API.get('/api/websites'),
            API.get('/api/ssl'),
        ]);

        _sslWebsites = websites;
        _sslCerts = certs;

        // Map certs by domain for quick lookup
        const certMap = {};
        certs.forEach(c => { certMap[c.domain_name] = c; });

        content.innerHTML = `
            <div class="page-header">
                <div class="page-header-left">
                    <h1>SSL / TLS</h1>
                    <p>Manage HTTPS certificates for your websites</p>
                </div>
                <div class="page-header-actions">
                    <button class="btn btn-secondary" onclick="renewAllCerts()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15"/></svg>
                        Renew All
                    </button>
                    <button class="btn btn-primary" onclick="showIssueSSLModal()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
                        Issue Certificate
                    </button>
                </div>
            </div>

            <!-- Websites with SSL status -->
            ${websites.length > 0 ? `
                <div class="card" style="margin-bottom:var(--space-5)">
                    <div class="card-header" style="display:flex;justify-content:space-between;align-items:center">
                        <h3>Website Certificates</h3>
                        <span class="badge badge-neutral" style="font-size:11px">${certs.filter(c => c.status === 'active').length}/${websites.length} Secured</span>
                    </div>
                    <div class="card-body" style="padding:0">
                        <div class="table-wrapper" style="margin:0">
                            <table class="table" style="margin:0">
                                <thead>
                                    <tr>
                                        <th>Domain</th>
                                        <th>Type</th>
                                        <th>SSL Status</th>
                                        <th>Issuer</th>
                                        <th>Expires</th>
                                        <th>Auto-Renew</th>
                                        <th style="text-align:right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${websites.map(w => {
                                        const cert = certMap[w.domain];
                                        const hasCert = cert && cert.status === 'active';
                                        return `
                                            <tr>
                                                <td>
                                                    <div style="display:flex;align-items:center;gap:var(--space-2)">
                                                        <span style="font-size:16px">${hasCert ? '🔒' : '🔓'}</span>
                                                        <div>
                                                            <div style="font-weight:var(--font-medium)">${w.domain}</div>
                                                            <div style="font-size:var(--text-xs);color:var(--text-tertiary)">${w.site_type}</div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td>
                                                    ${hasCert
                                                        ? `<span class="badge badge-success" style="font-size:10px">${cert.cert_type}</span>`
                                                        : `<span class="badge badge-neutral" style="font-size:10px">None</span>`
                                                    }
                                                </td>
                                                <td>
                                                    ${hasCert
                                                        ? `<span class="badge badge-success">🛡️ Secured</span>`
                                                        : `<span class="badge badge-danger" style="background:rgba(239,68,68,0.12);color:#ef4444;border:1px solid rgba(239,68,68,0.25)">Not Secured</span>`
                                                    }
                                                </td>
                                                <td style="font-size:var(--text-xs);color:var(--text-secondary)">${hasCert ? (cert.issuer || '—') : '—'}</td>
                                                <td style="font-size:var(--text-xs);color:var(--text-secondary)">
                                                    ${hasCert && cert.expires_at ? new Date(cert.expires_at).toLocaleDateString() : '—'}
                                                </td>
                                                <td>${hasCert ? (cert.auto_renew ? '<span style="color:#22c55e">✓ Yes</span>' : '<span style="color:var(--text-tertiary)">No</span>') : '—'}</td>
                                                <td>
                                                    <div class="table-actions">
                                                        ${hasCert ? `
                                                            <button class="btn btn-ghost btn-sm" onclick="showCertDetails('${w.domain}')" title="Details" style="font-size:11px">
                                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                                                                Details
                                                            </button>
                                                            <button class="btn btn-ghost btn-sm btn-icon" onclick="deleteSSL(${cert.id},'${w.domain}')" title="Remove" style="color:var(--danger-400)">
                                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                                                            </button>
                                                        ` : `
                                                            <button class="btn btn-primary btn-sm" onclick="issueSSLForDomain('${w.domain}', ${w.id})" style="font-size:11px">
                                                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                                                                Install SSL
                                                            </button>
                                                        `}
                                                    </div>
                                                </td>
                                            </tr>
                                        `;
                                    }).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            ` : `
                <div class="card" style="margin-bottom:var(--space-5)">
                    <div class="card-body">
                        <div class="empty-state">
                            <div class="empty-state-icon">🌐</div>
                            <h3>No websites yet</h3>
                            <p>Create a website first, then you can secure it with SSL.</p>
                            <button class="btn btn-primary" onclick="window.location.hash='#/websites'">Go to Websites</button>
                        </div>
                    </div>
                </div>
            `}

            <!-- Standalone certificates (not linked to a website) -->
            ${(() => {
                const websiteDomains = new Set(websites.map(w => w.domain));
                const standaloneCerts = certs.filter(c => !websiteDomains.has(c.domain_name));
                if (standaloneCerts.length === 0) return '';
                return `
                    <div class="card">
                        <div class="card-header"><h3>Other Certificates</h3></div>
                        <div class="card-body" style="padding:0">
                            <div class="table-wrapper" style="margin:0">
                                <table class="table" style="margin:0">
                                    <thead><tr><th>Domain</th><th>Type</th><th>Status</th><th>Issuer</th><th>Expires</th><th style="text-align:right">Actions</th></tr></thead>
                                    <tbody>
                                        ${standaloneCerts.map(c => `
                                            <tr>
                                                <td><strong>🔒 ${c.domain_name}</strong></td>
                                                <td><span class="badge badge-neutral">${c.cert_type}</span></td>
                                                <td><span class="badge ${c.status === 'active' ? 'badge-success' : 'badge-danger'}">${c.status}</span></td>
                                                <td style="font-size:var(--text-xs)">${c.issuer || '—'}</td>
                                                <td style="font-size:var(--text-xs)">${c.expires_at ? new Date(c.expires_at).toLocaleDateString() : '—'}</td>
                                                <td><div class="table-actions">
                                                    <button class="btn btn-ghost btn-sm btn-icon" onclick="deleteSSL(${c.id},'${c.domain_name}')" style="color:var(--danger-400)">
                                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                                                    </button>
                                                </div></td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                `;
            })()}
        `;
    } catch (e) {
        content.innerHTML = `<div class="card"><div class="card-body"><div class="empty-state"><h3>Error</h3><p>${e.message}</p></div></div></div>`;
    }
}


/* ── Issue SSL Modal (dropdown of websites) ─────────────── */

function showIssueSSLModal() {
    const unsecuredSites = _sslWebsites.filter(w => {
        return !_sslCerts.find(c => c.domain_name === w.domain && c.status === 'active');
    });

    const siteOptions = unsecuredSites.length > 0
        ? unsecuredSites.map(w => `<option value="${w.domain}" data-id="${w.id}">${w.domain} (${w.site_type})</option>`).join('')
        : '<option value="">No unsecured websites</option>';

    const allSiteOptions = _sslWebsites.length > 0
        ? _sslWebsites.map(w => `<option value="${w.domain}" data-id="${w.id}">${w.domain} (${w.site_type})</option>`).join('')
        : '';

    openModal('Install SSL Certificate', `
        <div class="tabs" style="margin-bottom:var(--space-4)">
            <div class="tab active" onclick="showIssueSslTab('website', this)">From Website (Let's Encrypt)</div>
            <div class="tab" onclick="showIssueSslTab('manual', this)">Manual Domain (Let's Encrypt)</div>
            <div class="tab" onclick="showIssueSslTab('custom', this)">Upload Custom SSL</div>
        </div>

        <div id="tab-issue-website">
            <div class="form-group">
                <label class="form-label">Select Website</label>
                <select class="form-input" id="ssl-website-select">
                    ${siteOptions}
                </select>
            </div>
            <div class="form-group">
                <label class="form-label" style="display:flex;align-items:center;gap:var(--space-2)">
                    <label class="toggle"><input type="checkbox" id="ssl-auto-renew" checked><span class="toggle-slider"></span></label>
                    Auto-renew certificate before expiry
                </label>
            </div>
            <div class="setting-alert-callout" style="margin-top:var(--space-3)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                <span>DNS must point to this server. Certbot will verify domain ownership via HTTP challenge on port 80.</span>
            </div>
        </div>

        <div id="tab-issue-manual" style="display:none">
            <div class="form-group">
                <label class="form-label">Domain Name</label>
                <input type="text" class="form-input" id="ssl-manual-domain" placeholder="example.com">
            </div>
            <div class="form-group">
                <label class="form-label" style="display:flex;align-items:center;gap:var(--space-2)">
                    <label class="toggle"><input type="checkbox" id="ssl-auto-renew-manual" checked><span class="toggle-slider"></span></label>
                    Auto-renew certificate before expiry
                </label>
            </div>
            <div class="setting-alert-callout" style="margin-top:var(--space-3)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                <span>DNS must point to this server. Certbot will verify domain ownership via HTTP challenge on port 80.</span>
            </div>
        </div>

        <div id="tab-issue-custom" style="display:none">
            <div class="form-group">
                <label class="form-label">Target Website / Domain</label>
                <select class="form-input" id="ssl-custom-domain-select" onchange="toggleCustomDomainInput(this.value)">
                    <option value="__custom__">Custom / External Domain...</option>
                    ${allSiteOptions}
                </select>
            </div>
            <div class="form-group" id="group-custom-domain-input">
                <label class="form-label">Domain Name</label>
                <input type="text" class="form-input" id="ssl-custom-domain-text" placeholder="domain.com">
            </div>
            <div class="form-group">
                <label class="form-label">Certificate (PEM / CRT)</label>
                <textarea class="form-input" id="ssl-custom-crt" rows="4" placeholder="-----BEGIN CERTIFICATE-----&#10;...&#10;-----END CERTIFICATE-----" style="font-family:monospace;font-size:11px"></textarea>
            </div>
            <div class="form-group">
                <label class="form-label">Private Key (KEY)</label>
                <textarea class="form-input" id="ssl-custom-key" rows="4" placeholder="-----BEGIN PRIVATE KEY-----&#10;...&#10;-----END PRIVATE KEY-----" style="font-family:monospace;font-size:11px"></textarea>
            </div>
            <div class="form-group">
                <label class="form-label">Chain / CA Bundle (Optional)</label>
                <textarea class="form-input" id="ssl-custom-chain" rows="3" placeholder="-----BEGIN CERTIFICATE-----&#10;...&#10;-----END CERTIFICATE-----" style="font-family:monospace;font-size:11px"></textarea>
            </div>
        </div>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button class="btn btn-primary" id="btn-issue-ssl" onclick="submitIssueSSL()">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            Install Certificate
        </button>
    `);
}

function showIssueSslTab(tab, el) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('tab-issue-website').style.display = tab === 'website' ? 'block' : 'none';
    document.getElementById('tab-issue-manual').style.display = tab === 'manual' ? 'block' : 'none';
    document.getElementById('tab-issue-custom').style.display = tab === 'custom' ? 'block' : 'none';
}

function toggleCustomDomainInput(val) {
    document.getElementById('group-custom-domain-input').style.display = val === '__custom__' ? 'block' : 'none';
}

async function submitIssueSSL() {
    const isCustom = document.getElementById('tab-issue-custom').style.display !== 'none';
    const isManual = document.getElementById('tab-issue-manual').style.display !== 'none';
    const btn = document.getElementById('btn-issue-ssl');

    if (isCustom) {
        const selectVal = document.getElementById('ssl-custom-domain-select').value;
        const textVal = document.getElementById('ssl-custom-domain-text').value.trim();
        const domain = selectVal === '__custom__' ? textVal : selectVal;
        const certificate = document.getElementById('ssl-custom-crt').value.trim();
        const private_key = document.getElementById('ssl-custom-key').value.trim();
        const chain = document.getElementById('ssl-custom-chain').value.trim() || null;

        if (!domain || !certificate || !private_key) {
            showToast('Validation Error', 'Domain, Certificate, and Private Key are required', 'warning');
            return;
        }

        btn.disabled = true;
        btn.innerHTML = `<span class="spinner spinner-sm" style="display:inline-block;vertical-align:middle;margin-right:6px"></span> Installing...`;

        try {
            await API.post('/api/ssl/upload', {
                domain_name: domain,
                certificate: certificate,
                private_key: private_key,
                chain: chain,
            });
            closeModal();
            showToast('SSL Installed', `Custom SSL certificate installed for ${domain}`, 'success');
            renderSSL();
        } catch (e) {
            showToast('SSL Error', e.message, 'error');
            btn.disabled = false;
            btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> Install Certificate`;
        }
        return;
    }

    let domain, websiteId = null;
    let autoRenew = true;

    if (isManual) {
        domain = document.getElementById('ssl-manual-domain').value.trim();
        autoRenew = document.getElementById('ssl-auto-renew-manual').checked;
    } else {
        const select = document.getElementById('ssl-website-select');
        domain = select.value;
        websiteId = select.selectedOptions[0]?.dataset?.id ? parseInt(select.selectedOptions[0].dataset.id) : null;
        autoRenew = document.getElementById('ssl-auto-renew').checked;
    }

    if (!domain) {
        showToast('Validation Error', 'Please select a website or enter a domain', 'warning');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = `<span class="spinner spinner-sm" style="display:inline-block;vertical-align:middle;margin-right:6px"></span> Issuing...`;

    try {
        await API.post('/api/ssl/issue', {
            domain_name: domain,
            website_id: websiteId,
            auto_renew: autoRenew,
        });
        closeModal();
        showToast('SSL Installed', `Let's Encrypt certificate issued for ${domain}`, 'success');
        renderSSL();
    } catch (e) {
        showToast('SSL Error', e.message, 'error');
        btn.disabled = false;
        btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> Install Certificate`;
    }
}


/* ── Certificate Details ─────────────────────────────────── */

function showCertDetails(domain) {
    const cert = _sslCerts.find(c => c.domain_name === domain);
    if (!cert) return;

    openModal(`Certificate: ${domain}`, `
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-4);font-size:var(--text-sm)">
            <div>
                <div style="color:var(--text-tertiary);font-size:11px;margin-bottom:2px">Domain</div>
                <div style="font-weight:var(--font-medium)">${cert.domain_name}</div>
            </div>
            <div>
                <div style="color:var(--text-tertiary);font-size:11px;margin-bottom:2px">Type</div>
                <div><span class="badge badge-success">${cert.cert_type}</span></div>
            </div>
            <div>
                <div style="color:var(--text-tertiary);font-size:11px;margin-bottom:2px">Status</div>
                <div><span class="badge ${cert.status === 'active' ? 'badge-success' : 'badge-danger'}">${cert.status}</span></div>
            </div>
            <div>
                <div style="color:var(--text-tertiary);font-size:11px;margin-bottom:2px">Issuer</div>
                <div style="font-weight:var(--font-medium)">${cert.issuer || 'Unknown'}</div>
            </div>
            <div>
                <div style="color:var(--text-tertiary);font-size:11px;margin-bottom:2px">Issued At</div>
                <div>${cert.issued_at ? new Date(cert.issued_at).toLocaleDateString() : '—'}</div>
            </div>
            <div>
                <div style="color:var(--text-tertiary);font-size:11px;margin-bottom:2px">Expires At</div>
                <div style="font-weight:var(--font-medium);color:${cert.status === 'active' ? '#22c55e' : 'var(--danger-400)'}">${cert.expires_at ? new Date(cert.expires_at).toLocaleDateString() : '—'}</div>
            </div>
            <div>
                <div style="color:var(--text-tertiary);font-size:11px;margin-bottom:2px">Auto Renew</div>
                <div>${cert.auto_renew ? '<span style="color:#22c55e">✓ Enabled</span>' : '<span style="color:var(--text-tertiary)">Disabled</span>'}</div>
            </div>
            <div>
                <div style="color:var(--text-tertiary);font-size:11px;margin-bottom:2px">Created</div>
                <div>${cert.created_at ? new Date(cert.created_at).toLocaleDateString() : '—'}</div>
            </div>
        </div>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">Close</button>
        <button class="btn btn-danger" onclick="closeModal(); deleteSSL(${cert.id},'${cert.domain_name}')">Remove Certificate</button>
    `);
}


/* ── Renew All ───────────────────────────────────────────── */

async function renewAllCerts() {
    confirmModal('Renew All Certificates', 'Run <code>certbot renew</code> to renew all Let\\'s Encrypt certificates that are due for renewal?', async () => {
        try {
            const res = await API.post('/api/ssl/renew');
            closeModal();
            showToast('Renewal Complete', res.message || 'Certificate renewal process completed', 'success');
            renderSSL();
        } catch (e) {
            showToast('Error', e.message, 'error');
        }
    }, 'primary');
}


/* ── Delete Certificate ──────────────────────────────────── */

async function deleteSSL(id, domain) {
    confirmModal('Remove Certificate', `Revoke and remove the SSL certificate for <strong>${domain}</strong>? The site will revert to HTTP.`, async () => {
        try {
            await API.delete(`/api/ssl/${id}`);
            showToast('Removed', `Certificate for ${domain} has been deleted`, 'success');
            renderSSL();
        } catch (e) {
            showToast('Error', e.message, 'error');
        }
    });
}
