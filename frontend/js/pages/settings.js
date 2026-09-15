/**
 * HyperPanel — Settings Page
 * Includes:
 * - Commonly Used: Network & Access (Domain, Port), Panel SSL, Authentication & Security (Panel User, Password, 2FA)
 * - System & Preferences: Appearance, Official GitHub Release Updater, About HyperPanel
 */

let _updateData = null;
let _panelSettings = null;
let _currentSetupSecret = null;

async function renderSettings() {
    const content = document.getElementById('page-content');
    const theme = localStorage.getItem('hyperpanel-theme') || 'dark';

    try {
        _panelSettings = await API.get('/api/settings/panel');
    } catch (e) {
        _panelSettings = {
            panel_port: 8443,
            panel_domain: '',
            panel_user: currentUser?.username || 'admin',
            ssl: {
                enabled: true,
                status: 'Self-signed',
                domain: '127.0.0.1',
                issuer: 'HyperPanel Authority',
                expiration_date: '—',
                days_remaining: 3650,
                total_days: 3650,
                validity_percent: 100,
            }
        };
    }

    const ssl = _panelSettings.ssl || {};

    content.innerHTML = `
        <div class="page-header">
            <div class="page-header-left">
                <h1>Settings</h1>
                <p>Panel preferences, network access, security, and updates</p>
            </div>
        </div>

        <!-- ══ SECTION: Commonly used ══ -->
        <div style="margin-bottom:var(--space-6)">
            <div style="font-size:17px;font-weight:600;margin-bottom:var(--space-4);color:var(--text-primary);letter-spacing:-0.2px">
                Commonly used
            </div>

            <div class="commonly-used-grid">
                <!-- 1. Network & Access -->
                <div class="setting-card">
                    <div class="setting-card-header">
                        <div class="setting-card-icon">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                        </div>
                        <div class="setting-card-titles">
                            <h3>Network & Access</h3>
                            <p>Configure panel network settings and access methods</p>
                        </div>
                    </div>

                    <!-- Domain -->
                    <div class="form-group" style="margin:0">
                        <label class="form-label" style="font-size:12px;color:var(--text-secondary);margin-bottom:6px">Domain - Set the domain for the panel</label>
                        <div class="setting-input-row">
                            <input type="text" class="form-input" id="setting-panel-domain" value="${_panelSettings.panel_domain || ''}" placeholder="Please enter domain, it can be empty">
                            <button class="btn-action-green" onclick="savePanelDomain()">Save</button>
                        </div>
                        <div class="setting-alert-callout">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                            <span>After setting, the panel only be accessed from this domain</span>
                        </div>
                    </div>

                    <!-- Panel Port -->
                    <div class="form-group" style="margin:0">
                        <label class="form-label" style="font-size:12px;color:var(--text-secondary);margin-bottom:6px">Panel port - Suggested port: 8888-65535</label>
                        <div class="setting-input-row">
                            <input type="text" class="form-input" id="setting-panel-port" value="${_panelSettings.panel_port}" readonly style="cursor:default">
                            <button class="btn-action-green" onclick="showModifyPortModal(${_panelSettings.panel_port})">Modify</button>
                        </div>
                        <div class="setting-alert-callout">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                            <span>If using security groups, Release new ports in security group</span>
                        </div>
                    </div>
                </div>

                <!-- 2. Panel SSL -->
                <div class="setting-card">
                    <div class="setting-card-header">
                        <div class="setting-card-icon">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                        </div>
                        <div class="setting-card-titles">
                            <h3>Panel SSL</h3>
                            <p>Configure HTTPS secure connection</p>
                        </div>
                    </div>

                    <!-- Toggle & Modify -->
                    <div style="display:flex;align-items:center;justify-content:space-between;padding:2px 0">
                        <div style="display:flex;align-items:center;gap:var(--space-3)">
                            <div style="position:relative;display:inline-block;width:38px;height:22px;cursor:pointer" onclick="togglePanelSsl(!${ssl.enabled})">
                                <div style="position:absolute;top:0;left:0;right:0;bottom:0;background-color:${ssl.enabled ? '#22c55e' : 'rgba(255,255,255,0.1)'};border:1px solid ${ssl.enabled ? '#16a34a' : 'var(--border-color)'};border-radius:22px;transition:0.2s">
                                    <div style="position:absolute;top:2px;left:${ssl.enabled ? '18px' : '2px'};width:16px;height:16px;border-radius:50%;background:#ffffff;transition:0.2s;box-shadow:0 1px 3px rgba(0,0,0,0.3)"></div>
                                </div>
                            </div>
                            <div>
                                <div style="font-size:13px;font-weight:500;color:var(--text-primary)">SSL Certificate</div>
                                <div style="font-size:11px;color:var(--text-tertiary)">HTTPS secure connection ${ssl.enabled ? 'Enabled' : 'Disabled'}</div>
                            </div>
                        </div>
                        <button class="btn-action-green" onclick="showModifySslModal()">Modify</button>
                    </div>

                    <!-- Certificate Status Box -->
                    <div class="ssl-status-box">
                        <div style="display:flex;justify-content:space-between;align-items:center">
                            <span style="font-size:13px;font-weight:600;color:var(--text-primary)">Certificate Status</span>
                            <div style="display:flex;align-items:center;gap:6px">
                                <span class="badge" style="background:${ssl.status === 'Trusted' ? 'rgba(34,197,94,0.15)' : 'rgba(234,179,8,0.15)'};color:${ssl.status === 'Trusted' ? '#22c55e' : '#eab308'};border:1px solid ${ssl.status === 'Trusted' ? 'rgba(34,197,94,0.3)' : 'rgba(234,179,8,0.3)'};font-size:11px">
                                    ${ssl.status === 'Trusted' ? '🛡️ Trusted' : '🛡️ Self-signed'}
                                </span>
                                ${_panelSettings.panel_domain && ssl.status !== 'Trusted' ? `
                                    <button class="btn btn-primary btn-sm" onclick="submitLetsEncryptPanelSsl()" style="font-size:11px;padding:3px 8px;height:auto">
                                        🔒 Issue Let's Encrypt
                                    </button>
                                ` : ''}
                            </div>
                        </div>

                        <div>
                            <div style="display:flex;justify-content:space-between;font-size:12px;color:var(--text-secondary);margin-bottom:4px">
                                <span>Validity Period</span>
                                <span style="font-weight:500">${ssl.days_remaining || 0}/${ssl.total_days || 365} Day(s)</span>
                            </div>
                            <div class="ssl-progress-bar-bg">
                                <div class="ssl-progress-bar-fill" style="width:${ssl.validity_percent || 100}%"></div>
                            </div>
                        </div>

                        <div class="ssl-meta-grid">
                            <div>
                                <div style="color:var(--text-tertiary);font-size:11px">Domain</div>
                                <div style="font-weight:500;color:var(--text-primary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${ssl.domain}">${ssl.domain || '127.0.0.1'}</div>
                            </div>
                            <div>
                                <div style="color:var(--text-tertiary);font-size:11px">Issuer</div>
                                <div style="font-weight:500;color:var(--text-primary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${ssl.issuer}">${ssl.issuer || 'HyperPanel CA'}</div>
                            </div>
                            <div>
                                <div style="color:var(--text-tertiary);font-size:11px">Expiration Date</div>
                                <div style="font-weight:500;color:var(--text-primary)">${ssl.expiration_date || '—'}</div>
                            </div>
                            <div>
                                <div style="color:var(--text-tertiary);font-size:11px">Days Remaining</div>
                                <div style="font-weight:600;color:#22c55e">${ssl.days_remaining || 0} Day(s)</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 3. Authentication & Security -->
                <div class="setting-card">
                    <div class="setting-card-header">
                        <div class="setting-card-icon">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                        </div>
                        <div class="setting-card-titles">
                            <h3>Authentication & Security</h3>
                            <p>Manage panel login and security settings</p>
                        </div>
                    </div>

                    <!-- Panel User -->
                    <div class="form-group" style="margin:0">
                        <label class="form-label" style="font-size:12px;color:var(--text-secondary);margin-bottom:6px">Panel user - Set up panel user</label>
                        <div class="setting-input-row">
                            <input type="text" class="form-input" id="setting-panel-user" value="${currentUser?.username || 'admin'}" readonly style="cursor:default">
                            <button class="btn-action-green" onclick="showModifyUserModal('${currentUser?.username || 'admin'}')">Modify</button>
                        </div>
                    </div>

                    <!-- Panel Password -->
                    <div class="form-group" style="margin:0">
                        <label class="form-label" style="font-size:12px;color:var(--text-secondary);margin-bottom:6px">Panel password - Set up panel password</label>
                        <div class="setting-input-row">
                            <input type="password" class="form-input" value="••••••••••••" readonly style="cursor:default">
                            <button class="btn-action-green" onclick="showModifyPasswordModal()">Modify</button>
                        </div>
                    </div>

                    <!-- Two-Factor Authentication -->
                    <div style="border-top:1px solid var(--border-color);padding-top:var(--space-3);display:flex;align-items:center;justify-content:space-between">
                        <div>
                            <div style="font-size:12px;font-weight:500;color:var(--text-primary);display:flex;align-items:center;gap:6px">
                                2FA Authentication (TOTP)
                                <span class="badge ${currentUser?.totp_enabled ? 'badge-success' : 'badge-neutral'}" style="font-size:10px">
                                    ${currentUser?.totp_enabled ? 'Active' : 'Disabled'}
                                </span>
                            </div>
                            <div style="font-size:11px;color:var(--text-tertiary)">Google Authenticator / Authy</div>
                        </div>
                        ${currentUser?.totp_enabled ? `
                            <button class="btn btn-ghost btn-sm" onclick="showDisable2FaModal()" style="color:var(--danger-400)">Disable</button>
                        ` : `
                            <button class="btn btn-ghost btn-sm" onclick="showEnable2FaModal()" style="color:var(--primary-400)">Configure</button>
                        `}
                    </div>
                </div>
            </div>
        </div>

        <!-- ══ SECTION: System & Preferences ══ -->
        <div style="margin-bottom:var(--space-4)">
            <div style="font-size:17px;font-weight:600;margin-bottom:var(--space-4);color:var(--text-primary);letter-spacing:-0.2px">
                System & Preferences
            </div>

            <div class="grid grid-2" style="gap:var(--space-5)">
                <!-- Appearance -->
                <div class="card">
                    <div class="card-header"><h3>Appearance</h3></div>
                    <div class="card-body">
                        <div class="form-group" style="margin:0">
                            <label class="form-label">Theme</label>
                            <select class="form-input" id="settings-theme" onchange="changeTheme(this.value)">
                                <option value="dark" ${theme === 'dark' ? 'selected' : ''}>Dark Mode</option>
                                <option value="light" ${theme === 'light' ? 'selected' : ''}>Light Mode</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Panel Updates (Official GitHub Releases) -->
                <div class="card" style="border:1px solid var(--border-color)">
                    <div class="card-header" style="display:flex;justify-content:space-between;align-items:center">
                        <div style="display:flex;align-items:center;gap:var(--space-2)">
                            <h3>System Updates</h3>
                            <span class="badge badge-secondary" id="panel-version-badge">v1.0.0</span>
                        </div>
                        <button class="btn btn-ghost btn-sm" id="check-updates-btn" onclick="checkForUpdates()">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15"/></svg>
                            Check for Updates
                        </button>
                    </div>
                    <div class="card-body" id="update-status-container">
                        <div style="font-size:var(--text-xs);color:var(--text-secondary);line-height:1.5">
                            Updates are based on <strong>official GitHub releases</strong> to ensure system stability. Test commits or work-in-progress code on the repository are excluded.
                        </div>
                        <div id="update-details-box" style="margin-top:var(--space-4)"></div>
                    </div>
                </div>

                <!-- About HyperPanel -->
                <div class="card" style="grid-column: 1 / -1">
                    <div class="card-header"><h3>About HyperPanel</h3></div>
                    <div class="card-body">
                        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(180px, 1fr));gap:var(--space-4)">
                            <div><span style="font-size:var(--text-xs);color:var(--text-tertiary)">Version</span><div style="font-weight:var(--font-medium)">v1.0.0 (Release-Tracked)</div></div>
                            <div><span style="font-size:var(--text-xs);color:var(--text-tertiary)">Repository</span><div><a href="https://github.com/ibrahimarchive/hyperpanel" target="_blank" style="color:var(--primary-400);font-size:var(--text-sm)">github.com/ibrahimarchive/hyperpanel</a></div></div>
                            <div><span style="font-size:var(--text-xs);color:var(--text-tertiary)">License</span><div style="font-weight:var(--font-medium)">GNU General Public License v3.0</div></div>
                            <div><span style="font-size:var(--text-xs);color:var(--text-tertiary)">Architecture</span><div style="font-weight:var(--font-medium)">Modular & Lightweight SPA</div></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Automatically check for updates on settings render
    checkForUpdates(true);
}

/* ── Network & Access Handlers ─────────────────────────────── */

async function savePanelDomain() {
    const domainInput = document.getElementById('setting-panel-domain');
    const domain = domainInput ? domainInput.value.trim() : '';
    const btn = document.querySelector("button[onclick='savePanelDomain()']");
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner spinner-sm" style="display:inline-block;vertical-align:middle;margin-right:4px"></span> Saving...`;
    }

    try {
        const res = await API.post('/api/settings/panel/domain', { domain });
        showToast('Domain & SSL Updated', res.message || 'Panel domain saved', res.letsencrypt_issued ? 'success' : 'info');
        renderSettings();
    } catch (e) {
        showToast('Error', e.message, 'error');
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Save';
        }
    }
}

