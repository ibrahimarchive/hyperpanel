/**
 * HyperPanel — Email Management Page (BillionMail)
 * Modular, on-demand mail server and marketing suite.
 */

async function renderEmail() {
    const content = document.getElementById('page-content');
    content.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:center;height:50vh;">
            <div class="spinner spinner-lg"></div>
        </div>
    `;

    try {
        const status = await API.get('/api/email/status');

        if (!status.installed) {
            renderEmailUninstalled(content, status);
            return;
        }

        renderEmailInstalled(content, status);
    } catch (e) {
        content.innerHTML = `
            <div class="page-header">
                <div class="page-header-left">
                    <h1>Mail Server</h1>
                    <p>BillionMail Email & Marketing Suite</p>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <div class="empty-state">
                        <div class="empty-state-icon">⚠️</div>
                        <h3>Unable to load email status</h3>
                        <p style="color:var(--text-tertiary)">${e.message}</p>
                        <button class="btn btn-primary" onclick="renderEmail()" style="margin-top:var(--space-3)">Retry</button>
                    </div>
                </div>
            </div>
        `;
    }
}

function renderEmailUninstalled(content, status) {
    const hasDocker = !!status.docker_installed;

    content.innerHTML = `
        <div class="page-header">
            <div class="page-header-left">
                <h1>Mail Server</h1>
                <p>Enterprise self-hosted email infrastructure & marketing suite</p>
            </div>
            <div class="page-header-actions">
                <span class="badge badge-secondary">Optional Module</span>
            </div>
        </div>

        <div class="card" style="margin-bottom:var(--space-5);border:1px solid var(--border-color);background:linear-gradient(180deg, rgba(37,99,235,0.04) 0%, transparent 100%)">
            <div class="card-body" style="padding:var(--space-8);text-align:center">
                <div style="width:64px;height:64px;border-radius:var(--radius-xl);background:rgba(59,130,246,0.15);display:inline-flex;align-items:center;justify-content:center;margin-bottom:var(--space-4);color:var(--primary-400)">
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                        <polyline points="22,6 12,13 2,6"/>
                    </svg>
                </div>
                <h2 style="font-size:var(--text-2xl);margin-bottom:var(--space-2)">BillionMail Not Installed</h2>
                <p style="color:var(--text-tertiary);max-width:560px;margin:0 auto var(--space-5);font-size:var(--text-sm);line-height:1.6">
                    HyperPanel keeps your server lightweight by keeping the mail daemon optional. Install <strong>BillionMail</strong> to get a full-stack open-source email server with SMTP, IMAP, POP3, integrated RoundCube Webmail, and email marketing campaigns.
                </p>

                ${!hasDocker ? `
                    <div style="display:inline-flex;align-items:center;gap:var(--space-3);padding:var(--space-3) var(--space-4);border-radius:var(--radius-md);background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.25);margin-bottom:var(--space-5);text-align:left">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                        <div>
                            <div style="font-weight:var(--font-medium);font-size:var(--text-sm);color:#f59e0b">Docker is required</div>
                            <div style="font-size:var(--text-xs);color:var(--text-secondary)">BillionMail runs in high-performance containers. Please install Docker first.</div>
                        </div>
                        <button class="btn btn-secondary btn-sm" onclick="window.location.hash='#/docker'" style="margin-left:var(--space-2)">Install Docker</button>
                    </div>
                ` : `
                    <div style="display:inline-flex;align-items:center;gap:var(--space-2);padding:var(--space-2) var(--space-3);border-radius:var(--radius-full);background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.25);margin-bottom:var(--space-5);color:var(--success-400);font-size:var(--text-xs);font-weight:var(--font-medium)">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>
                        Prerequisite Met: Docker Engine is active
                    </div>
                `}

                <div>
                    <button class="btn btn-primary" id="install-email-btn" onclick="installEmail()" ${!hasDocker ? 'disabled title="Please install Docker first"' : ''} style="padding:var(--space-3) var(--space-6);font-size:var(--text-base)">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
                        Install BillionMail Mail Server
                    </button>
                </div>
                <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:var(--space-3)">
                    Clones aaPanel/BillionMail and boots Postfix, Dovecot, Rspamd & Webmail containers.
                </div>
            </div>
        </div>

        <div class="grid grid-3" style="gap:var(--space-4)">
            <div class="card">
                <div class="card-body">
                    <div style="font-size:24px;margin-bottom:var(--space-2)">📬</div>
                    <div style="font-weight:var(--font-semibold);margin-bottom:var(--space-1)">Complete Mail Stack</div>
                    <div style="font-size:var(--text-xs);color:var(--text-secondary);line-height:1.5">
                        Postfix for lightning-fast SMTP transfer, Dovecot for IMAP/POP3 mailbox storage, and Rspamd for spam filtering.
                    </div>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <div style="font-size:24px;margin-bottom:var(--space-2)">🌐</div>
                    <div style="font-weight:var(--font-semibold);margin-bottom:var(--space-1)">Integrated Webmail</div>
                    <div style="font-size:var(--text-xs);color:var(--text-secondary);line-height:1.5">
                        Access emails securely anywhere via webmail (RoundCube) with address book, identities, and rich composer.
                    </div>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <div style="font-size:24px;margin-bottom:var(--space-2)">🚀</div>
                    <div style="font-weight:var(--font-semibold);margin-bottom:var(--space-1)">Campaigns & Marketing</div>
                    <div style="font-size:var(--text-xs);color:var(--text-secondary);line-height:1.5">
                        Native support for subscriber list management, mass email dispatching, open rate analytics, and zero fees.
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderEmailInstalled(content, status) {
    const isRunning = !!status.running;
    const webUrl = status.url || 'http://' + window.location.hostname + ':8080';

    content.innerHTML = `
        <div class="page-header">
            <div class="page-header-left">
                <h1>Mail Server</h1>
                <p>BillionMail Server & Marketing Platform</p>
            </div>
            <div class="page-header-actions">
                <a href="${webUrl}" target="_blank" class="btn btn-primary">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3"/></svg>
                    Open BillionMail Portal
                </a>
                <button class="btn btn-secondary" onclick="showEmailCredentials()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
                    Credentials
                </button>
            </div>
        </div>

        <!-- Hero Status Card -->
        <div class="card" style="margin-bottom:var(--space-5)">
            <div class="card-body" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:var(--space-4)">
                <div style="display:flex;align-items:center;gap:var(--space-4)">
                    <div style="width:48px;height:48px;border-radius:var(--radius-lg);background:rgba(59,130,246,0.12);display:flex;align-items:center;justify-content:center;color:var(--primary-400)">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                    </div>
                    <div>
                        <div style="display:flex;align-items:center;gap:var(--space-2)">
                            <h3 style="margin:0;font-size:var(--text-lg)">BillionMail Core Services</h3>
                            <span class="badge ${isRunning ? 'badge-success' : 'badge-danger'}">
                                ${isRunning ? '● Running' : '● Stopped'}
                            </span>
                        </div>
                        <div style="font-size:var(--text-xs);color:var(--text-secondary);margin-top:2px">
                            Installed at <code style="font-size:11px">${status.directory}</code> • Web UI on Port <strong>8080</strong>
                        </div>
                    </div>
                </div>

                <div style="display:flex;align-items:center;gap:var(--space-2)">
                    ${isRunning ? `
                        <button class="btn btn-secondary btn-sm" onclick="controlEmail('restart')" title="Restart Containers">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15"/></svg>
                            Restart
                        </button>
                        <button class="btn btn-secondary btn-sm" onclick="controlEmail('stop')" style="color:var(--warning-400)" title="Stop Containers">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
                            Stop
                        </button>
                    ` : `
                        <button class="btn btn-primary btn-sm" onclick="controlEmail('start')" title="Start Containers">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                            Start
                        </button>
                    `}
                    <button class="btn btn-ghost btn-sm" onclick="uninstallEmail()" style="color:var(--danger-400)" title="Uninstall BillionMail">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                        Uninstall
                    </button>
                </div>
            </div>
        </div>

        <!-- Protocol Ports & Connection Details -->
        <div class="grid grid-2" style="gap:var(--space-5);margin-bottom:var(--space-5)">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Mail Protocol Ports</h3>
                    <span class="badge badge-secondary">Active Listeners</span>
                </div>
                <div class="table-wrapper">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Service</th>
                                <th>Port</th>
                                <th>Protocol / Security</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="font-weight:var(--font-medium)">SMTP Outbound/Inbound</td>
                                <td><code>25</code></td>
                                <td><span class="badge badge-warning">Plain / STARTTLS</span></td>
                            </tr>
                            <tr>
                                <td style="font-weight:var(--font-medium)">SMTP Submission</td>
                                <td><code>587</code></td>
                                <td><span class="badge badge-success">STARTTLS (Encrypted)</span></td>
                            </tr>
                            <tr>
                                <td style="font-weight:var(--font-medium)">SMTPS Secure</td>
                                <td><code>465</code></td>
                                <td><span class="badge badge-success">SSL / TLS Direct</span></td>
                            </tr>
                            <tr>
                                <td style="font-weight:var(--font-medium)">IMAPS Mailbox</td>
                                <td><code>993</code></td>
                                <td><span class="badge badge-success">SSL / TLS Direct</span></td>
                            </tr>
                            <tr>
                                <td style="font-weight:var(--font-medium)">POP3S Mailbox</td>
                                <td><code>995</code></td>
                                <td><span class="badge badge-success">SSL / TLS Direct</span></td>
                            </tr>
                            <tr>
                                <td style="font-weight:var(--font-medium)">Web Portal / Admin</td>
                                <td><code>8080</code></td>
                                <td><span class="badge badge-primary">HTTP / Webmail</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div class="card-footer" style="font-size:var(--text-xs);color:var(--text-tertiary)">
                    💡 <strong>Note on Port 25:</strong> Many VPS providers (Hetzner, Linode, AWS, DigitalOcean) block outbound port 25 by default to prevent spam. Open a ticket with your VPS provider if you cannot send external mail.
                </div>
            </div>

            <!-- DNS Guidance Card -->
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Required DNS Records</h3>
                    <button class="btn btn-ghost btn-sm" onclick="window.location.hash='#/dns'">Open DNS Manager</button>
                </div>
                <div class="card-body" style="font-size:var(--text-xs);line-height:1.6;color:var(--text-secondary)">
                    <p style="margin-bottom:var(--space-3)">
                        To ensure high inbox delivery and avoid spam folders, add these records to your domain's DNS:
                    </p>
                    <div style="background:var(--bg-primary);padding:var(--space-3);border-radius:var(--radius-md);margin-bottom:var(--space-3);border:1px solid var(--border-color)">
                        <div style="font-weight:var(--font-medium);color:var(--text-primary);margin-bottom:2px">1. MX Record (Mail Exchanger)</div>
                        <code>Type: MX | Host: @ | Value: mail.yourdomain.com | Priority: 10</code>
                    </div>
                    <div style="background:var(--bg-primary);padding:var(--space-3);border-radius:var(--radius-md);margin-bottom:var(--space-3);border:1px solid var(--border-color)">
                        <div style="font-weight:var(--font-medium);color:var(--text-primary);margin-bottom:2px">2. SPF Record (Sender Policy Framework)</div>
                        <code>Type: TXT | Host: @ | Value: "v=spf1 mx ~all"</code>
                    </div>
                    <div style="background:var(--bg-primary);padding:var(--space-3);border-radius:var(--radius-md);margin-bottom:var(--space-3);border:1px solid var(--border-color)">
                        <div style="font-weight:var(--font-medium);color:var(--text-primary);margin-bottom:2px">3. DMARC Policy</div>
                        <code>Type: TXT | Host: _dmarc | Value: "v=DMARC1; p=quarantine"</code>
                    </div>
                    <div style="background:var(--bg-primary);padding:var(--space-3);border-radius:var(--radius-md);border:1px solid var(--border-color)">
                        <div style="font-weight:var(--font-medium);color:var(--text-primary);margin-bottom:2px">4. DKIM Signature</div>
                        <div>Generated automatically inside the BillionMail admin console per domain.</div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

async function installEmail() {
    if (!confirm('Install BillionMail Email Server? This will download Docker containers and set up mail services.')) return;

    const btn = document.getElementById('install-email-btn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner spinner-sm" style="margin-right:8px"></span> Installing BillionMail...`;
    }
    showToast('Installing', 'BillionMail installation started. This may take 2-4 minutes.', 'info');

    try {
        await API.post('/api/email/install');
        showToast('Success', 'BillionMail installed successfully!', 'success');
        renderEmail();
    } catch (e) {
        showToast('Install Failed', e.message, 'error');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = 'Install BillionMail Mail Server';
        }
    }
}

