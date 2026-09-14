/**
 * HyperPanel — FTP Management Page (Pure-FTPd)
 * Modular, lightweight FTP server with virtual user isolation and chroot jailing.
 */

let _ftpAccounts = [];

async function renderFTP() {
    const content = document.getElementById('page-content');
    content.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:center;height:50vh;">
            <div class="spinner spinner-lg"></div>
        </div>
    `;

    try {
        const status = await API.get('/api/ftp/status');

        if (!status.installed) {
            renderFTPUninstalled(content);
            return;
        }

        _ftpAccounts = await API.get('/api/ftp/accounts');
        renderFTPInstalled(content, status, _ftpAccounts);
    } catch (e) {
        content.innerHTML = `
            <div class="page-header">
                <div class="page-header-left">
                    <h1>FTP Accounts</h1>
                    <p>Pure-FTPd Virtual FTP Server</p>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <div class="empty-state">
                        <div class="empty-state-icon">⚠️</div>
                        <h3>Unable to load FTP status</h3>
                        <p style="color:var(--text-tertiary)">${e.message}</p>
                        <button class="btn btn-primary" onclick="renderFTP()" style="margin-top:var(--space-3)">Retry</button>
                    </div>
                </div>
            </div>
        `;
    }
}

function renderFTPUninstalled(content) {
    content.innerHTML = `
        <div class="page-header">
            <div class="page-header-left">
                <h1>FTP Accounts</h1>
                <p>High-performance virtual FTP/FTPS server with chroot security</p>
            </div>
            <div class="page-header-actions">
                <span class="badge badge-secondary">Optional Module</span>
            </div>
        </div>

        <div class="card" style="margin-bottom:var(--space-5);border:1px solid var(--border-color);background:linear-gradient(180deg, rgba(16,185,129,0.03) 0%, transparent 100%)">
            <div class="card-body" style="padding:var(--space-8);text-align:center">
                <div style="width:64px;height:64px;border-radius:var(--radius-xl);background:rgba(16,185,129,0.12);display:inline-flex;align-items:center;justify-content:center;margin-bottom:var(--space-4);color:var(--success-400)">
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/>
                        <path d="M12 12v9"/>
                        <path d="m16 16-4-4-4 4"/>
                    </svg>
                </div>
                <h2 style="font-size:var(--text-2xl);margin-bottom:var(--space-2)">Pure-FTPd Not Installed</h2>
                <p style="color:var(--text-tertiary);max-width:560px;margin:0 auto var(--space-5);font-size:var(--text-sm);line-height:1.6">
                    HyperPanel keeps your server lightweight and minimal by leaving FTP optional. Install <strong>Pure-FTPd</strong> to create isolated virtual FTP accounts, enable chroot jailing to website folders, and upload files securely.
                </p>

                <div>
                    <button class="btn btn-primary" id="install-ftp-btn" onclick="installFTP()" style="padding:var(--space-3) var(--space-6);font-size:var(--text-base)">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
                        Install Pure-FTPd Server
                    </button>
                </div>
                <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:var(--space-3)">
                    Configures PureDB virtual accounts, chroot jail, and passive port range (30000–30050).
                </div>
            </div>
        </div>

        <div class="grid grid-3" style="gap:var(--space-4)">
            <div class="card">
                <div class="card-body">
                    <div style="font-size:24px;margin-bottom:var(--space-2)">🔒</div>
                    <div style="font-weight:var(--font-semibold);margin-bottom:var(--space-1)">Chroot Jailing</div>
                    <div style="font-size:var(--text-xs);color:var(--text-secondary);line-height:1.5">
                        Each FTP user is strictly locked into their designated document root (e.g. <code>/var/www/site</code>) and cannot navigate elsewhere.
                    </div>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <div style="font-size:24px;margin-bottom:var(--space-2)">⚡</div>
                    <div style="font-weight:var(--font-semibold);margin-bottom:var(--space-1)">Minimal RAM (&lt;10MB)</div>
                    <div style="font-size:var(--text-xs);color:var(--text-secondary);line-height:1.5">
                        Pure-FTPd is globally recognized for zero bloat, high concurrency, and virtually negligible idle memory usage.
                    </div>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <div style="font-size:24px;margin-bottom:var(--space-2)">👤</div>
                    <div style="font-weight:var(--font-semibold);margin-bottom:var(--space-1)">Virtual PureDB Users</div>
                    <div style="font-size:var(--text-xs);color:var(--text-secondary);line-height:1.5">
                        No system Linux user accounts are created. All credentials exist inside a dedicated encrypted database.
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderFTPInstalled(content, status, accounts) {
    const isRunning = !!status.running;
    const serverHost = window.location.hostname || '127.0.0.1';

    content.innerHTML = `
        <div class="page-header">
            <div class="page-header-left">
                <h1>FTP Accounts</h1>
                <p>Pure-FTPd Virtual Accounts (${accounts.length} created)</p>
            </div>
            <div class="page-header-actions">
                <button class="btn btn-primary" onclick="showCreateFTPModal()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
                    New FTP Account
                </button>
            </div>
        </div>

        <!-- Server Controls & Connection Card -->
        <div class="card" style="margin-bottom:var(--space-5)">
            <div class="card-body" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:var(--space-4)">
                <div style="display:flex;align-items:center;gap:var(--space-4)">
                    <div style="width:48px;height:48px;border-radius:var(--radius-lg);background:rgba(16,185,129,0.12);display:flex;align-items:center;justify-content:center;color:var(--success-400)">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/>
                            <path d="M12 12v9"/>
                            <path d="m16 16-4-4-4 4"/>
                        </svg>
                    </div>
                    <div>
                        <div style="display:flex;align-items:center;gap:var(--space-2)">
                            <h3 style="margin:0;font-size:var(--text-lg)">Pure-FTPd Service</h3>
                            <span class="badge ${isRunning ? 'badge-success' : 'badge-danger'}">
                                ${isRunning ? '● Active' : '● Stopped'}
                            </span>
                        </div>
                        <div style="font-size:var(--text-xs);color:var(--text-secondary);margin-top:2px">
                            Host: <strong>${serverHost}</strong> • Port: <strong>21</strong> • Passive Ports: <strong>${status.passive_port_range || '30000-30050'}</strong>
                        </div>
                    </div>
                </div>

                <div style="display:flex;align-items:center;gap:var(--space-2)">
                    ${isRunning ? `
                        <button class="btn btn-secondary btn-sm" onclick="controlFTP('restart')" title="Restart Pure-FTPd">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15"/></svg>
                            Restart
                        </button>
                        <button class="btn btn-secondary btn-sm" onclick="controlFTP('stop')" style="color:var(--warning-400)" title="Stop Pure-FTPd">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
                            Stop
                        </button>
                    ` : `
                        <button class="btn btn-primary btn-sm" onclick="controlFTP('start')" title="Start Pure-FTPd">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                            Start
                        </button>
                    `}
                    <button class="btn btn-ghost btn-sm" onclick="uninstallFTP()" style="color:var(--danger-400)" title="Uninstall Pure-FTPd">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                        Uninstall
                    </button>
                </div>
            </div>
        </div>

        <!-- Connection Information Box -->
        <div class="card" style="margin-bottom:var(--space-5);background:var(--bg-secondary);border:1px solid var(--border-color)">
            <div class="card-body" style="padding:var(--space-3) var(--space-4)">
                <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:var(--space-3);font-size:var(--text-xs)">
                    <div>💻 <strong>FTP Client Setup:</strong> Connect with FileZilla, Cyberduck, or WinSCP using:</div>
                    <div style="display:flex;gap:var(--space-4);flex-wrap:wrap">
                        <span>Host: <code>${serverHost}</code></span>
                        <span>Port: <code>21</code></span>
                        <span>Encryption: <code>Require explicit FTP over TLS</code></span>
                        <span>Logon: <code>Normal (Virtual User)</code></span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Accounts Table -->
        ${renderFTPAccountsTable(accounts)}
    `;
}

function renderFTPAccountsTable(accounts) {
    if (!accounts.length) {
        return `
            <div class="card">
                <div class="card-body">
                    <div class="empty-state">
                        <div class="empty-state-icon">📂</div>
                        <h3>No FTP Accounts</h3>
                        <p style="color:var(--text-tertiary);margin-bottom:var(--space-4)">
                            Create your first virtual FTP account to allow file transfers to specific website directories.
                        </p>
                        <button class="btn btn-primary" onclick="showCreateFTPModal()">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
                            Create FTP Account
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    return `
        <div class="table-wrapper">
            <table class="table">
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>Chroot Home Directory</th>
                        <th>Quota</th>
                        <th>Status</th>
                        <th>Created</th>
                        <th style="text-align:right">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${accounts.map(a => `
                        <tr>
                            <td style="font-weight:var(--font-medium)">
                                <div style="display:flex;align-items:center;gap:var(--space-2)">
                                    <div style="width:28px;height:28px;border-radius:var(--radius-md);background:rgba(59,130,246,0.1);display:flex;align-items:center;justify-content:center;color:var(--primary-400);font-size:11px">FTP</div>
                                    <span>${a.username}</span>
                                </div>
                            </td>
                            <td><code style="font-size:var(--text-xs)">${a.directory}</code></td>
                            <td style="font-size:var(--text-xs)">${a.quota_mb > 0 ? a.quota_mb + ' MB' : '<span style="color:var(--text-tertiary)">Unlimited</span>'}</td>
                            <td>
                                <span class="badge ${a.status === 'active' ? 'badge-success' : 'badge-warning'}">
                                    ${a.status}
                                </span>
                            </td>
                            <td style="font-size:var(--text-xs);color:var(--text-tertiary)">
                                ${new Date(a.created_at).toLocaleDateString()}
                            </td>
                            <td>
                                <div class="table-actions">
                                    <button class="btn btn-ghost btn-sm btn-icon" onclick="showEditFTPModal(${a.id})" title="Edit Account / Change Password">
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                                    </button>
                                    <button class="btn btn-ghost btn-sm btn-icon" onclick="deleteFTPAccount(${a.id}, '${a.username}')" style="color:var(--danger-400)" title="Delete FTP Account">
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

async function installFTP() {
    if (!confirm('Install Pure-FTPd Server? This will install the package and configure virtual user chroot security.')) return;

    const btn = document.getElementById('install-ftp-btn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner spinner-sm" style="margin-right:8px"></span> Installing Pure-FTPd...`;
    }
    showToast('Installing', 'Pure-FTPd installation started...', 'info');

    try {
        await API.post('/api/ftp/install');
        showToast('Success', 'Pure-FTPd installed and running!', 'success');
        renderFTP();
    } catch (e) {
        showToast('Install Failed', e.message, 'error');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = 'Install Pure-FTPd Server';
        }
    }
}

async function controlFTP(action) {
    showToast('Processing', `${action.toUpperCase()} command sent to Pure-FTPd...`, 'info');
    try {
        await API.post(`/api/ftp/service/${action}`);
        showToast('Success', `Pure-FTPd ${action}ed successfully`, 'success');
        renderFTP();
    } catch (e) {
        showToast('Action Failed', e.message, 'error');
    }
}

async function uninstallFTP() {
    confirmModal(
        'Uninstall Pure-FTPd',
        'Are you sure you want to uninstall Pure-FTPd? This will remove the FTP server package to keep your server minimal and lightweight. Your files and websites will NOT be deleted.',
        async () => {
            showToast('Uninstalling', 'Removing Pure-FTPd...', 'info');
            try {
                await API.post('/api/ftp/uninstall');
                showToast('Success', 'Pure-FTPd uninstalled', 'success');
                renderFTP();
            } catch (e) {
                showToast('Error', e.message, 'error');
            }
        },
        'danger'
    );
}

function showCreateFTPModal() {
    openModal('Create FTP Account', `
        <div class="form-group">
            <label class="form-label">Username</label>
            <input type="text" class="form-input" id="ftp-username" placeholder="e.g. webmaster" autocomplete="off">
            <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:4px">Letters, numbers, underscores, and hyphens only.</div>
        </div>
        <div class="form-group">
            <label class="form-label" style="display:flex;justify-content:space-between">
                <span>Password</span>
                <a href="javascript:void(0)" onclick="generateFTPPassword()" style="font-size:var(--text-xs);color:var(--primary-400)">Generate Strong Password</a>
            </label>
            <input type="text" class="form-input" id="ftp-password" placeholder="Enter secure password" autocomplete="new-password">
        </div>
        <div class="form-group">
            <label class="form-label">Chrooted Document Root Directory</label>
            <input type="text" class="form-input" id="ftp-directory" placeholder="/var/www/example.com">
            <div style="display:flex;gap:var(--space-2);margin-top:6px;flex-wrap:wrap">
                <button type="button" class="btn btn-ghost btn-sm" onclick="document.getElementById('ftp-directory').value='/var/www'" style="font-size:11px;padding:2px 8px">/var/www</button>
                <button type="button" class="btn btn-ghost btn-sm" onclick="document.getElementById('ftp-directory').value='/var/www/html'" style="font-size:11px;padding:2px 8px">/var/www/html</button>
            </div>
        </div>
        <div class="form-group">
            <label class="form-label">Quota in MB (0 for unlimited)</label>
            <input type="number" class="form-input" id="ftp-quota" value="0" min="0">
        </div>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button class="btn btn-primary" onclick="submitCreateFTPAccount()">Create Account</button>
    `);
}

function generateFTPPassword() {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%^&*';
    let pass = '';
    for (let i = 0; i < 16; i++) {
        pass += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    const el = document.getElementById('ftp-password');
    if (el) el.value = pass;
}

async function submitCreateFTPAccount() {
    const username = document.getElementById('ftp-username')?.value.trim();
    const password = document.getElementById('ftp-password')?.value;
    const directory = document.getElementById('ftp-directory')?.value.trim();
    const quota_mb = parseInt(document.getElementById('ftp-quota')?.value || '0', 10);

    if (!username || !password || !directory) {
        showToast('Validation Error', 'Username, password, and directory are required', 'warning');
        return;
    }

    try {
        await API.post('/api/ftp/accounts', {
            username,
            password,
            directory,
            quota_mb,
        });
        closeModal();
        showToast('Success', `FTP Account '${username}' created!`, 'success');
        renderFTP();
    } catch (e) {
        showToast('Creation Failed', e.message, 'error');
    }
}

function showEditFTPModal(accountId) {
    const account = _ftpAccounts.find(a => a.id === accountId);
    if (!account) return;

    openModal(`Edit FTP Account — ${account.username}`, `
        <div class="form-group">
            <label class="form-label">New Password (leave blank to keep unchanged)</label>
            <input type="text" class="form-input" id="edit-ftp-password" placeholder="Enter new password (optional)" autocomplete="new-password">
        </div>
        <div class="form-group">
            <label class="form-label">Chrooted Document Root Directory</label>
            <input type="text" class="form-input" id="edit-ftp-directory" value="${account.directory}">
        </div>
        <div class="form-group">
            <label class="form-label">Quota in MB (0 for unlimited)</label>
            <input type="number" class="form-input" id="edit-ftp-quota" value="${account.quota_mb}" min="0">
        </div>
        <div class="form-group">
            <label class="form-label">Account Status</label>
            <select class="form-input" id="edit-ftp-status">
                <option value="active" ${account.status === 'active' ? 'selected' : ''}>Active</option>
                <option value="suspended" ${account.status === 'suspended' ? 'selected' : ''}>Suspended</option>
            </select>
        </div>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button class="btn btn-primary" onclick="submitEditFTPAccount(${accountId})">Save Changes</button>
    `);
}

async function submitEditFTPAccount(accountId) {
    const password = document.getElementById('edit-ftp-password')?.value;
    const directory = document.getElementById('edit-ftp-directory')?.value.trim();
    const quota_mb = parseInt(document.getElementById('edit-ftp-quota')?.value || '0', 10);
    const status = document.getElementById('edit-ftp-status')?.value;

    const payload = {
        directory,
        quota_mb,
        status,
    };
    if (password && password.trim()) {
        payload.password = password.trim();
    }

    try {
        await API.put(`/api/ftp/accounts/${accountId}`, payload);
        closeModal();
        showToast('Success', 'FTP Account updated successfully', 'success');
        renderFTP();
    } catch (e) {
        showToast('Update Failed', e.message, 'error');
    }
}

async function deleteFTPAccount(accountId, username) {
    confirmModal(
        `Delete FTP Account '${username}'`,
        `Are you sure you want to delete the FTP account '${username}'? The user will lose FTP access immediately. Files inside their directory will NOT be deleted.`,
        async () => {
            try {
                await API.delete(`/api/ftp/accounts/${accountId}`);
                showToast('Success', `FTP Account '${username}' deleted`, 'success');
                renderFTP();
            } catch (e) {
                showToast('Delete Failed', e.message, 'error');
            }
        },
        'danger'
    );
}
