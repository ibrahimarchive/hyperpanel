/**
 * HyperPanel — Databases Page
 * Supports MySQL/MariaDB databases, users, SQL export/import, and Adminer Web GUI.
 */
async function renderDatabases() {
    const content = document.getElementById('page-content');
    try {
        const databases = await API.get('/api/databases');
        const dbUsers = await API.get('/api/databases/users');

        content.innerHTML = `
            <div class="page-header">
                <div class="page-header-left">
                    <h1>Databases</h1>
                    <p>Manage MySQL/MariaDB databases, users, SQL dumps, and web GUI</p>
                </div>
                <div class="page-header-actions">
                    <button class="btn btn-ghost" onclick="openAdminerModal()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
                        Adminer Web GUI
                    </button>
                    <button class="btn btn-secondary" onclick="showCreateDbUserModal()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>
                        Add DB User
                    </button>
                    <button class="btn btn-primary" onclick="showCreateDatabaseModal()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
                        New Database
                    </button>
                </div>
            </div>

            <div class="tabs">
                <div class="tab active" onclick="showDbTab('databases', this)">Databases (${databases.length})</div>
                <div class="tab" onclick="showDbTab('users', this)">Users (${dbUsers.length})</div>
            </div>

            <div id="db-tab-databases">
                ${databases.length > 0 ? `
                    <div class="table-wrapper">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Charset</th>
                                    <th>Size</th>
                                    <th>Created</th>
                                    <th style="text-align:right">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${databases.map(d => `
                                    <tr>
                                        <td><strong>${d.name}</strong></td>
                                        <td><span class="badge badge-neutral">${d.charset}</span></td>
                                        <td>${formatBytes(d.size_bytes)}</td>
                                        <td style="font-size:var(--text-xs);color:var(--text-tertiary)">${d.created_at ? new Date(d.created_at).toLocaleDateString() : '—'}</td>
                                        <td>
                                            <div class="table-actions">
                                                <button class="btn btn-ghost btn-sm btn-icon" onclick="exportDatabase('${d.name}')" title="Export SQL Dump">
                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                                                </button>
                                                <button class="btn btn-ghost btn-sm btn-icon" onclick="showImportModal('${d.name}')" title="Import SQL File">
                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                                                </button>
                                                <button class="btn btn-ghost btn-sm btn-icon" onclick="deleteDatabase(${d.id},'${d.name}')" style="color:var(--danger-400)" title="Drop Database">
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
                    <div class="card">
                        <div class="card-body">
                            <div class="empty-state">
                                <div class="empty-state-icon">🗄️</div>
                                <h3>No databases</h3>
                                <p>Create a database to get started.</p>
                                <button class="btn btn-primary" onclick="showCreateDatabaseModal()">Create Database</button>
                            </div>
                        </div>
                    </div>
                `}
            </div>

            <div id="db-tab-users" style="display:none">
                ${dbUsers.length > 0 ? `
                    <div class="table-wrapper">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Username</th>
                                    <th>Host</th>
                                    <th>Privileges</th>
                                    <th>Created</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${dbUsers.map(u => `
                                    <tr>
                                        <td><strong>${u.username}</strong></td>
                                        <td>${u.host}</td>
                                        <td><span class="badge badge-info">${u.privileges}</span></td>
                                        <td style="font-size:var(--text-xs);color:var(--text-tertiary)">${u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                ` : `
                    <div class="card">
                        <div class="card-body">
                            <div class="empty-state">
                                <h3>No database users</h3>
                            </div>
                        </div>
                    </div>
                `}
            </div>`;
    } catch (e) {
        content.innerHTML = `<div class="card"><div class="card-body"><div class="empty-state"><h3>Error</h3><p>${e.message}</p></div></div></div>`;
    }
}

function showDbTab(tab, el) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('db-tab-databases').style.display = tab === 'databases' ? 'block' : 'none';
    document.getElementById('db-tab-users').style.display = tab === 'users' ? 'block' : 'none';
}

function showCreateDatabaseModal() {
    openModal('Create Database', `
        <div class="form-group"><label class="form-label">Database Name</label><input type="text" class="form-input" id="new-db-name" placeholder="my_database"></div>
        <div class="form-group"><label class="form-label">Charset</label><select class="form-input" id="new-db-charset"><option value="utf8mb4">utf8mb4 (recommended)</option><option value="utf8">utf8</option><option value="latin1">latin1</option></select></div>
    `, `<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="createDatabase()">Create</button>`);
}

async function createDatabase() {
    try {
        await API.post('/api/databases', { name: document.getElementById('new-db-name').value, charset: document.getElementById('new-db-charset').value });
        closeModal();
        showToast('Created', 'Database created successfully', 'success');
        renderDatabases();
    } catch (e) {
        showToast('Error', e.message, 'error');
    }
}

async function deleteDatabase(id, name) {
    confirmModal('Delete Database', `Are you sure you want to drop database "${name}"? This cannot be undone.`, async () => {
        try {
            await API.delete(`/api/databases/${id}`);
            showToast('Deleted', `Database ${name} dropped`, 'success');
            renderDatabases();
        } catch (e) {
            showToast('Error', e.message, 'error');
        }
    });
}

function showCreateDbUserModal() {
    openModal('Create Database User', `
        <div class="form-group"><label class="form-label">Username</label><input type="text" class="form-input" id="new-dbuser-name" placeholder="db_user"></div>
        <div class="form-group"><label class="form-label">Password</label><input type="password" class="form-input" id="new-dbuser-pass" placeholder="Strong password"></div>
        <div class="form-group"><label class="form-label">Host</label><input type="text" class="form-input" id="new-dbuser-host" value="localhost"></div>
    `, `<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="createDbUser()">Create User</button>`);
}

async function createDbUser() {
    try {
        await API.post('/api/databases/users', {
            username: document.getElementById('new-dbuser-name').value,
            password: document.getElementById('new-dbuser-pass').value,
            host: document.getElementById('new-dbuser-host').value
        });
        closeModal();
        showToast('Created', 'Database user created', 'success');
        renderDatabases();
    } catch (e) {
        showToast('Error', e.message, 'error');
    }
}

async function exportDatabase(name) {
    showToast('Exporting', `Generating SQL dump for ${name}...`, 'info');
    try {
        const token = localStorage.getItem('hyperpanel-token');
        const res = await fetch(`/api/databases/${encodeURIComponent(name)}/export`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: 'Export failed' }));
            throw new Error(err.detail || 'Export failed');
        }
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${name}_backup.sql`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
        showToast('Exported', `Database ${name} exported successfully`, 'success');
    } catch (e) {
        showToast('Error', e.message, 'error');
    }
}

function showImportModal(name) {
    openModal(`Import SQL into ${name}`, `
        <p style="font-size:var(--text-sm);color:var(--text-secondary);margin-bottom:var(--space-3)">
            Select a <code>.sql</code> dump file to import into database <strong>${name}</strong>.
        </p>
        <div class="form-group">
            <label class="form-label">SQL File</label>
            <input type="file" id="import-sql-file" class="form-input" accept=".sql">
        </div>
    `, `
        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button class="btn btn-primary" id="btn-do-import" onclick="doImportSql('${name}')">Start Import</button>
    `);
}

async function doImportSql(name) {
    const fileInput = document.getElementById('import-sql-file');
    if (!fileInput.files.length) {
        showToast('Error', 'Please select a .sql file', 'warning');
        return;
    }
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    const btn = document.getElementById('btn-do-import');
    btn.disabled = true;
    btn.textContent = 'Importing...';

    try {
        const token = localStorage.getItem('hyperpanel-token');
        const res = await fetch(`/api/databases/${encodeURIComponent(name)}/import`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData,
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Import failed');

        closeModal();
        showToast('Imported', data.message || `Imported into ${name}`, 'success');
        renderDatabases();
    } catch (e) {
        showToast('Error', e.message, 'error');
        btn.disabled = false;
        btn.textContent = 'Start Import';
    }
}

async function openAdminerModal() {
    try {
        const status = await API.get('/api/databases/adminer/status');
        if (status.installed) {
            openModal('Database Web GUI (Adminer)', `
                <div style="text-align:center;padding:var(--space-4)">
                    <div style="font-size:44px;margin-bottom:var(--space-2)">🗄️</div>
                    <h3 style="margin-bottom:var(--space-2)">Adminer Web GUI is Ready</h3>
                    <p style="font-size:var(--text-sm);color:var(--text-secondary);margin-bottom:var(--space-4)">
                        Adminer provides visual table, view, and SQL query management with zero background overhead.
                    </p>
                    <div style="background:var(--bg-secondary);border-radius:var(--radius-md);padding:var(--space-3);text-align:left;font-size:var(--text-xs);margin-bottom:var(--space-4);border:1px solid var(--border-color)">
                        <div style="margin-bottom:4px"><strong>Server:</strong> localhost</div>
                        <div style="margin-bottom:4px"><strong>System:</strong> MySQL / MariaDB</div>
                        <div><strong>Credentials:</strong> Enter any database user and password</div>
                    </div>
                    <a href="${status.url}" target="_blank" class="btn btn-primary btn-lg" style="display:inline-flex;align-items:center;gap:var(--space-2)">
                        Launch Adminer
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3"/></svg>
                    </a>
                </div>
            `, `<button class="btn btn-secondary" onclick="closeModal()">Close</button>`);
        } else {
            openModal('Install Adminer Web GUI', `
                <div style="text-align:center;padding:var(--space-4)">
                    <div style="font-size:44px;margin-bottom:var(--space-2)">🚀</div>
                    <h3 style="margin-bottom:var(--space-2)">Install Adminer (Web GUI)</h3>
                    <p style="font-size:var(--text-sm);color:var(--text-secondary);margin-bottom:var(--space-4);line-height:1.6">
                        Adminer is a fast, ultra-lightweight single-file PHP database manager (&lt;1 MB). It requires no background daemon and allows full management of databases, users, tables, and records.
                    </p>
                    <button class="btn btn-primary btn-lg" id="btn-install-adminer" onclick="installAdminer()">
                        1-Click Install Adminer
                    </button>
                </div>
            `, `<button class="btn btn-secondary" onclick="closeModal()">Cancel</button>`);
        }
    } catch (e) {
        showToast('Error', e.message, 'error');
    }
}

async function installAdminer() {
    const btn = document.getElementById('btn-install-adminer');
    if (btn) { btn.disabled = true; btn.textContent = 'Installing...'; }
    try {
        const res = await API.post('/api/databases/adminer/install');
        showToast('Installed', res.message || 'Adminer installed successfully', 'success');
        closeModal();
        openAdminerModal();
    } catch (e) {
        showToast('Error', e.message, 'error');
        if (btn) { btn.disabled = false; btn.textContent = '1-Click Install Adminer'; }
    }
}