async function controlEmail(action) {
    showToast('Processing', `${action.toUpperCase()} command sent to BillionMail...`, 'info');
    try {
        await API.post(`/api/email/${action}`);
        showToast('Success', `BillionMail ${action}ed successfully`, 'success');
        renderEmail();
    } catch (e) {
        showToast('Action Failed', e.message, 'error');
    }
}

async function showEmailCredentials() {
    openModal('BillionMail Credentials', `
        <div style="display:flex;align-items:center;justify-content:center;padding:var(--space-6)">
            <div class="spinner spinner-md"></div>
        </div>
    `, `<button class="btn btn-secondary" onclick="closeModal()">Close</button>`);

    try {
        const creds = await API.get('/api/email/credentials');
        const raw = creds.raw || 'No command output available.';

        const bodyEl = document.getElementById('modal-body');
        if (bodyEl) {
            bodyEl.innerHTML = `
                <div style="margin-bottom:var(--space-3);font-size:var(--text-sm);color:var(--text-secondary)">
                    Default login information generated by BillionMail (<code>bm default</code>):
                </div>
                <pre style="margin:0;padding:var(--space-3);background:var(--bg-primary);color:var(--text-primary);font-family:'JetBrains Mono',monospace;font-size:12px;line-height:1.5;max-height:360px;overflow:auto;white-space:pre-wrap;word-break:break-all;border-radius:var(--radius-md);border:1px solid var(--border-color)">${raw}</pre>
                <div style="margin-top:var(--space-3);font-size:var(--text-xs);color:var(--text-tertiary)">
                    Make sure to change the admin credentials upon initial login!
                </div>
            `;
        }
    } catch (e) {
        const bodyEl = document.getElementById('modal-body');
        if (bodyEl) {
            bodyEl.innerHTML = `<div class="empty-state"><p>${e.message}</p></div>`;
        }
    }
}

async function uninstallEmail() {
    confirmModal(
        'Uninstall BillionMail',
        'Are you sure you want to uninstall BillionMail? This will stop all mail containers and remove the installation directory to keep the server lightweight. Your website databases and files will not be affected.',
        async () => {
            showToast('Uninstalling', 'Stopping and removing BillionMail...', 'info');
            try {
                await API.post('/api/email/uninstall');
                showToast('Success', 'BillionMail uninstalled', 'success');
                renderEmail();
            } catch (e) {
                showToast('Error', e.message, 'error');
            }
        },
        'danger'
    );
}
