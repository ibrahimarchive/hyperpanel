/**
 * HyperPanel — Websites Page
 */

async function renderWebsites() {
    const content = document.getElementById('page-content');

    try {
        const websites = await API.get('/api/websites');

        content.innerHTML = `
            <div class="page-header">
                <div class="page-header-left">
                    <h1>Websites</h1>
                    <p>Manage your web applications and virtual hosts</p>
                </div>
                <div class="page-header-actions">
                    <button class="btn btn-secondary" onclick="showInstallWordPressModal()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"/><path d="M7 9l3 6 2-4 2 4 3-6"/></svg>
                        Install WordPress
                    </button>
                    <button class="btn btn-primary" onclick="showCreateWebsiteModal()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
                        New Website
                    </button>
                </div>
            </div>

            ${websites.length > 0 ? `
                <div class="table-wrapper">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Domain</th>
                                <th>Type</th>
                                <th>Status</th>
                                <th>SSL</th>
                                <th>PHP</th>
                                <th>Created</th>
                                <th style="text-align:right">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${websites.map(w => `
                                <tr>
                                    <td>
                                        <div class="file-item">
                                            <span class="file-item-icon">🌐</span>
                                            <div>
                                                <div class="file-item-name">${w.domain}</div>
                                                <div style="font-size:var(--text-xs);color:var(--text-tertiary)">${w.document_root}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td><span class="badge badge-neutral">${w.site_type}</span></td>
                                    <td><span class="badge ${w.status === 'active' ? 'badge-success' : 'badge-danger'}">${w.status}</span></td>
                                    <td>${w.ssl_enabled ? '<span class="badge badge-success">🔒 Enabled</span>' : '<span class="badge badge-neutral">Off</span>'}</td>
                                    <td>${w.php_version || '—'}</td>
                                    <td style="font-size:var(--text-xs);color:var(--text-tertiary)">${new Date(w.created_at).toLocaleDateString()}</td>
                                    <td>
                                        <div class="table-actions">
                                            <button class="btn btn-ghost btn-sm" onclick="toggleWebsite(${w.id})" title="${w.status === 'active' ? 'Disable' : 'Enable'}">
                                                ${w.status === 'active' ? '⏸' : '▶️'}
                                            </button>
                                            <button class="btn btn-ghost btn-sm btn-icon" onclick="deleteWebsite(${w.id}, '${w.domain}')" title="Delete" style="color:var(--danger-400)">
                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            ` : `
                <div class="card"><div class="card-body">
                    <div class="empty-state">
                        <div class="empty-state-icon">🌐</div>
                        <h3>No websites yet</h3>
                        <p>Create your first website to get started with hosting.</p>
                        <button class="btn btn-primary" onclick="showCreateWebsiteModal()">Create Website</button>
                    </div>
                </div></div>
            `}
        `;
    } catch (e) {
        content.innerHTML = `<div class="card"><div class="card-body"><div class="empty-state"><h3>Error</h3><p>${e.message}</p></div></div></div>`;
    }
}

function showCreateWebsiteModal() {
    const body = `
        <div class="form-group">
            <label class="form-label">Domain Name</label>
            <input type="text" class="form-input" id="new-site-domain" placeholder="example.com">
        </div>
        <div class="form-group">
            <label class="form-label">Site Name</label>
            <input type="text" class="form-input" id="new-site-name" placeholder="My Website">
        </div>
        <div class="form-group">
            <label class="form-label">Site Type</label>
            <select class="form-input" id="new-site-type">
                <option value="php">PHP</option>
                <option value="static">Static HTML</option>
                <option value="nodejs">Node.js (Reverse Proxy)</option>
                <option value="python">Python (Reverse Proxy)</option>
            </select>
        </div>
        <div class="form-group" id="php-version-group">
            <label class="form-label">PHP Version</label>
            <select class="form-input" id="new-site-php">
                <option value="8.2">PHP 8.2</option>
                <option value="8.1">PHP 8.1</option>
                <option value="8.0">PHP 8.0</option>
                <option value="7.4">PHP 7.4</option>
            </select>
        </div>
        <div class="form-group" id="proxy-port-group" style="display:none">
            <label class="form-label">Proxy Port</label>
            <input type="number" class="form-input" id="new-site-port" placeholder="3000">
        </div>
    `;

    const footer = `
        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button class="btn btn-primary" onclick="createWebsite()">Create Website</button>
    `;

    openModal('Create Website', body, footer);

    // Toggle fields based on site type
    document.getElementById('new-site-type').addEventListener('change', (e) => {
        const isPhp = e.target.value === 'php';
        const isProxy = ['nodejs', 'python', 'reverse_proxy'].includes(e.target.value);
        document.getElementById('php-version-group').style.display = isPhp ? 'block' : 'none';
        document.getElementById('proxy-port-group').style.display = isProxy ? 'block' : 'none';
    });
}

async function createWebsite() {
    const data = {
        domain: document.getElementById('new-site-domain').value,
        name: document.getElementById('new-site-name').value,
        site_type: document.getElementById('new-site-type').value,
        php_version: document.getElementById('new-site-php')?.value,
        proxy_port: document.getElementById('new-site-port')?.value ? parseInt(document.getElementById('new-site-port').value) : null,
    };

    if (!data.domain || !data.name) {
        showToast('Validation Error', 'Domain and name are required', 'warning');
        return;
    }

    try {
        await API.post('/api/websites', data);
        closeModal();
        showToast('Website Created', `${data.domain} is now live`, 'success');
        renderWebsites();
    } catch (e) {
        showToast('Error', e.message, 'error');
    }
}

async function toggleWebsite(id) {
    try {
        const result = await API.post(`/api/websites/${id}/toggle`);
        showToast('Success', result.message, 'success');
        renderWebsites();
    } catch (e) {
        showToast('Error', e.message, 'error');
    }
}

async function deleteWebsite(id, domain) {
    confirmModal('Delete Website', `Are you sure you want to delete "${domain}"? This will remove its Nginx configuration.`, async () => {
        try {
            await API.delete(`/api/websites/${id}`);
            showToast('Deleted', `${domain} has been removed`, 'success');
            renderWebsites();
        } catch (e) {
            showToast('Error', e.message, 'error');
        }
    });
}

function showInstallWordPressModal() {
    openModal('Deploy WordPress Site', `
        <div style="margin-bottom:var(--space-4);font-size:var(--text-sm);color:var(--text-secondary)">
            Deploy a complete WordPress installation with automated database provisioning, security salts, and Nginx PHP-FPM virtual host.
        </div>
        <div class="form-group">
            <label class="form-label">Domain Name</label>
            <input type="text" class="form-input" id="wp-domain" placeholder="example.com" required>
        </div>
        <div class="form-group">
            <label class="form-label">Site Title</label>
            <input type="text" class="form-input" id="wp-title" value="My WordPress Site" placeholder="Blog / Company Name">
        </div>
        <div class="grid grid-2" style="gap:var(--space-3)">
            <div class="form-group">
                <label class="form-label">Admin Username</label>
                <input type="text" class="form-input" id="wp-admin-user" value="admin">
            </div>
            <div class="form-group">
                <label class="form-label">Admin Password</label>
                <input type="password" class="form-input" id="wp-admin-pass" placeholder="Strong password" required>
            </div>
        </div>
        <div class="grid grid-2" style="gap:var(--space-3)">
            <div class="form-group">
                <label class="form-label">Admin Email</label>
                <input type="email" class="form-input" id="wp-admin-email" placeholder="admin@example.com" required>
            </div>
            <div class="form-group">
                <label class="form-label">PHP Version</label>
                <select class="form-input" id="wp-php-version">
                    <option value="8.2" selected>PHP 8.2 (Recommended)</option>
                    <option value="8.3">PHP 8.3</option>
                    <option value="8.1">PHP 8.1</option>
                </select>
            </div>
        </div>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button class="btn btn-primary" id="btn-submit-wp" onclick="submitInstallWordPress()">
            Deploy WordPress
        </button>
    `);
}

async function submitInstallWordPress() {
    const domain = document.getElementById('wp-domain').value.trim();
    const site_title = document.getElementById('wp-title').value.trim() || 'My WordPress Site';
    const admin_username = document.getElementById('wp-admin-user').value.trim() || 'admin';
    const admin_password = document.getElementById('wp-admin-pass').value;
    const admin_email = document.getElementById('wp-admin-email').value.trim();
    const php_version = document.getElementById('wp-php-version').value;

    if (!domain) {
        showToast('Validation Error', 'Domain name is required', 'warning');
        return;
    }
    if (!admin_password) {
        showToast('Validation Error', 'Admin password is required', 'warning');
        return;
    }
    if (!admin_email) {
        showToast('Validation Error', 'Admin email is required', 'warning');
        return;
    }

    const btn = document.getElementById('btn-submit-wp');
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner spinner-sm" style="display:inline-block;vertical-align:middle;margin-right:6px"></span> Deploying WordPress...`;

    try {
        const res = await API.post('/api/websites/wordpress', {
            domain,
            site_title,
            admin_username,
            admin_password,
            admin_email,
            php_version,
        });

        closeModal();
        showToast('WordPress Deployed', res.message || 'WordPress installed successfully!', 'success');
        renderWebsites();

        openModal('WordPress Deployment Complete', `
            <div style="text-align:center;padding:var(--space-3)">
                <div style="font-size:40px;margin-bottom:var(--space-2)">🎉</div>
                <h3>WordPress is Live!</h3>
                <p style="font-size:var(--text-sm);color:var(--text-secondary);margin-bottom:var(--space-4)">
                    Your site and database have been successfully provisioned.
                </p>
                <div style="background:var(--bg-secondary);border:1px solid var(--border-color);border-radius:var(--radius-md);padding:var(--space-3);text-align:left;font-size:var(--text-xs);margin-bottom:var(--space-4)">
                    <div style="margin-bottom:4px"><strong>Site URL:</strong> <a href="${res.url}" target="_blank" style="color:var(--primary-400)">${res.url}</a></div>
                    <div style="margin-bottom:4px"><strong>Admin Username:</strong> <code>${res.admin_username}</code></div>
                    <div style="margin-bottom:4px"><strong>Database:</strong> <code>${res.db_name}</code></div>
                    <div><strong>Database User:</strong> <code>${res.db_user}</code></div>
                </div>
                <a href="${res.url}" target="_blank" class="btn btn-primary">Visit Website</a>
            </div>
        `, `<button class="btn btn-secondary" onclick="closeModal()">Close</button>`);
    } catch (e) {
        showToast('Installation Error', e.message, 'error');
        btn.disabled = false;
        btn.textContent = 'Deploy WordPress';
    }
}