function showModifyPortModal(currentPort) {
    openModal('Modify Panel Port', `
        <p style="font-size:var(--text-sm);color:var(--text-secondary);margin-bottom:var(--space-4);line-height:1.5">
            Set a custom listening port for the control panel (recommended: 8888-65535).
        </p>
        <div class="form-group">
            <label class="form-label">Panel Port</label>
            <input type="number" class="form-input" id="modal-panel-port" value="${currentPort}" min="1024" max="65535" required>
        </div>
        <div class="setting-alert-callout" style="margin-top:var(--space-3)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <span><strong>Critical:</strong> If you are using cloud security groups (AWS, GCP, DigitalOcean, Hetzner, etc.), release the new port in your security group before changing to avoid getting locked out.</span>
        </div>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button class="btn btn-primary" id="btn-save-port" onclick="submitModifyPort()">Save & Apply</button>
    `);
}

async function submitModifyPort() {
    const port = parseInt(document.getElementById('modal-panel-port').value, 10);
    if (!port || port < 1024 || port > 65535) {
        showToast('Validation Error', 'Port must be between 1024 and 65535', 'warning');
        return;
    }

    const btn = document.getElementById('btn-save-port');
    btn.disabled = true;
    btn.textContent = 'Updating...';

    try {
        const res = await API.post('/api/settings/panel/port', { port });
        closeModal();
        showToast('Port Updated', res.message || `Panel port changed to ${port}`, 'success');
        renderSettings();
    } catch (e) {
        showToast('Error', e.message, 'error');
        btn.disabled = false;
        btn.textContent = 'Save & Apply';
    }
}

/* ── Panel SSL Handlers ─────────────────────────────────────── */

async function togglePanelSsl(enabled) {
    try {
        const res = await API.post('/api/settings/panel/ssl/toggle', { enabled });
        showToast('SSL Updated', `Panel HTTPS is now ${enabled ? 'Enabled' : 'Disabled'}`, 'success');
        renderSettings();
    } catch (e) {
        showToast('Error', e.message, 'error');
    }
}

function showModifySslModal() {
    const domain = _panelSettings.panel_domain || '';

    openModal('Configure Panel SSL', `
        <div class="tabs" style="margin-bottom:var(--space-4)">
            <div class="tab active" onclick="showSslTab('letsencrypt', this)">Let's Encrypt SSL</div>
            <div class="tab" onclick="showSslTab('custom', this)">Custom PEM Certificate</div>
        </div>

        <!-- 1. Let's Encrypt Tab -->
        <div id="tab-ssl-letsencrypt">
            ${domain ? `
                <p style="font-size:var(--text-sm);color:var(--text-secondary);margin-bottom:var(--space-3);line-height:1.5">
                    Issue an official, browser-trusted <strong>Let's Encrypt</strong> SSL certificate for your panel domain <code>${domain}</code>.
                </p>

                <div class="form-group">
                    <label class="form-label">Panel Domain</label>
                    <input type="text" class="form-input" value="${domain}" readonly style="cursor:default;background:rgba(255,255,255,0.04)">
                </div>

                <div class="form-group">
                    <label class="form-label">Email for Certificate Expiry Notifications (Optional)</label>
                    <input type="email" class="form-input" id="panel-le-email" placeholder="admin@${domain}">
                </div>

                <div class="setting-alert-callout" style="margin-bottom:var(--space-4)">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                    <span>DNS A-Record for <strong>${domain}</strong> must point to this server's public IP address before issuing.</span>
                </div>

                <button class="btn btn-primary" id="btn-issue-panel-le" onclick="submitLetsEncryptPanelSsl()">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                    Issue Let's Encrypt Certificate
                </button>
            ` : `
                <div class="setting-alert-callout" style="margin-bottom:var(--space-4)">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                    <span><strong>Panel Domain Required:</strong> You must configure a panel domain (e.g. <code>panel.yourdomain.com</code>) under Network & Access settings before Let's Encrypt can issue a certificate.</span>
                </div>

                <div class="form-group">
                    <label class="form-label">Set Panel Domain Now</label>
                    <div class="setting-input-row">
                        <input type="text" class="form-input" id="quick-panel-domain" placeholder="panel.example.com">
                        <button class="btn btn-primary" onclick="saveQuickPanelDomain()">Save Domain</button>
                    </div>
                </div>
            `}
        </div>

        <!-- 2. Custom PEM Tab -->
        <div id="tab-ssl-custom" style="display:none">
            <p style="font-size:var(--text-xs);color:var(--text-secondary);margin-bottom:var(--space-3)">
                Paste your custom SSL Certificate (CRT/PEM) and Private Key (KEY/PEM) to use trusted enterprise certificates:
            </p>
            <div class="form-group">
                <label class="form-label">Certificate (PEM / CRT)</label>
                <textarea class="form-input" id="custom-ssl-crt" rows="5" placeholder="-----BEGIN CERTIFICATE-----&#10;...&#10;-----END CERTIFICATE-----" style="font-family:monospace;font-size:11px"></textarea>
            </div>
            <div class="form-group">
                <label class="form-label">Private Key (KEY)</label>
                <textarea class="form-input" id="custom-ssl-key" rows="5" placeholder="-----BEGIN PRIVATE KEY-----&#10;...&#10;-----END PRIVATE KEY-----" style="font-family:monospace;font-size:11px"></textarea>
            </div>
            <button class="btn btn-primary" onclick="submitCustomSsl()">
                Save & Apply Custom Certificate
            </button>
        </div>
    `, `<button class="btn btn-secondary" onclick="closeModal()">Close</button>`);
}

function showSslTab(tab, el) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('tab-ssl-letsencrypt').style.display = tab === 'letsencrypt' ? 'block' : 'none';
    document.getElementById('tab-ssl-custom').style.display = tab === 'custom' ? 'block' : 'none';
}

async function submitLetsEncryptPanelSsl() {
    const email = document.getElementById('panel-le-email')?.value?.trim() || '';
    const btn = document.getElementById('btn-issue-panel-le');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner spinner-sm" style="display:inline-block;vertical-align:middle;margin-right:6px"></span> Issuing Let's Encrypt SSL...`;
    }

    try {
        const res = await API.post('/api/settings/panel/ssl/letsencrypt', { email });
        closeModal();
        showToast('SSL Issued', res.message || "Let's Encrypt certificate installed for panel domain", 'success');
        renderSettings();
    } catch (e) {
        showToast('SSL Error', e.message, 'error');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> Issue Let's Encrypt Certificate`;
        }
    }
}

async function saveQuickPanelDomain() {
    const domain = document.getElementById('quick-panel-domain')?.value?.trim() || '';
    if (!domain) {
        showToast('Validation Error', 'Please enter a valid panel domain name', 'warning');
        return;
    }
    try {
        await API.post('/api/settings/panel/domain', { domain });
        showToast('Domain Saved', `Panel domain set to ${domain}`, 'success');
        _panelSettings.panel_domain = domain;
        showModifySslModal(); // refresh modal state
    } catch (e) {
        showToast('Error', e.message, 'error');
    }
}

async function submitSelfSignedSsl() {
    try {
        const res = await API.post('/api/settings/panel/ssl/self-signed');
        closeModal();
        showToast('Certificate Generated', '10-Year SSL certificate created and applied', 'success');
        renderSettings();
    } catch (e) {
        showToast('Error', e.message, 'error');
    }
}

async function submitCustomSsl() {
    const certificate = document.getElementById('custom-ssl-crt').value.trim();
    const private_key = document.getElementById('custom-ssl-key').value.trim();

    if (!certificate || !private_key) {
        showToast('Validation Error', 'Both Certificate and Private Key are required', 'warning');
        return;
    }

    try {
        const res = await API.post('/api/settings/panel/ssl/custom', { certificate, private_key });
        closeModal();
        showToast('SSL Applied', res.message || 'Custom SSL certificate installed successfully', 'success');
        renderSettings();
    } catch (e) {
        showToast('SSL Error', e.message, 'error');
    }
}

/* ── Authentication & Security Handlers ─────────────────────── */

function showModifyUserModal(currentUsername) {
    openModal('Modify Panel User', `
        <div class="form-group">
            <label class="form-label">New Username</label>
            <input type="text" class="form-input" id="modal-panel-newuser" value="${currentUsername}" placeholder="Enter new username" required>
        </div>
        <div class="form-group">
            <label class="form-label">Current Password (to verify authorization)</label>
            <input type="password" class="form-input" id="modal-panel-userpass" placeholder="Enter your current password" required>
        </div>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button class="btn btn-primary" onclick="submitModifyUser()">Update Username</button>
    `);
}

async function submitModifyUser() {
    const username = document.getElementById('modal-panel-newuser').value.trim();
    const password = document.getElementById('modal-panel-userpass').value;

    if (!username || username.length < 3) {
        showToast('Validation Error', 'Username must be at least 3 characters', 'warning');
        return;
    }
    if (!password) {
        showToast('Validation Error', 'Current password is required to change username', 'warning');
        return;
    }

    try {
        const res = await API.post('/api/settings/panel/username', { username, password });
        closeModal();
        showToast('Username Updated', res.message || 'Username changed successfully', 'success');
        if (window.currentUser) {
            window.currentUser.username = username;
            document.getElementById('user-display-name').textContent = username;
        }
        renderSettings();
    } catch (e) {
        showToast('Error', e.message, 'error');
    }
}

function showModifyPasswordModal() {
    openModal('Change Panel Password', `
        <div class="form-group">
            <label class="form-label">Current Password</label>
            <input type="password" class="form-input" id="modal-current-pass" placeholder="Enter current password" required>
        </div>
        <div class="form-group">
            <label class="form-label">New Password</label>
            <input type="password" class="form-input" id="modal-new-pass" placeholder="Enter strong new password" required>
        </div>
        <div class="form-group">
            <label class="form-label">Confirm New Password</label>
            <input type="password" class="form-input" id="modal-confirm-pass" placeholder="Repeat new password" required>
        </div>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button class="btn btn-primary" onclick="submitModifyPassword()">Change Password</button>
    `);
}

async function submitModifyPassword() {
    const current_password = document.getElementById('modal-current-pass').value;
    const new_password = document.getElementById('modal-new-pass').value;
    const confirm_password = document.getElementById('modal-confirm-pass').value;

    if (!current_password || !new_password) {
        showToast('Validation Error', 'All fields are required', 'warning');
        return;
    }
    if (new_password !== confirm_password) {
        showToast('Validation Error', 'New passwords do not match', 'warning');
        return;
    }

    try {
        await API.post('/api/users/change-password', {
            current_password: current_password,
            new_password: new_password,
        });
        closeModal();
        showToast('Password Changed', 'Panel password successfully updated', 'success');
    } catch (e) {
        showToast('Error', e.message, 'error');
    }
}

/* ── 2FA Modal Handlers ─────────────────────────────────────── */

async function showEnable2FaModal() {
    try {
        const data = await API.post('/api/auth/2fa/setup');
        _currentSetupSecret = data.secret;

        const qrImgHtml = data.qr_code && data.qr_code.startsWith('data:image')
            ? `<img src="${data.qr_code}" alt="QR Code" style="width:180px;height:180px;border-radius:var(--radius-md);border:1px solid var(--border-color);margin:0 auto var(--space-3) auto;display:block">`
            : `<div style="padding:var(--space-3);background:var(--bg-secondary);border-radius:var(--radius-md);margin-bottom:var(--space-3)"><p style="font-size:var(--text-xs);word-break:break-all">URI: ${data.provisioning_uri}</p></div>`;

        openModal('Set Up Two-Factor Authentication', `
            <div style="text-align:center">
                <p style="font-size:var(--text-sm);color:var(--text-secondary);margin-bottom:var(--space-3)">
                    Scan this QR code with Google Authenticator, Microsoft Authenticator, or Authy:
                </p>
                ${qrImgHtml}
                <div style="background:var(--bg-secondary);padding:var(--space-2) var(--space-3);border-radius:var(--radius-sm);font-size:var(--text-xs);display:inline-block;margin-bottom:var(--space-4);border:1px solid var(--border-color)">
                    Manual Secret: <code style="letter-spacing:1px;font-weight:bold">${data.secret}</code>
                </div>
            </div>
            <div class="form-group">
                <label class="form-label" style="text-align:center">Enter 6-digit confirmation code from app</label>
                <input type="text" class="form-input" id="setup-totp-code" placeholder="123456" maxlength="6" inputmode="numeric" style="text-align:center;letter-spacing:4px;font-size:var(--text-lg);font-weight:bold" autocomplete="off">
            </div>
        `, `
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn btn-primary" id="btn-confirm-2fa" onclick="confirmEnable2Fa()">Confirm & Enable</button>
        `);
    } catch (e) {
        showToast('Error', e.message, 'error');
    }
}

async function confirmEnable2Fa() {
    const code = document.getElementById('setup-totp-code').value.trim();
    if (!code || code.length !== 6) {
        showToast('Error', 'Please enter a valid 6-digit verification code', 'warning');
        return;
    }
    const btn = document.getElementById('btn-confirm-2fa');
    btn.disabled = true;
    btn.textContent = 'Enabling...';

    try {
        await API.post('/api/auth/2fa/enable', {
            secret: _currentSetupSecret,
            code: code,
        });
        closeModal();
        showToast('2FA Enabled', 'Two-Factor Authentication is now active on your account', 'success');
        const user = await API.get('/api/auth/me');
        window.currentUser = user;
        renderSettings();
    } catch (e) {
        showToast('Verification Failed', e.message, 'error');
        btn.disabled = false;
        btn.textContent = 'Confirm & Enable';
    }
}

function showDisable2FaModal() {
    openModal('Disable Two-Factor Authentication', `
        <p style="font-size:var(--text-sm);color:var(--text-secondary);margin-bottom:var(--space-4)">
            Are you sure you want to disable 2FA? This will reduce the security level of your server control panel.
        </p>
        <div class="form-group">
            <label class="form-label">Enter 6-digit Authenticator Code or Account Password</label>
            <input type="password" class="form-input" id="disable-2fa-input" placeholder="Current Code or Password" autocomplete="off">
        </div>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button class="btn btn-danger" id="btn-do-disable-2fa" onclick="doDisable2Fa()">Disable 2FA</button>
    `);
}

async function doDisable2Fa() {
    const val = document.getElementById('disable-2fa-input').value.trim();
    if (!val) {
        showToast('Error', 'Please enter your verification code or password', 'warning');
        return;
    }
    const btn = document.getElementById('btn-do-disable-2fa');
    btn.disabled = true;

    try {
        const payload = /^\d{6}$/.test(val) ? { code: val } : { password: val };
        await API.post('/api/auth/2fa/disable', payload);
        closeModal();
        showToast('2FA Disabled', 'Two-Factor Authentication has been removed', 'info');
        const user = await API.get('/api/auth/me');
        window.currentUser = user;
        renderSettings();
    } catch (e) {
        showToast('Error', e.message, 'error');
        btn.disabled = false;
    }
}

/* ── Appearance Handlers ────────────────────────────────────── */

function changeTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('hyperpanel-theme', theme);
    updateThemeIcons(theme);
}

function updateThemeIcons(theme) {
    const sun = document.getElementById('theme-icon-sun');
    const moon = document.getElementById('theme-icon-moon');
    if (sun && moon) {
        sun.style.display = theme === 'dark' ? 'block' : 'none';
        moon.style.display = theme === 'dark' ? 'none' : 'block';
    }
}

/* ── System Updates Handlers ────────────────────────────────── */

async function checkForUpdates(silent = false) {
    const btn = document.getElementById('check-updates-btn');
    const detailsBox = document.getElementById('update-details-box');
    const versionBadge = document.getElementById('panel-version-badge');

    if (!detailsBox) return;

    if (!silent && btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner spinner-sm" style="display:inline-block;vertical-align:middle;margin-right:4px"></span> Checking...`;
    }

    try {
        const data = await API.get('/api/updates/check');
        _updateData = data;

        if (versionBadge) {
            versionBadge.textContent = data.current_version;
        }

        if (data.update_available || data.has_update) {
            detailsBox.innerHTML = `
                <div style="background:var(--bg-tertiary);border:1px solid var(--primary-500);border-radius:var(--radius-md);padding:var(--space-4)">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-2)">
                        <div style="font-weight:var(--font-semibold);color:var(--primary-400);font-size:var(--text-sm)">
                            🎉 New Release Available: ${data.latest_version || data.tag_name}
                        </div>
                        <span class="badge badge-success">Official Release</span>
                    </div>
                    <div style="font-size:var(--text-xs);color:var(--text-secondary);margin-bottom:var(--space-3);white-space:pre-line;max-height:120px;overflow-y:auto">
                        ${data.release_notes || 'Official update is ready for installation.'}
                    </div>
                    <div style="display:flex;gap:var(--space-3);align-items:center">
                        <button class="btn btn-primary btn-sm" onclick="triggerUpdate('${data.latest_version}')">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
                            Update to ${data.latest_version}
                        </button>
                        ${data.release_url ? `
                            <a href="${data.release_url}" target="_blank" class="btn btn-ghost btn-sm" style="text-decoration:none">
                                View Release Notes
                            </a>
                        ` : ''}
                    </div>
                </div>`;
        } else {
            detailsBox.innerHTML = `
                <div style="display:flex;align-items:center;gap:var(--space-2);color:var(--success-400);font-size:var(--text-xs);background:var(--bg-tertiary);padding:var(--space-3);border-radius:var(--radius-md)">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                    <span>HyperPanel is up to date (${data.current_version}). Tracking official releases.</span>
                </div>`;
        }
    } catch (e) {
        detailsBox.innerHTML = `
            <div style="color:var(--danger-400);font-size:var(--text-xs)">
                Failed to check for updates: ${e.message}
            </div>`;
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15"/></svg> Check for Updates`;
        }
    }
}

async function triggerUpdate(version) {
    confirmModal(
        `Install Update ${version}`,
        `Are you sure you want to update HyperPanel to official release <strong>${version}</strong>?<br><br>
         The update script will execute cleanly in the background. The panel may briefly disconnect for a few seconds while restarting.`,
        async () => {
            try {
                openModal('Updating HyperPanel', `
                    <div style="text-align:center;padding:var(--space-5)">
                        <div class="spinner spinner-lg" style="margin:0 auto var(--space-4) auto"></div>
                        <h3>Applying Update ${version}...</h3>
                        <p style="color:var(--text-secondary);font-size:var(--text-xs);margin-top:var(--space-2)" id="update-poll-status">
                            Downloading official release and updating dependencies. Please do not close this window.
                        </p>
                    </div>
                `, '');

                const res = await API.post('/api/updates/trigger', { version });

                let attempts = 0;
                const maxAttempts = 40;
                const pollInterval = setInterval(async () => {
                    attempts++;
                    const statusEl = document.getElementById('update-poll-status');
                    if (statusEl) {
                        statusEl.textContent = `Waiting for panel service restart (attempt ${attempts}/${maxAttempts})...`;
                    }

                    try {
                        const res = await fetch('/api/health?t=' + Date.now());
                        if (res.ok) {
                            clearInterval(pollInterval);
                            if (statusEl) statusEl.textContent = 'Update applied successfully! Refreshing...';
                            setTimeout(() => {
                                window.location.reload(true);
                            }, 1200);
                        }
                    } catch (err) {
                        // Restarting
                    }

                    if (attempts >= maxAttempts) {
                        clearInterval(pollInterval);
                        if (statusEl) {
                            statusEl.innerHTML = `<span style="color:var(--warning-400)">Update script was executed. If the panel does not reload automatically, please refresh the page manually.</span>`;
                        }
                    }
                }, 2000);

            } catch (e) {
                closeModal();
                showToast('Update Failed', e.message, 'error');
            }
        },
        'primary'
    );
}
